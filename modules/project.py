"""Módulo 4 — projeção Jaccard em blocos + backbone (corte τ + remoção de isolados).

A projeção é feita em blocos de usuários, cortando o peso Jaccard em `tau`
*durante* a geração das arestas — nunca materializa o produto B·Bᵀ inteiro.
Em seguida remove nós que ficaram isolados (sem nenhuma aresta ≥ τ). O resultado
é o grafo de backbone, pronto para a detecção de comunidades.

O corte de Jaccard fica embutido aqui (não há um módulo de backbone separado):
J(u,v) depende só dos conjuntos T_u e T_v, então filtrar por τ na projeção dá
exatamente o mesmo grafo que projetar tudo e filtrar depois. Para a análise de
sensibilidade a τ, reprojetar com outro `tau` (ver D14 em decisoes-metodologicas.md).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from modules.bipartite import BipartiteGraph
from modules.stage import Stage


@dataclass
class ProjectedGraph:
    """Grafo unipartido usuário x usuário, triangular superior, peso Jaccard ≥ τ."""

    W: sp.csr_matrix
    user_index: np.ndarray

    def save(self, out_dir, prefix: str = "backbone") -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        sp.save_npz(out / f"{prefix}_W.npz", self.W)
        pd.DataFrame({"user_id": self.user_index}).to_parquet(
            out / f"{prefix}_user_index.parquet", index=False
        )
        return out


class JaccardProjector(Stage):
    """Projeta a bipartida em grafo de co-retweet (Jaccard ≥ τ) e remove isolados.

    Processa `block_size` usuários por vez, cortando o Jaccard em `tau` dentro de
    cada bloco — o pico de memória fica limitado ao bloco, não ao grafo inteiro.
    """

    FILES = ("backbone_W.npz", "backbone_user_index.parquet", "backbone_stats.json")

    def __init__(self, tau: float = 0.10, block_size: int = 2000):
        self.tau = tau
        self.block_size = block_size
        self.stats: dict = {}

    def project(self, bg: BipartiteGraph) -> ProjectedGraph:
        # matriz de incidência: incidence[u, t] = 1 se o usuário u retuitou o tweet t
        incidence = bg.B.astype(np.int32).tocsr()
        incidence_T = incidence.T.tocsr()
        tweets_per_user = np.asarray(incidence.sum(axis=1)).ravel().astype(np.int64)  # |T_u|
        n_users = incidence.shape[0]

        # acumuladores das arestas que sobrevivem ao corte τ
        kept_user_i, kept_user_j, kept_weight = [], [], []
        for block_start in range(0, n_users, self.block_size):
            block_end = min(block_start + self.block_size, n_users)

            # shared_counts[i, j] = nº de tweets em comum entre o usuário i (deste bloco) e o usuário j
            shared_counts = (incidence[block_start:block_end] @ incidence_T).tocoo()
            user_i = shared_counts.row + block_start     # índice global do 1º usuário do par
            user_j = shared_counts.col                   # índice do 2º usuário do par

            upper = user_j > user_i                      # mantém cada par uma vez (triângulo superior)
            user_i, user_j = user_i[upper], user_j[upper]
            intersection = shared_counts.data[upper].astype(np.int64)                 # |T_i ∩ T_j|
            union = tweets_per_user[user_i] + tweets_per_user[user_j] - intersection  # |T_i ∪ T_j|
            jaccard = intersection / union

            above_tau = jaccard >= self.tau              # backbone embutido na projeção
            kept_user_i.append(user_i[above_tau])
            kept_user_j.append(user_j[above_tau])
            kept_weight.append(jaccard[above_tau])

        edge_i = np.concatenate(kept_user_i) if kept_user_i else np.empty(0, np.int64)
        edge_j = np.concatenate(kept_user_j) if kept_user_j else np.empty(0, np.int64)
        edge_weight = np.concatenate(kept_weight) if kept_weight else np.empty(0, float)
        self.stats = {"before": {"nodes": int(n_users), "edges": int(len(edge_i))}}

        # remove usuários que ficaram isolados (sem nenhuma aresta ≥ τ) e reindexa de forma compacta
        active_users = (
            np.unique(np.concatenate([edge_i, edge_j])) if len(edge_i) else np.empty(0, np.int64)
        )
        new_index = np.full(n_users, -1, np.int64)       # índice antigo do usuário -> índice compacto
        new_index[active_users] = np.arange(len(active_users))
        weight_matrix = sp.coo_matrix(
            (edge_weight, (new_index[edge_i], new_index[edge_j])),
            shape=(len(active_users), len(active_users)),
        ).tocsr()
        self.stats["after"] = {"nodes": int(len(active_users)), "edges": int(weight_matrix.nnz)}
        return ProjectedGraph(W=weight_matrix, user_index=bg.user_index[active_users])

    # --- hooks de cache (Stage) ---
    def _compute(self, bg: BipartiteGraph) -> ProjectedGraph:
        return self.project(bg)

    def _save(self, pg: ProjectedGraph, out_dir) -> None:
        pg.save(out_dir, prefix="backbone")
        with open(Path(out_dir) / "backbone_stats.json", "w") as f:
            json.dump(self.stats, f, indent=2)

    def _load(self, out_dir) -> ProjectedGraph:
        out = Path(out_dir)
        W = sp.load_npz(out / "backbone_W.npz").tocsr()
        user_index = pd.read_parquet(out / "backbone_user_index.parquet")["user_id"].values
        self.stats = json.loads((out / "backbone_stats.json").read_text())
        return ProjectedGraph(W=W, user_index=user_index)
