import json

import numpy as np
import pandas as pd

from modules.overlap import ContentOverlap


def _nodes():
    return pd.DataFrame({"user_id": ["A1", "A2", "B1", "C1"],
                         "community": np.array([0, 0, 1, 2], dtype=np.int32)})


def _retweets():
    """t1: A1, A2, B1 (pureza c0 = 2/3) · t2: A1 (c0 = 1) · t3: B1, C1 · t1 repetido por A1."""
    rows = [("A1", "t1"), ("A1", "t1"), ("A2", "t1"), ("B1", "t1"), ("A1", "t2"),
            ("B1", "t3"), ("C1", "t3"), ("X9", "t1")]
    return pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"]).astype("string")


def test_shared_with_is_retweet_weighted_share_of_other_cluster():
    out = ContentOverlap(clusters=[0, 1, 2]).compute(_nodes(), _retweets())
    c0 = out["clusters"]["0"]
    # RTs de c0: t1 ×2 (A1, A2) e t2 ×1 → Σ = 3. Em t1, c1 tem 1/3 dos RTs do grafo.
    assert abs(c0["shared_with"]["1"] - (2 * (1 / 3)) / 3) < 1e-12
    assert c0["shared_with"]["2"] == 0.0
    assert abs(c0["shared"] - 2 / 9) < 1e-12


def test_shared_is_one_minus_weighted_mean_purity_and_asymmetric():
    out = ContentOverlap(clusters=[0, 1, 2]).compute(_nodes(), _retweets())
    c1 = out["clusters"]["1"]
    # RTs de c1: t1 (c0 = 2/3) e t3 (c2 = 1/2) → shared_with c0 = (2/3)/2, c2 = (1/2)/2
    assert abs(c1["shared_with"]["0"] - 1 / 3) < 1e-12
    assert abs(c1["shared_with"]["2"] - 1 / 4) < 1e-12
    assert abs(c1["shared"] - 7 / 12) < 1e-12
    assert c1["shared_with"]["0"] != out["clusters"]["0"]["shared_with"]["1"]


def test_only_requested_clusters_are_reported_but_all_count_as_others():
    out = ContentOverlap(clusters=[0, 1]).compute(_nodes(), _retweets())
    assert set(out["clusters"]) == {"0", "1"}
    assert set(out["clusters"]["1"]["shared_with"]) == {"0", "2"}


def test_run_persists_json(tmp_path):
    out = ContentOverlap(clusters=[0, 1]).run(_nodes(), _retweets(), out_dir=tmp_path)
    assert json.loads((tmp_path / "content_overlap.json").read_text()) == out
