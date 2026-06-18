"""Módulo 4 — projeção unipartida com peso Jaccard."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from modules.bipartite import BipartiteGraph


@dataclass
class ProjectedGraph:
    """Grafo unipartido usuário×usuário, triangular superior, peso Jaccard."""

    W: sp.csr_matrix
    user_index: np.ndarray

    def save(self, out_dir, prefix: str = "projection") -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        sp.save_npz(out / f"{prefix}_W.npz", self.W)
        pd.DataFrame({"user_id": self.user_index}).to_parquet(
            out / f"{prefix}_user_index.parquet", index=False
        )
        return out


class JaccardProjector:
    """Projeta a matriz bipartida em grafo de co-retweet com peso Jaccard."""

    def project(self, bg: BipartiteGraph) -> ProjectedGraph:
        # int64 evita overflow no produto B·Bᵀ (B é int8)
        B = bg.B.astype(np.int32)
        B = B.tocsr()
        C = (B @ B.T)                     # |T_u ∩ T_v|
        deg = np.asarray(B.sum(axis=1)).ravel()   # |T_u|

        # apenas triângulo superior (i < j), sem diagonal
        mask = C.row < C.col
        rows = C.row[mask]
        cols = C.col[mask]
        inter = C.data[mask]
        union = deg[rows] + deg[cols] - inter
        jac = inter / union

        n = len(bg.user_index)
        W = sp.coo_matrix((jac, (rows, cols)), shape=(n, n)).tocsr()
        return ProjectedGraph(W=W, user_index=bg.user_index)
