"""Módulo 6 — detecção de comunidades (Leiden)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import igraph as ig
import numpy as np
import pandas as pd

from modules.project import ProjectedGraph
from modules.stage import Stage


@dataclass
class CommunityResult:
    """Grafo igraph com comunidades + partição crua + mapeamento de usuário."""

    g: ig.Graph
    partition: ig.VertexClustering
    membership: list
    user_index: np.ndarray

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        self.g.write_graphml(str(out / "community_graph.graphml"))
        pd.DataFrame(
            {"user_id": self.user_index, "community": self.membership}
        ).to_parquet(out / "membership.parquet", index=False)
        return out


class CommunityDetector(Stage):
    """Roda Leiden (objetivo de modularidade) sobre o grafo de backbone."""

    FILES = ("community_graph.graphml", "membership.parquet")

    def __init__(self, resolution: float = 1.0,
                 objective_function: str = "modularity",
                 n_iterations: int = -1):
        self.resolution = resolution
        self.objective_function = objective_function
        self.n_iterations = n_iterations

    def detect(self, pg: ProjectedGraph) -> CommunityResult:
        W = pg.W.tocoo()
        n = len(pg.user_index)
        edges = list(zip(W.row.tolist(), W.col.tolist()))

        g = ig.Graph(n=n, edges=edges, directed=False)
        g.es["weight"] = W.data.tolist()
        g.vs["user_id"] = [str(u) for u in pg.user_index]

        partition = g.community_leiden(
            weights="weight",
            objective_function=self.objective_function,
            resolution=self.resolution,
            n_iterations=self.n_iterations,
        )
        membership = list(partition.membership)
        g.vs["community"] = membership

        return CommunityResult(
            g=g,
            partition=partition,
            membership=membership,
            user_index=pg.user_index,
        )

    # --- hooks de cache (Stage) ---
    def _compute(self, pg: ProjectedGraph) -> CommunityResult:
        return self.detect(pg)

    def _save(self, cr: CommunityResult, out_dir) -> None:
        cr.save(out_dir)

    def _load(self, out_dir) -> CommunityResult:
        out = Path(out_dir)
        g = ig.Graph.Read_GraphML(str(out / "community_graph.graphml"))
        mdf = pd.read_parquet(out / "membership.parquet")
        membership = mdf["community"].astype(int).tolist()
        partition = ig.VertexClustering(
            g, membership, modularity_params={"weights": "weight"}
        )
        return CommunityResult(
            g=g,
            partition=partition,
            membership=membership,
            user_index=mdf["user_id"].values,
        )
