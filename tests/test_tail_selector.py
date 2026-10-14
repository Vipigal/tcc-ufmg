import json

import numpy as np
import pandas as pd

from modules.select_tweets import TailSelector


def _nodes():
    """c0 = {A1, A2, A3} · c1 = {B1, B2} · c2 = {C1} (sem top-K → fora da cauda)."""
    return pd.DataFrame({
        "user_id": ["A1", "A2", "A3", "B1", "B2", "C1"],
        "community": np.array([0, 0, 0, 1, 1, 2], dtype=np.int32),
    })


def _retweets():
    """Pares distintos no grafo: A1{t1,t2,t3} A2{t1,t2,t4} A3{t4} B1{t4,t8} B2{t8}.

    RT_graph = 10 · RT_c0 = 7 · RT_c1 = 3 (C1 não retuitou nada).
    lift(t, c) = (rt_c / rt_graph) / (RT_c / RT_graph):
      t1, t2, t3 em c0 → 1 / 0,7 = 10/7 · t4 em c0 → (2/3) / 0,7 ≈ 0,952
      t4 em c1 → (1/3) / 0,3 ≈ 1,111   · t8 em c1 → 1 / 0,3 ≈ 3,333
    """
    rows = [
        ("A1", "t1"), ("A1", "t2"), ("A1", "t3"),
        ("A2", "t1"), ("A2", "t2"), ("A2", "t2"),   # repetido: conta 1
        ("A2", "t4"), ("A3", "t4"),
        ("B1", "t4"), ("B1", "t8"), ("B2", "t8"),
        ("X1", "t4"),                                # fora do grafo: só rt_event
    ]
    df = pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"])
    return df.astype({"author_id": "string", "referenced_tweet_id": "string"})


def _top():
    return pd.DataFrame({"community": [0, 1], "tweet_id": ["t1", "t8"]})


def _sel(**kw):
    params = dict(m=2, min_rt=1)
    params.update(kw)
    return TailSelector(**params)


def test_lift_is_cluster_share_over_cluster_baseline():
    out = _sel(m=10).select(_nodes(), _retweets(), _top()).set_index(["community", "tweet_id"])
    assert abs(out.loc[(0, "t2"), "lift"] - 10 / 7) < 1e-9
    assert (0, "t4") not in out.index                       # lift (2/3)/0,7 < 1: fora
    assert abs(out.loc[(1, "t4"), "lift"] - (1 / 3) / 0.3) < 1e-9


def test_top_k_tweets_are_excluded_from_their_own_cluster_tail():
    out = _sel(m=10).select(_nodes(), _retweets(), _top())
    assert "t1" not in set(out[out["community"] == 0]["tweet_id"])
    assert "t8" not in set(out[out["community"] == 1]["tweet_id"])


def test_ranking_by_lift_then_rt_cluster_then_id_and_cut_at_m():
    out = _sel(m=2).select(_nodes(), _retweets(), _top())
    c0 = out[out["community"] == 0].sort_values("rank")
    assert list(c0["tweet_id"]) == ["t2", "t3"]       # empate de lift → rt_cluster 2 > 1
    assert list(c0["rank"]) == [1, 2]
    assert list(c0["m"]) == [2, 2]


def test_min_rt_floor_drops_low_volume_candidates():
    out = _sel(m=10, min_rt=2).select(_nodes(), _retweets(), _top())
    assert list(out[out["community"] == 0].sort_values("rank")["tweet_id"]) == ["t2"]  # t4: lift < 1
    assert out[out["community"] == 1].empty


def test_only_clusters_present_in_top_k_get_a_tail():
    out = _sel(m=10).select(_nodes(), _retweets(), _top())
    assert set(out["community"]) <= {0, 1}


def test_counts_are_reported():
    out = _sel(m=10).select(_nodes(), _retweets(), _top()).set_index(["community", "tweet_id"])
    row = out.loc[(1, "t4")]
    assert row["rt_cluster"] == 1 and row["rt_graph"] == 3 and row["rt_event"] == 4


def test_run_persists_and_reloads_with_stats(tmp_path):
    sel = _sel()
    out1 = sel.run(_nodes(), _retweets(), _top(), out_dir=tmp_path)
    stats = json.loads((tmp_path / "tail_tweets_stats.json").read_text())
    assert stats["params"] == {"m": 2, "min_rt": 1}
    assert stats["clusters"]["0"]["n_selected"] == 2
    assert stats["clusters"]["0"]["n_candidates"] == 2       # t2, t3 (t4 tem lift < 1)
    out2 = _sel().run(None, None, None, out_dir=tmp_path)
    pd.testing.assert_frame_equal(out1.reset_index(drop=True), out2.reset_index(drop=True))


def test_under_represented_tweets_never_enter_the_tail():
    out = _sel(m=10).select(_nodes(), _retweets(), _top())
    assert (out["lift"] > 1).all()
    assert "t4" not in set(out[out["community"] == 0]["tweet_id"])   # lift ≈ 0,952 em c0
