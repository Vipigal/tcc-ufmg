"""Módulo 5 — detecção de comunidades (Leiden) + serialização final.

Resultado final da pipeline, gravado em dois parquets autocontidos:
  - `graph_edges.parquet` (src, dst, weight) — arestas do backbone;
  - `graph_nodes.parquet` (user_id, community) — nós e sua comunidade.

Desses dois arquivos todo o resto é recuperável; os artefatos dos módulos 1–4
podem ser apagados depois (ver `modules.cleanup`). O `graph_nodes.parquet` é o
acumulador natural para atributos por usuário das etapas seguintes (score
ideológico, coordenadas de layout, grau).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import igraph as ig
import numpy as np
import pandas as pd
import scipy.sparse as sp

from modules.project import ProjectedGraph
from modules.stage import Stage


def _build_igraph(W: sp.spmatrix) -> ig.Graph:
    """Constrói o igraph a partir da matriz esparsa"""
    Wc = W.tocoo()
    g = ig.Graph(n=W.shape[0], edges=np.column_stack([Wc.row, Wc.col]))
    g.es["weight"] = Wc.data
    return g


@dataclass
class CommunityResult:
    """Grafo igraph com comunidades + partição + mapeamento de usuário + matriz."""

    g: ig.Graph
    partition: ig.VertexClustering
    membership: list
    user_index: np.ndarray
    W: sp.csr_matrix

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        Wc = self.W.tocoo()
        pd.DataFrame(
            {
                "src": Wc.row.astype(np.int32),
                "dst": Wc.col.astype(np.int32),
                "weight": Wc.data.astype(np.float32),
            }
        ).to_parquet(out / "graph_edges.parquet", index=False, compression="zstd")
        pd.DataFrame(
            {
                "user_id": self.user_index,
                "community": np.asarray(self.membership, dtype=np.int32),
            }
        ).to_parquet(out / "graph_nodes.parquet", index=False, compression="zstd")
        return out


class CommunityDetector(Stage):
    """Roda Leiden (objetivo de modularidade) e grava o grafo final em 2 parquets."""

    FILES = ("graph_edges.parquet", "graph_nodes.parquet")

    def __init__(self, resolution: float = 1.0,
                 objective_function: str = "modularity",
                 n_iterations: int = -1):
        self.resolution = resolution
        self.objective_function = objective_function
        self.n_iterations = n_iterations

    def detect(self, pg: ProjectedGraph) -> CommunityResult:
        g = _build_igraph(pg.W)
        partition = g.community_leiden(
            weights="weight",
            objective_function=self.objective_function,
            resolution=self.resolution,
            n_iterations=self.n_iterations,
        )
        membership = list(partition.membership)
        g.vs["community"] = membership
        g.vs["user_id"] = [str(u) for u in pg.user_index]
        return CommunityResult(
            g=g, partition=partition, membership=membership,
            user_index=pg.user_index, W=pg.W,
        )

    # --- hooks de cache (Stage) ---
    def _compute(self, pg: ProjectedGraph) -> CommunityResult:
        return self.detect(pg)

    def _save(self, cr: CommunityResult, out_dir) -> None:
        cr.save(out_dir)

    def _load(self, out_dir) -> CommunityResult:
        out = Path(out_dir)
        edges = pd.read_parquet(out / "graph_edges.parquet")
        nodes = pd.read_parquet(out / "graph_nodes.parquet")
        n = len(nodes)
        W = sp.coo_matrix(
            (edges["weight"].to_numpy(),
             (edges["src"].to_numpy(), edges["dst"].to_numpy())),
            shape=(n, n),
        ).tocsr()
        membership = nodes["community"].astype(int).tolist()
        g = _build_igraph(W)
        g.vs["community"] = membership
        g.vs["user_id"] = [str(u) for u in nodes["user_id"].to_numpy()]
        partition = ig.VertexClustering(
            g, membership, modularity_params={"weights": "weight"}
        )
        return CommunityResult(
            g=g, partition=partition, membership=membership,
            user_index=nodes["user_id"].to_numpy(), W=W,
        )
