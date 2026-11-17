"""Módulo 12 — mapa dos grupos para o leitor web ("grupos primeiro").

Duas partes, como no M7:

- `GroupMap` (Stage, cacheado em `data/processed/<evento>/`): a parte cara. Refaz a componente
  gigante do grafo top-k do M7, roda o ForceAtlas2 (fa2_modified, sem pesos, semente fixa) e guarda,
  por nó, as coordenadas FA2 e DRL e o grau no grafo completo; guarda também a ligação mais forte de
  cada nó dentro do grupo (textura), as ligações mais fortes entre cada par de grupos (pontes,
  ordenadas por peso) e o total de ligações por par.
- `GroupMapRenderer` (sempre refeito): arranja os grupos e desenha. Cada grupo ocupa uma região com
  raio ∝ √pessoas e forma interna do FA2; um **par dominante** (D18) vira uma unidade só, com a forma
  conjunta do DRL. Grava em `data/export/<evento>/` as imagens clara e escura (e miniaturas), uma
  imagem por grupo em destaque (`grafo-<tema>-g<comunidade>.webp`: o grupo colorido, os demais em cinza) e
  `grafo.json`: âncoras dos rótulos e uma grade que diz qual grupo ocupa cada célula (clique).

É apresentação: posições e cortes de arestas não entram em nenhuma medida da pesquisa.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import igraph as ig
import matplotlib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import scipy.sparse as sp

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402

from modules.stage import Stage  # noqa: E402

GROUP_COLORS = ["#5E4FA2", "#26A69A", "#E8852B", "#E2B33C", "#B5651D"]
OTHER_COLOR = "#BDB8CC"
BG = {"claro": "#FFFFFF", "escuro": "#13111B"}
MUTED = {"claro": "#D8D4E0", "escuro": "#3A3548"}  # demais grupos quando um está em destaque
DOMINANT_SHARE = 0.40
DOMINANT_CONCENTRATION = 0.70
ISOLATED_MAX = 0.10
MAX_BRIDGE_CANDIDATES = 900
EXTENT = 1.06
FILL = 0.90  # meia-largura ocupada pelos pontos; o resto da moldura é respiro para os rótulos


def top_k_edges(src, dst, w, k: int) -> np.ndarray:
    """Índices das arestas que estão entre as k mais fortes de pelo menos um dos extremos (união)."""
    eid = np.arange(len(w))
    node = np.concatenate([src, dst])
    wt = np.concatenate([w, w])
    ee = np.concatenate([eid, eid])
    o = np.lexsort((-wt, node))
    node_s, ee_s = node[o], ee[o]
    _, start = np.unique(node_s, return_index=True)
    pos = np.arange(len(node_s)) - np.repeat(start, np.diff(np.append(start, len(node_s))))
    return np.unique(ee_s[pos < k])


def dominant_pairs(clusters, min_share=DOMINANT_SHARE, min_concentration=DOMINANT_CONCENTRATION):
    """Pares (a, b, share) em que um grupo manda ≥ min_share do que retuíta ao outro e esse parceiro
    concentra ≥ min_concentration de tudo o que ele compartilha (`shared_with`, D17)."""
    by = {c["community"]: c for c in clusters}
    out = []
    ids = list(by)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            best = 0.0
            for x, y in ((a, b), (b, a)):
                s = (by[x].get("shared_with") or {}).get(str(y), 0.0)
                total = by[x].get("shared") or 0.0
                if s >= min_share and total > 0 and s / total >= min_concentration:
                    best = max(best, s)
            if best:
                out.append((min(a, b), max(a, b), round(best, 3)))
    return sorted(out, key=lambda t: -t[2])


def placement_units(communities, pairs):
    """Unidades de posicionamento: cada par dominante vira uma; os demais grupos, uma cada."""
    units, used = [], set()
    for a, b, _ in pairs:
        if a not in used and b not in used:
            units.append((a, b))
            used |= {a, b}
    return units + [(c,) for c in communities if c not in used]


def arrange_units(units, radius, start, strength, gap: float, isolated, iterations=3000):
    """Centros das unidades: alvo de distância cai com a força da ligação; nunca abaixo de
    gap × (soma dos raios); unidades isoladas vão para fora das demais."""
    pos = {u: np.array(start[u], float) for u in units}

    def target(a, b):
        return (radius[a] + radius[b]) * (gap + 0.6 * (1 - strength(a, b)))

    def step(fn, rate):
        for i, a in enumerate(units):
            for b in units[i + 1:]:
                v = pos[b] - pos[a]
                d = np.linalg.norm(v) + 1e-9
                t = fn(a, b, d)
                if t is None:
                    continue
                mv = (d - t) / d * rate
                pos[a] += v * mv
                pos[b] -= v * mv

    for _ in range(iterations):
        step(lambda a, b, d: target(a, b), 0.05)
    for _ in range(iterations):
        step(lambda a, b, d: gap * 1.05 * (radius[a] + radius[b]) if d < gap * 1.05 * (radius[a] + radius[b]) else None, 0.25)
    others_all = [u for u in units if u not in isolated]
    for u in units:
        if u not in isolated or not others_all:
            continue
        center = np.mean([pos[w] for w in others_all], axis=0)
        direction = pos[u] - center
        norm = np.linalg.norm(direction)
        direction = direction / norm if norm > 1e-6 else np.array([1.0, 0.0])
        reach = max(np.linalg.norm(pos[w] - center) + radius[w] for w in others_all)
        pos[u] = center + direction * (reach + radius[u] * gap + 0.15)
    return pos


def hit_grid(x01, y01, comm, n: int) -> list[int]:
    """Grade n×n (linha a linha, de cima) com o grupo majoritário de cada célula; células vazias
    vizinhas de um grupo herdam a maioria da vizinhança; o resto é -1."""
    ix = np.clip((np.asarray(x01) * n).astype(int), 0, n - 1)
    iy = np.clip((np.asarray(y01) * n).astype(int), 0, n - 1)
    groups = np.unique(comm)
    counts = np.zeros((len(groups), n, n))
    gi = np.searchsorted(groups, comm)
    np.add.at(counts, (gi, iy, ix), 1)
    total = counts.sum(axis=0)
    padded = np.pad(counts, ((0, 0), (1, 1), (1, 1)))
    neigh = sum(padded[:, 1 + dy:1 + dy + n, 1 + dx:1 + dx + n] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    best = np.where(total > 0, counts.argmax(axis=0), neigh.argmax(axis=0))
    filled = (total > 0) | (neigh.sum(axis=0) > 0)
    cells = np.where(filled, groups[best], -1)
    return [int(c) for c in cells.ravel()]


class GroupMap(Stage):
    """M12 (parte cara) — FA2 da componente gigante + arestas de exibição, por evento."""

    FILES = ("group_map_nodes.parquet", "group_map_edges.parquet", "group_map.json")

    def __init__(self, top_k: int = 12, seed: int = 42, iterations: int = 800, min_frac: float = 0.01):
        self.top_k = top_k
        self.seed = seed
        self.iterations = iterations
        self.min_frac = min_frac

    def build(self, processed_dir) -> dict:
        d = Path(processed_dir)
        memb = pq.read_table(d / "graph_nodes.parquet").column("community").to_numpy()
        e = pq.read_table(d / "graph_edges.parquet").to_pandas()
        src, dst, w = e["src"].to_numpy(), e["dst"].to_numpy(), e["weight"].to_numpy()
        n_all = len(memb)

        k12 = top_k_edges(src, dst, w, self.top_k)
        random.seed(self.seed)
        ig.set_random_number_generator(random)
        g = ig.Graph(n=n_all, edges=np.column_stack([src[k12], dst[k12]]).tolist())
        gc = np.sort(np.array(max(g.connected_components(), key=len)))
        drl = pd.read_parquet(d / "drl_layout.parquet")
        if len(drl) != len(gc) or not (drl["community"].to_numpy() == memb[gc]).all():
            raise ValueError("drl_layout não corresponde à componente gigante do top-k; rode o M7 de novo")
        local = -np.ones(n_all, dtype=np.int64)
        local[gc] = np.arange(len(gc))

        a, b = local[src[k12]], local[dst[k12]]
        keep = (a >= 0) & (b >= 0) & (a != b)
        adj = sp.coo_matrix((np.ones(keep.sum()), (a[keep], b[keep])), shape=(len(gc), len(gc))).tocsr()
        adj = ((adj + adj.T) > 0).astype(float)
        from fa2_modified import ForceAtlas2
        rng = np.random.default_rng(self.seed)
        fa = ForceAtlas2(outboundAttractionDistribution=False, edgeWeightInfluence=0, jitterTolerance=1.0,
                         barnesHutOptimize=True, barnesHutTheta=1.2, scalingRatio=2.0,
                         strongGravityMode=False, gravity=1.0, verbose=False)
        fa2 = np.asarray(fa.forceatlas2(adj, pos=rng.random((len(gc), 2)) * 100, iterations=self.iterations))

        degree = (np.bincount(src, minlength=n_all) + np.bincount(dst, minlength=n_all))[gc]
        nodes = pd.DataFrame({"node": gc, "community": memb[gc], "fa2_x": fa2[:, 0], "fa2_y": fa2[:, 1],
                              "drl_x": drl["x"].to_numpy(), "drl_y": drl["y"].to_numpy(), "degree": degree})

        k1 = top_k_edges(src, dst, w, 1)
        a1, b1 = local[src[k1]], local[dst[k1]]
        m1 = (a1 >= 0) & (b1 >= 0) & (memb[src[k1]] == memb[dst[k1]])
        intra = pd.DataFrame({"kind": "intra", "a": a1[m1], "b": b1[m1], "weight": w[k1][m1]})

        sizes = pd.Series(memb).value_counts()
        big = set(sizes[sizes >= self.min_frac * n_all].index.tolist())
        ca, cb = memb[src], memb[dst]
        inter = (ca != cb) & np.isin(ca, list(big)) & np.isin(cb, list(big))
        df = pd.DataFrame({"a": local[src[inter]], "b": local[dst[inter]], "weight": w[inter],
                           "ka": np.minimum(ca[inter], cb[inter]), "kb": np.maximum(ca[inter], cb[inter])})
        totals = df.groupby(["ka", "kb"]).size()
        df = df[(df["a"] >= 0) & (df["b"] >= 0)]
        mx = totals.max() if len(totals) else 1
        parts = []
        for (ka, kb), n in totals.items():
            take = int(max(12, MAX_BRIDGE_CANDIDATES * np.sqrt(n / mx)))
            parts.append(df[(df["ka"] == ka) & (df["kb"] == kb)].nlargest(take, "weight"))
        bridges = (pd.concat(parts) if parts else df.head(0))[["a", "b", "weight"]].assign(kind="bridge")
        edges = pd.concat([intra, bridges[["kind", "a", "b", "weight"]]], ignore_index=True)
        return {"nodes": nodes, "edges": edges,
                "pair_counts": {f"{ka}-{kb}": int(n) for (ka, kb), n in totals.items()},
                "params": {"top_k": self.top_k, "seed": self.seed, "iterations": self.iterations}}

    def _compute(self, processed_dir) -> dict:
        return self.build(processed_dir)

    def _save(self, result: dict, out_dir) -> None:
        out = Path(out_dir)
        result["nodes"].to_parquet(out / "group_map_nodes.parquet", index=False)
        result["edges"].to_parquet(out / "group_map_edges.parquet", index=False)
        (out / "group_map.json").write_text(json.dumps({"pair_counts": result["pair_counts"],
                                                         "params": result["params"]}, indent=1))

    def _load(self, out_dir) -> dict:
        out = Path(out_dir)
        meta = json.loads((out / "group_map.json").read_text())
        return {"nodes": pd.read_parquet(out / "group_map_nodes.parquet"),
                "edges": pd.read_parquet(out / "group_map_edges.parquet"), **meta}


def _soft_unit(v, q: float) -> np.ndarray:
    r = np.linalg.norm(v, axis=1)
    r90, rq = np.percentile(r, 90), np.percentile(r, q)
    rs = np.where(r <= r90, r, r90 * (1 + 0.25 * np.tanh((r - r90) / (0.25 * r90))))
    return v * (rs / np.maximum(r, 1e-9))[:, None] / rq


def _lighten(rgb, amount):
    return tuple(x + (1 - x) * amount for x in rgb)


class GroupMapRenderer:
    """M12 (desenho) — arranja os grupos de um evento e grava imagens + `grafo.json` no export."""

    def __init__(self, gap: float = 1.25, max_bridges: int = 90, grid: int = 64, size_px: int = 1400, mini_px: int = 480):
        self.gap = gap
        self.max_bridges = max_bridges
        self.grid = grid
        self.size_px = size_px
        self.mini_px = mini_px

    def layout(self, gm: dict, clusters: list[dict]):
        nodes, edges = gm["nodes"], gm["edges"]
        comm = nodes["community"].to_numpy()
        fa2 = nodes[["fa2_x", "fa2_y"]].to_numpy()
        drl = nodes[["drl_x", "drl_y"]].to_numpy()
        by = {c["community"]: c for c in clusters}
        sel = list(by)
        pairs = dominant_pairs(clusters)
        units = placement_units(sel, pairs)
        radius = {u: float(np.sqrt(sum(by[c]["frac_nodes"] for c in u))) for u in units}
        local = np.full_like(fa2, np.nan)
        start = {}
        for u in units:
            m = np.isin(comm, u)
            src_xy = drl if len(u) > 1 else fa2
            p = src_xy[m]
            local[m] = _soft_unit(p - np.median(p, axis=0), 55 if len(u) > 1 else 90) * radius[u]
            start[u] = np.median(fa2[m], axis=0)
        scale = np.mean([np.linalg.norm(start[a] - start[b]) for a in units for b in units if a != b] or [1.0]) or 1.0
        start = {u: start[u] / scale * 2 for u in units}

        density = {}
        for key, n in gm["pair_counts"].items():
            ka, kb = (int(x) for x in key.split("-"))
            if ka in by and kb in by:
                density[(ka, kb)] = n / (by[ka]["n_nodes"] * by[kb]["n_nodes"])
        mxd = max(density.values()) if density else 1.0

        def share(a, b):
            return max((by[a].get("shared_with") or {}).get(str(b), 0.0), (by[b].get("shared_with") or {}).get(str(a), 0.0))

        def strength(u, w):
            return (max(density.get((min(a, b), max(a, b)), 0.0) for a in u for b in w) / mxd) ** 0.5

        isolated = {u for u in units if len(units) > 2
                    and max(share(a, b) for a in u for w in units if w != u for b in w) < ISOLATED_MAX}
        centers = arrange_units(units, radius, start, strength, self.gap, isolated)
        xy = np.full_like(fa2, np.nan)
        for u in units:
            m = np.isin(comm, u)
            xy[m] = centers[u] + local[m]
        keep = ~np.isnan(xy[:, 0])
        lo, hi = xy[keep].min(axis=0), xy[keep].max(axis=0)
        mid, half = (lo + hi) / 2, (hi - lo).max() / 2 / FILL
        xy = np.where(keep[:, None], (xy - mid) / half, 0.0)

        intra = edges[edges["kind"] == "intra"]
        bridges = edges[edges["kind"] == "bridge"]
        ka = np.minimum(comm[bridges["a"]], comm[bridges["b"]])
        kb = np.maximum(comm[bridges["a"]], comm[bridges["b"]])
        mxn = max(gm["pair_counts"].values()) if gm["pair_counts"] else 1
        cap = {tuple(int(x) for x in k.split("-")): int(max(4, self.max_bridges * np.sqrt(n / mxn)))
               for k, n in gm["pair_counts"].items()}
        rank = bridges.assign(ka=ka, kb=kb).groupby(["ka", "kb"]).cumcount().to_numpy()
        limit = np.array([cap.get((int(x), int(y)), 0) for x, y in zip(ka, kb)])
        shown = bridges[rank < limit]
        return {"xy": xy, "keep": keep, "comm": comm, "units": units, "pairs": pairs, "by": by,
                "intra": intra, "bridges": shown, "degree": nodes["degree"].to_numpy()}

    def _draw(self, lay, theme: str, path: Path, px: int, mini: bool, focus: int | None = None):
        """Desenha o grafo; com `focus`, só esse grupo fica colorido (e por cima) e os demais em cinza."""
        xy, keep, comm, by = lay["xy"], lay["keep"], lay["comm"], lay["by"]
        base = np.array([to_rgb(GROUP_COLORS[(by[c]["group"] - 1) % len(GROUP_COLORS)]) if c in by else to_rgb(OTHER_COLOR)
                         for c in comm])
        colors = np.array([_lighten(c, 0.18) for c in base]) if theme == "escuro" else base
        lit = np.ones(len(comm), dtype=bool) if focus is None else comm == focus
        colors = np.where(lit[:, None], colors, np.array(to_rgb(MUTED[theme])))
        deg = lay["degree"]
        rank = deg.argsort().argsort() / max(len(deg) - 1, 1)
        scale = (px / self.size_px) ** 2 * (1.8 if mini else 1.0)
        size = (1.2 + 16 * rank ** 4) * scale
        dpi = 200
        fig = plt.figure(figsize=(px / dpi, px / dpi), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        fig.patch.set_facecolor(BG[theme])
        ax.set_facecolor(BG[theme])
        if not mini:
            it = lay["intra"]
            a, b = it["a"].to_numpy(), it["b"].to_numpy()
            m = keep[a] & keep[b]
            ax.add_collection(LineCollection(np.stack([xy[a[m]], xy[b[m]]], 1), colors=colors[a[m]], linewidths=0.2,
                                             alpha=0.05 if theme == "escuro" else 0.035, zorder=1))
            segs, cols = [], []
            t = np.linspace(0, 1, 12)[:, None]
            for u, v in zip(lay["bridges"]["a"].to_numpy(), lay["bridges"]["b"].to_numpy()):
                if not (keep[u] and keep[v]):
                    continue
                p, q = xy[u], xy[v]
                ctrl = (p + q) / 2 + 0.18 * np.array([-(q - p)[1], (q - p)[0]])
                pts = (1 - t) ** 2 * p + 2 * (1 - t) * t * ctrl + t ** 2 * q
                segs += [pts[:6], pts[5:]]
                cols += [colors[u], colors[v]]
            ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.4,
                                             alpha=0.3 if theme == "escuro" else 0.22, zorder=2))
        rng = np.random.default_rng(0)
        order = np.lexsort((rng.random(len(size)), size, lit))
        order = order[keep[order]]
        ax.scatter(xy[order, 0], xy[order, 1], s=size[order], c=colors[order], alpha=0.9, linewidths=0, zorder=3)
        ax.set_xlim(-EXTENT, EXTENT)
        ax.set_ylim(-EXTENT, EXTENT)
        ax.axis("off")
        fig.savefig(path, facecolor=BG[theme], format="webp", pil_kwargs={"quality": 82})
        plt.close(fig)

    def render(self, processed_dir, event_meta: dict, out_dir) -> dict:
        gm = GroupMap()._load(processed_dir)
        lay = self.layout(gm, event_meta["clusters"])
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for theme in ("claro", "escuro"):
            self._draw(lay, theme, out / f"grafo-{theme}.webp", self.size_px, mini=False)
            self._draw(lay, theme, out / f"grafo-{theme}-mini.webp", self.mini_px, mini=True)
            for c in lay["by"]:
                self._draw(lay, theme, out / f"grafo-{theme}-g{c}.webp", self.size_px, mini=False, focus=c)

        xy, keep, comm = lay["xy"], lay["keep"], lay["comm"]
        to01 = lambda p: ((p[..., 0] + EXTENT) / (2 * EXTENT), 1 - (p[..., 1] + EXTENT) / (2 * EXTENT))  # noqa: E731
        sel_mask = keep & np.isin(comm, list(lay["by"]))
        x01, y01 = to01(xy[sel_mask])
        groups = []
        for u in lay["units"]:
            upts = xy[np.isin(comm, u) & keep]
            for i, c in enumerate(sorted(u, key=lambda c: lay["by"][c]["group"])):
                pts = xy[(comm == c) & keep]
                top = i == 0
                y = np.percentile(upts[:, 1], 98) if top else np.percentile(upts[:, 1], 2)
                lx, ly = to01(np.array([np.median(pts[:, 0]), y]))
                groups.append({"community": int(c), "group": int(lay["by"][c]["group"]),
                               "label_x": round(float(lx), 4), "label_y": round(float(ly), 4),
                               "anchor": "bottom" if top else "top"})
        info = {
            "groups": sorted(groups, key=lambda g: g["group"]),
            "dominant_pairs": [{"a": a, "b": b, "share": s} for a, b, s in lay["pairs"]],
            "grid": {"n": self.grid, "cells": hit_grid(x01, y01, comm[sel_mask], self.grid)},
            "params": {"gap": self.gap, "max_bridges": self.max_bridges,
                       "dominant_share": DOMINANT_SHARE, "dominant_concentration": DOMINANT_CONCENTRATION,
                       "isolated_max": ISOLATED_MAX, **gm.get("params", {})},
        }
        (out / "grafo.json").write_text(json.dumps(info, ensure_ascii=False, separators=(",", ":")))
        return info
