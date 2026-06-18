"""Módulo 3 — construção da matriz bipartida usuário × tweet."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp


@dataclass
class BipartiteGraph:
    """Matriz de incidência binária usuário × tweet + mapeamentos de índice."""

    B: sp.csr_matrix
    user_index: np.ndarray   # posição (linha) -> author_id
    tweet_index: np.ndarray  # posição (coluna) -> referenced_tweet_id

    def save(self, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        sp.save_npz(out / "bipartite_B.npz", self.B)
        pd.DataFrame({"user_id": self.user_index}).to_parquet(
            out / "bipartite_user_index.parquet", index=False
        )
        pd.DataFrame({"tweet_id": self.tweet_index}).to_parquet(
            out / "bipartite_tweet_index.parquet", index=False
        )
        return out


class BipartiteBuilder:
    """Constrói o BipartiteGraph a partir do DataFrame de retweets filtrado."""

    def build(self, df: pd.DataFrame) -> BipartiteGraph:
        user_codes, user_index = pd.factorize(df["author_id"])
        tweet_codes, tweet_index = pd.factorize(df["referenced_tweet_id"])

        data = np.ones(len(df), dtype=np.int8)
        B = sp.coo_matrix(
            (data, (user_codes, tweet_codes)),
            shape=(len(user_index), len(tweet_index)),
            dtype=np.int8
        ).tocsr()
        B.sum_duplicates()
        B.data = np.ones_like(B.data)  # binariza: retweet repetido conta 1

        return BipartiteGraph(
            B=B,
            user_index=np.asarray(user_index),
            tweet_index=np.asarray(tweet_index),
        )

    def load(self, in_dir) -> BipartiteGraph:
        in_ = Path(in_dir)
        B = sp.load_npz(in_ / "bipartite_B.npz").tocsr()
        user_index = pd.read_parquet(in_ / "bipartite_user_index.parquet")["user_id"].values
        tweet_index = pd.read_parquet(in_ / "bipartite_tweet_index.parquet")["tweet_id"].values
        return BipartiteGraph(B=B, user_index=user_index, tweet_index=tweet_index)
