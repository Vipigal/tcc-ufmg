from __future__ import annotations

from pathlib import Path

from modules.load import RetweetLoader
from modules.filter import NoiseFilter
from modules.bipartite import BipartiteBuilder
from modules.project import JaccardProjector
from modules.results import GraphResults
from modules.layout import CommunityMap


INTERMEDIATE_FILES = (
    NoiseFilter.FILES
    + BipartiteBuilder.FILES
    + JaccardProjector.FILES
    + GraphResults.FILES        # graph_metrics.json (dados; as PNGs ficam)
    + CommunityMap.FILES        # drl_layout.parquet + .json (coords; o PNG fica)
)


def cleanup_intermediates(out_dir, dry_run: bool = False) -> list[tuple[str, int]]:
    """Apaga os artefatos intermediários em `out_dir`, mantendo o resultado final.

    Retorna a lista de (arquivo, bytes) removidos. Com `dry_run=True` só lista,
    sem apagar.
    """
    out = Path(out_dir)
    removed: list[tuple[str, int]] = []
    for name in INTERMEDIATE_FILES:
        p = out / name
        if p.exists():
            removed.append((name, p.stat().st_size))
            if not dry_run:
                p.unlink()
    return removed
