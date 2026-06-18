"""Módulo 5 — backbone extraction por universal threshold."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from modules.project import ProjectedGraph


class BackboneExtractor:
    """Mantém arestas com peso ≥ tau e descarta nós que ficaram isolados."""

    def __init__(self, tau: float = 0.1):
        self.tau = tau
        self.stats: dict = {}

    def extract(self, pg: ProjectedGraph) -> ProjectedGraph:
        W = pg.W.tocoo()
        self.stats = {"before": {"nodes": int(len(pg.user_index)),
                                 "edges": int(W.nnz)}}

        keep = W.data >= self.tau
        rows, cols, vals = W.row[keep], W.col[keep], W.data[keep]

        # nós que ainda participam de alguma aresta
        if len(rows):
            used = np.unique(np.concatenate([rows, cols]))
        else:
            used = np.array([], dtype=int)

        remap = {int(old): new for new, old in enumerate(used)}
        new_rows = np.array([remap[int(r)] for r in rows], dtype=int)
        new_cols = np.array([remap[int(c)] for c in cols], dtype=int)

        W_new = sp.coo_matrix(
            (vals, (new_rows, new_cols)), shape=(len(used), len(used))
        ).tocsr()
        user_index = pg.user_index[used]

        self.stats["after"] = {"nodes": int(len(used)), "edges": int(W_new.nnz)}
        return ProjectedGraph(W=W_new, user_index=user_index)

    def save_stats(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "backbone_stats.json"
        with open(path, "w") as f:
            json.dump(self.stats, f, indent=2)
        return path
