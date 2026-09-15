"""Módulo 10 — exportação para a visualização (JSON estático, sem backend).

Último estágio da fase 2. Junta, por evento, a seleção (M8, `event_top_tweets`),
a hidratação (M9, `tweets` / `users` / `lookup_errors`) e as coordenadas DRL (M7)
nos arquivos que o app web lê diretamente (spec §5.3, "dados pré-computados"):

    data/export/index.json              eventos, clusters, paleta, atrição (via `write_index`)
    data/export/<evento>/event.json     metadados do evento — fonte do index
    data/export/<evento>/tweets.json    um registro por slot (cluster, rank), com tweet e autor
    data/export/<evento>/layout.json    coordenadas DRL + comunidade por nó + centróides

`FILES = ()` como no M9: a fonte é o banco, que não tem sinal de cache em arquivo,
e exportar custa < 1 s por evento — então `run()` sempre re-exporta. A saída é
**determinística** para o mesmo estado do banco; o único carimbo de tempo fica no
`index.json`. Números de grupo ("Grupo k") seguem a numeração por tamanho usada nas
figuras da fase 1 (M6/M7), e as cores vêm da mesma `PALETTE`.

O contrato completo dos arquivos está em
`docs/superpowers/specs/2026-09-15-leitor-de-clusters-design.md`.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from modules.hydrate import hydration_status
from modules.layout import PALETTE, CommunityLayout
from modules.stage import Stage

STATUS_BY_TITLE = {"Not Found Error": "not_found", "Authorization Error": "not_authorized"}
TWEET_METRICS = ("retweet_count", "reply_count", "like_count", "quote_count",
                 "bookmark_count", "impression_count")
USER_METRICS = ("followers_count", "following_count", "tweet_count", "listed_count")

SLOTS_SQL = """
    SELECT e.community, e.rank, e.tweet_id, e.rt_cluster, e.rt_graph, e.rt_event, e.k,
           t.raw_json AS tweet_json, t.author_id,
           u.raw_json AS user_json,
           le.title AS err_title, le.detail AS err_detail,
           lu.title AS user_err_title
    FROM event_top_tweets e
    LEFT JOIN tweets t         ON t.tweet_id = e.tweet_id
    LEFT JOIN users u          ON u.user_id = t.author_id
    LEFT JOIN lookup_errors le ON le.resource_type = 'tweet' AND le.resource_id = e.tweet_id
    LEFT JOIN lookup_errors lu ON lu.resource_type = 'user'  AND lu.resource_id = t.author_id
    WHERE e.event_slug = ?
    ORDER BY e.community, e.rank"""


def _status(hydrated: bool, err_title) -> str:
    if hydrated:
        return "hydrated"
    if err_title is None:
        return "pending"
    return STATUS_BY_TITLE.get(err_title, "error")


def _pick(d: dict, keys) -> dict:
    return {k: d[k] for k in keys if k in d}


def _tweet_view(raw: dict) -> dict:
    m = raw.get("public_metrics") or {}
    ent = raw.get("entities") or {}
    return {
        "id": str(raw["id"]),
        "text": raw.get("text"),
        "created_at": raw.get("created_at"),
        "lang": raw.get("lang"),
        "source": raw.get("source"),
        "possibly_sensitive": raw.get("possibly_sensitive"),
        "reply_settings": raw.get("reply_settings"),
        "conversation_id": raw.get("conversation_id"),
        "in_reply_to_user_id": raw.get("in_reply_to_user_id"),
        "metrics": {k: m.get(k) for k in TWEET_METRICS},
        "entities": {
            "urls": [_pick(u, ("start", "end", "url", "expanded_url", "display_url", "media_key"))
                     for u in ent.get("urls", [])],
            "hashtags": [_pick(h, ("start", "end", "tag")) for h in ent.get("hashtags", [])],
            "mentions": [_pick(x, ("start", "end", "username", "id")) for x in ent.get("mentions", [])],
        },
        "referenced_tweets": raw.get("referenced_tweets") or [],
        "url": f"https://x.com/i/web/status/{raw['id']}",
    }


def _author_view(raw: dict) -> dict:
    m = raw.get("public_metrics") or {}
    return {
        "id": str(raw["id"]),
        "username": raw.get("username"),
        "name": raw.get("name"),
        "description": raw.get("description"),
        "location": raw.get("location"),
        "url": raw.get("url"),
        "profile_image_url": raw.get("profile_image_url"),
        "protected": raw.get("protected"),
        "verified": raw.get("verified"),
        "verified_type": raw.get("verified_type"),
        "created_at": raw.get("created_at"),
        "metrics": {k: m.get(k) for k in USER_METRICS},
    }


def _dump(path: Path, obj, compact: bool = False) -> None:
    if compact:
        path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    else:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1))


class WebExporter(Stage):
    """M10 — JSON de um evento a partir de `data/processed/<evento>/` + banco."""

    FILES = ()                    # sempre re-exporta (fonte = banco; barato)

    def __init__(self, db):
        self.db = db

    # --- exportação -------------------------------------------------------
    def export(self, processed_dir) -> dict:
        d = Path(processed_dir)
        slug = d.name
        nodes = pd.read_parquet(d / "graph_nodes.parquet")
        n_edges = pq.read_metadata(d / "graph_edges.parquet").num_rows
        run_config = json.loads((d / "run_config.json").read_text())
        stats = json.loads((d / "top_tweets_stats.json").read_text())
        layout = CommunityLayout.load(d)

        sizes = nodes["community"].value_counts()                 # descendente = "Grupo k"
        group_of = {int(c): i + 1 for i, c in enumerate(sizes.index)}

        event = self._event_meta(slug, nodes, n_edges, run_config, stats, group_of)
        slots = self._slots(slug, group_of)
        lay = self._layout(layout, group_of)
        return {"event": event, "tweets": slots, "layout": lay}

    def _event_meta(self, slug, nodes, n_edges, run_config, stats, group_of) -> dict:
        row = self.db.conn.execute(
            "SELECT name, event_date FROM events WHERE slug = ?", (slug,)).fetchone()
        status = hydration_status(self.db)
        status = status[status["evento"] == slug].set_index("cluster")

        clusters = []
        for c_str, cs in stats["clusters"].items():
            c = int(c_str)
            g = group_of[c]
            st = status.loc[c] if c in status.index else None
            clusters.append({
                "community": c, "group": g, "label": f"Grupo {g}",
                "color": PALETTE[(g - 1) % len(PALETTE)],
                "n_nodes": int(cs["n_nodes"]), "frac_nodes": float(cs["frac_nodes"]),
                "intra_weight_frac": float(cs["intra_weight_frac"]), "k": int(cs["k"]),
                "n_selected": int(st["selecionados"]) if st is not None else 0,
                "n_hydrated": int(st["hidratados"]) if st is not None else 0,
                "n_not_found": int(st["nao_encontrados"]) if st is not None else 0,
                "n_not_authorized": int(st["nao_autorizados"]) if st is not None else 0,
                "n_other_errors": int(st["outros_erros"]) if st is not None else 0,
                "n_pending": int(st["pendentes"]) if st is not None else 0,
                "attrition": float(st["atricao"]) if st is not None else 0.0,
            })
        clusters.sort(key=lambda x: x["group"])
        return {
            "slug": slug,
            "name": row["name"] if row else slug,
            "event_date": row["event_date"] if row else None,
            "n_nodes": int(len(nodes)), "n_edges": int(n_edges),
            "n_communities": int(len(group_of)),
            "run_config": run_config,
            "selection": stats["params"],
            "clusters": clusters,
            "files": {"tweets": f"{slug}/tweets.json", "layout": f"{slug}/layout.json"},
        }

    def _slots(self, slug, group_of) -> list[dict]:
        rows = self.db.conn.execute(SLOTS_SQL, (slug,)).fetchall()
        where = defaultdict(list)                                  # tweet_id -> [(community, rank)]
        for r in rows:
            where[r["tweet_id"]].append((int(r["community"]), int(r["rank"])))

        slots = []
        for r in rows:
            c = int(r["community"])
            tweet_raw = json.loads(r["tweet_json"]) if r["tweet_json"] else None
            user_raw = json.loads(r["user_json"]) if r["user_json"] else None
            hydrated = tweet_raw is not None
            if not hydrated:
                author_status = None
            elif user_raw is not None:
                author_status = "hydrated"
            else:
                author_status = _status(False, r["user_err_title"])
            rt_graph = int(r["rt_graph"])
            slots.append({
                "community": c, "group": group_of[c], "rank": int(r["rank"]), "k": int(r["k"]),
                "tweet_id": r["tweet_id"],
                "rt_cluster": int(r["rt_cluster"]), "rt_graph": rt_graph, "rt_event": int(r["rt_event"]),
                "purity": round(int(r["rt_cluster"]) / rt_graph, 4) if rt_graph else None,
                "also_in": [{"community": oc, "group": group_of[oc], "rank": orank}
                            for oc, orank in where[r["tweet_id"]] if oc != c],
                "status": _status(hydrated, r["err_title"]),
                "error": ({"title": r["err_title"], "detail": r["err_detail"]}
                          if (not hydrated and r["err_title"]) else None),
                "tweet": _tweet_view(tweet_raw) if hydrated else None,
                "author_id": r["author_id"],
                "author": _author_view(user_raw) if user_raw else None,
                "author_status": author_status,
            })
        return slots

    @staticmethod
    def _layout(layout: CommunityLayout, group_of) -> dict:
        xy, comm = layout.coords, layout.community
        centroids = {}
        for c in np.unique(comm):
            m = comm == c
            centroids[str(int(c))] = [round(float(np.median(xy[m, 0])), 2),
                                      round(float(np.median(xy[m, 1])), 2)]
        return {
            "n_nodes": int(layout.n_nodes), "n_plotted": int(len(xy)),
            "top_k": int(layout.top_k), "seed": int(layout.seed),
            "x": [round(float(v), 2) for v in xy[:, 0]],
            "y": [round(float(v), 2) for v in xy[:, 1]],
            "community": [int(v) for v in comm],
            "centroids": centroids,
            "groups": {str(c): g for c, g in group_of.items()},
        }

    # --- hooks de cache (Stage): FILES vazio → run() sempre computa ---------
    def _compute(self, processed_dir) -> dict:
        return self.export(processed_dir)

    def _save(self, result: dict, out_dir) -> None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        _dump(out / "event.json", result["event"])
        _dump(out / "tweets.json", result["tweets"])
        _dump(out / "layout.json", result["layout"], compact=True)

    def _load(self, out_dir):
        raise NotImplementedError("FILES vazio — este estágio nunca carrega de disco")


def write_index(export_dir, slugs) -> Path:
    """Monta `index.json` a partir dos `event.json` já exportados (na ordem dada)."""
    export_dir = Path(export_dir)
    events = [json.loads((export_dir / slug / "event.json").read_text()) for slug in slugs]
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "palette": list(PALETTE),
        "events": events,
    }
    path = export_dir / "index.json"
    _dump(path, index)
    return path
