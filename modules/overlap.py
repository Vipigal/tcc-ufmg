"""Conteúdo compartilhado entre clusters (D17, 2026-10-14) — a barra da visão geral do leitor.

Para o cluster c, sobre o log completo do evento (usuário×tweet distinto conta 1, como M3/M8):

    shared_with(c, d) = Σ_t rt_c(t) · rt_d(t) / rt_graph(t)  ÷  Σ_t rt_c(t)
    shared(c)         = Σ_{d≠c} shared_with(c, d)
                      = 1 − pureza média dos tweets que c retuita, ponderada por rt_c

"Dos retweets que c dá, que fração vai a conteúdo que também circula em d." É a mesma
pureza que o leitor mostra por tweet, agregada por cluster; não depende de definir polos e
é assimétrica (o grupo menor compartilha mais com o maior). Todos os clusters do grafo
contam como "outros"; só os de `clusters` (os selecionados no M8) são reportados.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from modules.stage import Stage


class ContentOverlap(Stage):
    FILES = ("content_overlap.json",)

    def __init__(self, clusters):
        self.clusters = [int(c) for c in clusters]

    def compute(self, nodes: pd.DataFrame, retweets: pd.DataFrame) -> dict:
        rt = retweets[["author_id", "referenced_tweet_id"]].astype(str).drop_duplicates()
        comm_of = pd.Series(nodes["community"].to_numpy().astype(int),
                            index=nodes["user_id"].astype(str).to_numpy())
        rt = rt.assign(community=rt["author_id"].map(comm_of)).dropna(subset=["community"])
        g = (rt.assign(community=rt["community"].astype(int))
             .groupby(["referenced_tweet_id", "community"]).size().unstack(fill_value=0))
        share = g.div(g.sum(axis=1), axis=0)            # rt_d(t) / rt_graph(t)
        out = {}
        for c in self.clusters:
            w = g[c] if c in g.columns else pd.Series(0, index=g.index)
            total = float(w.sum())
            with_ = {str(int(d)): (float((w * share[d]).sum()) / total if total else 0.0)
                     for d in g.columns if int(d) != c}
            out[str(c)] = {"n_retweets": int(total), "shared": float(sum(with_.values())),
                           "shared_with": with_}
        return {"clusters": out}

    # --- hooks de cache (Stage) ------------------------------------------
    def _compute(self, nodes, retweets) -> dict:
        return self.compute(nodes, retweets)

    def _save(self, result: dict, out_dir) -> None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "content_overlap.json").write_text(json.dumps(result, indent=1))

    def _load(self, out_dir) -> dict:
        return json.loads((Path(out_dir) / "content_overlap.json").read_text())
