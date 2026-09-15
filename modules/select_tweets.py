"""Módulo 8 — seleção dos tweets a hidratar, por cluster (D6, revisão 2026-09-10).

Primeiro estágio da fase 2. Consome os artefatos **finais** da fase 1
(`graph_nodes.parquet`, `graph_edges.parquet`) e o `retweets.parquet` (M1) do
evento, e produz a lista de tweets a hidratar por (cluster, rank):

  - **unidade de seleção:** cada comunidade Leiden com ≥ `min_frac` dos nós;
  - **critério de ranking:** nº de retweets ao tweet feitos por **membros do
    cluster** (nós do grafo). Retweet repetido do mesmo usuário conta 1 — a
    mesma binarização da matriz bipartida (M3);
  - **K por cluster:** `k`; ou `k_small` para clusters com ≤ `small_weight_frac`
    do peso de arestas do grafo em arestas internas. O denominador é o peso
    **total** do grafo (intra + inter), o mesmo da matriz de fluxo de M6 —
    com esse denominador c0/c4 de eleicoes ficam em ~5,5%, logo acima do corte;
  - **desempate determinístico:** rt_cluster desc → rt_graph desc → tweet_id asc.

Saída (`top_tweets.parquet`), uma linha por (community, tweet_id):

    community, rank, tweet_id, rt_cluster, rt_graph, rt_event, k

`rt_graph` (retweets por qualquer nó do grafo) e `rt_event` (por qualquer
usuário do evento, inclusive a periferia filtrada em M2) são contexto barato de
calcular junto e permitem derivar pureza e cobertura depois, sem reprocessar.
As estatísticas por cluster ficam em `top_tweets_stats.json`.

O mesmo tweet pode aparecer em mais de um cluster do evento — a deduplicação
para a hidratação (e o cache) é feita a jusante, no banco.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from modules.stage import Stage

COLUMNS = ["community", "rank", "tweet_id", "rt_cluster", "rt_graph", "rt_event", "k"]


def load_final_graph(out_dir) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê o resultado final da fase 1: (`graph_nodes`, `graph_edges`).

    Em `graph_edges`, `src`/`dst` são **posições** (linhas) de `graph_nodes`.
    """
    out = Path(out_dir)
    nodes = pd.read_parquet(out / "graph_nodes.parquet")
    edges = pd.read_parquet(out / "graph_edges.parquet")
    return nodes, edges


class TopTweetSelector(Stage):
    """M8 — top-K tweets por cluster, ranqueados por retweets dos membros."""

    FILES = ("top_tweets.parquet", "top_tweets_stats.json")

    def __init__(self, k: int = 100, k_small: int = 20,
                 min_frac: float = 0.01, small_weight_frac: float = 0.05):
        self.k = k
        self.k_small = k_small
        self.min_frac = min_frac                  # cluster entra se ≥ min_frac dos nós
        self.small_weight_frac = small_weight_frac  # ≤ isso do peso total → K pequeno
        self.stats: dict = {}

    # --- seleção ---------------------------------------------------------
    def select(self, nodes: pd.DataFrame, edges: pd.DataFrame,
               retweets: pd.DataFrame) -> pd.DataFrame:
        membership = nodes["community"].to_numpy().astype(int)
        n_nodes = len(nodes)
        n_comm = int(membership.max()) + 1 if n_nodes else 0

        sizes = pd.Series(membership).value_counts()                # descendente
        big = [int(c) for c in sizes.index if sizes[c] >= self.min_frac * n_nodes]

        # peso interno de cada cluster como fração do peso TOTAL do grafo
        w = edges["weight"].to_numpy(dtype=np.float64)
        W = float(w.sum())
        cs = membership[edges["src"].to_numpy()]
        cd = membership[edges["dst"].to_numpy()]
        same = cs == cd
        intra = (np.bincount(cs[same], weights=w[same], minlength=n_comm) / W
                 if W > 0 else np.zeros(n_comm))
        k_of = {c: (self.k_small if intra[c] <= self.small_weight_frac else self.k)
                for c in big}

        # contagens — (usuário, tweet) distinto conta 1
        rt = (retweets[["author_id", "referenced_tweet_id"]]
              .astype(str).drop_duplicates())
        rt_event = rt.groupby("referenced_tweet_id").size()
        comm_of = pd.Series(membership, index=nodes["user_id"].astype(str).to_numpy())
        rt = rt.assign(community=rt["author_id"].map(comm_of))
        in_graph = rt.dropna(subset=["community"])
        in_graph = in_graph.assign(community=in_graph["community"].astype(int))
        rt_graph = in_graph.groupby("referenced_tweet_id").size()
        pairs = (in_graph.groupby(["community", "referenced_tweet_id"]).size()
                 .rename("rt_cluster").reset_index())

        frames, clusters = [], {}
        for c in big:
            cand = pairs[pairs["community"] == c].copy()
            cand["rt_graph"] = cand["referenced_tweet_id"].map(rt_graph).astype(int)
            cand = cand.sort_values(["rt_cluster", "rt_graph", "referenced_tweet_id"],
                                    ascending=[False, False, True], kind="mergesort")
            top = cand.head(k_of[c]).copy()
            top["rank"] = np.arange(1, len(top) + 1)
            top["k"] = k_of[c]
            frames.append(top)
            clusters[str(c)] = {
                "n_nodes": int(sizes[c]),
                "frac_nodes": float(sizes[c] / n_nodes),
                "intra_weight_frac": float(intra[c]),
                "k": int(k_of[c]),
                "n_candidates": int(len(cand)),
                "n_selected": int(len(top)),
            }

        out = (pd.concat(frames, ignore_index=True) if frames
               else pd.DataFrame(columns=["community", "referenced_tweet_id",
                                          "rt_cluster", "rt_graph", "rank", "k"]))
        out = out.rename(columns={"referenced_tweet_id": "tweet_id"})
        out["rt_event"] = out["tweet_id"].map(rt_event).astype(int)
        out = out[COLUMNS].reset_index(drop=True)

        excluded = [int(c) for c in sizes.index if int(c) not in k_of]
        self.stats = {
            "params": {"k": self.k, "k_small": self.k_small, "min_frac": self.min_frac,
                       "small_weight_frac": self.small_weight_frac},
            "n_nodes": int(n_nodes),
            "n_communities": int(len(sizes)),
            "total_weight": W,
            "clusters": clusters,                       # na ordem de tamanho (desc)
            "n_excluded_clusters": len(excluded),
            "excluded_nodes_frac": float(sizes.loc[excluded].sum() / n_nodes) if n_nodes else 0.0,
            "n_slots": int(len(out)),
            "n_unique_ids": int(out["tweet_id"].nunique()),
            "n_overlap": int(len(out) - out["tweet_id"].nunique()),
        }
        return out

    def save(self, df: pd.DataFrame, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out / "top_tweets.parquet", index=False)
        (out / "top_tweets_stats.json").write_text(
            json.dumps(self.stats, indent=2, ensure_ascii=False))
        return out / "top_tweets.parquet"

    # --- hooks de cache (Stage) ------------------------------------------
    def _compute(self, nodes, edges, retweets) -> pd.DataFrame:
        return self.select(nodes, edges, retweets)

    def _save(self, df: pd.DataFrame, out_dir) -> None:
        self.save(df, out_dir)

    def _load(self, out_dir) -> pd.DataFrame:
        out = Path(out_dir)
        self.stats = json.loads((out / "top_tweets_stats.json").read_text())
        return pd.read_parquet(out / "top_tweets.parquet")
