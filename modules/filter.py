"""Módulo 2 — filtragem de ruído (usuários inativos + tweets virais)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _counts(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "users": int(df["author_id"].nunique()),
        "tweets": int(df["referenced_tweet_id"].nunique()),
    }


class NoiseFilter:
    """Dois filtros sequenciais: usuários inativos e tweets virais espúrios."""

    def __init__(self, min_user_retweets: int = 3, viral_user_fraction: float = 0.30):
        self.min_user_retweets = min_user_retweets
        self.viral_user_fraction = viral_user_fraction
        self.stats: dict = {}

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        self.stats = {"initial": _counts(df)}

        # Filtro 1 — usuários com menos de N retweets (ações)
        user_size = df.groupby("author_id")["referenced_tweet_id"].transform("size")
        df = df[user_size >= self.min_user_retweets]
        self.stats["after_user_filter"] = _counts(df)

        # Filtro 2 — tweets retuitados por mais de X% dos usuários remanescentes
        n_users = df["author_id"].nunique()
        max_users = self.viral_user_fraction * n_users
        users_per_tweet = df.groupby("referenced_tweet_id")["author_id"].transform("nunique")
        df = df[users_per_tweet <= max_users]
        self.stats["after_viral_filter"] = _counts(df)

        return df.reset_index(drop=True)

    def save(self, df: pd.DataFrame, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out / "filtered_retweets.parquet", index=False)
        with open(out / "filter_stats.json", "w") as f:
            json.dump(self.stats, f, indent=2)
        return out / "filtered_retweets.parquet"
