"""Módulo 1 — carga e filtragem para retweets."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.stage import Stage


def _resolve_paths(csv_paths) -> list[Path]:
    if isinstance(csv_paths, (str, Path)):
        p = Path(csv_paths)
        if p.is_dir():
            return sorted(p.glob("*.csv"))
        return [p]
    return [Path(x) for x in csv_paths]


class RetweetLoader(Stage):
    """Lê os CSV(s) de um evento e mantém apenas os retweets.

    Aceita um caminho de arquivo, uma lista de caminhos ou um diretório
    (carrega todos os .csv contidos). Um evento pode ter vários CSVs.
    """

    FILES = ("retweets.parquet",)

    def __init__(self, csv_paths):
        self.paths = _resolve_paths(csv_paths)

    def load(self) -> pd.DataFrame:
        frames = [pd.read_csv(p, dtype=str) for p in self.paths]
        raw = pd.concat(frames, ignore_index=True)

        # Extração vetorizada do primeiro referenced tweet de cada linha.
        # Retweets têm uma única referência, de tipo "retweeted".
        ext = raw["referenced_tweets"].str.extract(
            r"<ReferencedTweet id=(?P<rid>\d+) type=(?P<rtype>\w+)"
        )
        mask = ext["rtype"] == "retweeted"

        df = pd.DataFrame(
            {
                "author_id": raw.loc[mask, "author_id"].astype("string").values,
                "referenced_tweet_id": ext.loc[mask, "rid"].astype("string").values,
                "created_at": pd.to_datetime(
                    raw.loc[mask, "Created_at_convert"], utc=True
                ).values,
            }
        )
        return df.reset_index(drop=True)

    def save(self, df: pd.DataFrame, out_dir) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "retweets.parquet"
        df.to_parquet(path, index=False)
        return path

    # --- hooks de cache (Stage) ---
    def _compute(self) -> pd.DataFrame:
        return self.load()

    def _save(self, df: pd.DataFrame, out_dir) -> None:
        self.save(df, out_dir)

    def _load(self, out_dir) -> pd.DataFrame:
        return pd.read_parquet(Path(out_dir) / "retweets.parquet")
