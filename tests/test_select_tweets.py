import json

import numpy as np
import pandas as pd

from modules.select_tweets import TopTweetSelector, load_final_graph


def _graph():
    """6 nós em 3 comunidades. Posição da linha = índice usado em `edges`.

    c0 = {A1, A2, A3} (50% dos nós) · c1 = {B1, B2} (33%) · c2 = {C1} (17%, pequena)
    Peso: intra-c0 = 3,0 · intra-c1 = 0,1 · inter c0–c1 = 0,5 → total 3,6.
    c1 fica com 0,1/3,6 ≈ 2,8% do peso total (≤ 5% → K pequeno).
    """
    nodes = pd.DataFrame({
        "user_id": ["A1", "A2", "A3", "B1", "B2", "C1"],
        "community": np.array([0, 0, 0, 1, 1, 2], dtype=np.int32),
    })
    edges = pd.DataFrame({
        "src": np.array([0, 0, 1, 3, 2], dtype=np.int32),
        "dst": np.array([1, 2, 2, 4, 3], dtype=np.int32),
        "weight": np.array([1.0, 1.0, 1.0, 0.1, 0.5], dtype=np.float32),
    })
    return nodes, edges


def _retweets():
    rows = [
        ("A1", "t1"), ("A1", "t2"), ("A1", "t3"),
        ("A2", "t1"), ("A2", "t1"),            # retweet repetido: conta 1
        ("A2", "t2"),
        ("A3", "t1"),
        ("B1", "t9"), ("B1", "t8"),
        ("B2", "t9"), ("B2", "t8"),            # empate t8 × t9 dentro de c1
        ("C1", "t5"),
        ("X1", "t1"), ("X1", "t7"), ("X1", "t7"),  # X1 não é nó do grafo
    ]
    df = pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"])
    return df.astype({"author_id": "string", "referenced_tweet_id": "string"})


def _selector(**kw):
    params = dict(k=2, k_small=1, min_frac=0.2, small_weight_frac=0.05)
    params.update(kw)
    return TopTweetSelector(**params)


def test_small_clusters_below_min_frac_are_excluded():
    nodes, edges = _graph()
    out = _selector().select(nodes, edges, _retweets())
    assert set(out["community"]) == {0, 1}          # c2 (1/6 dos nós) fica fora


def test_ranking_counts_only_cluster_members_and_cuts_at_k():
    nodes, edges = _graph()
    out = _selector().select(nodes, edges, _retweets())
    c0 = out[out["community"] == 0].sort_values("rank")
    assert list(c0["tweet_id"]) == ["t1", "t2"]     # t3 (1 retweet) cai no corte K=2
    assert list(c0["rank"]) == [1, 2]
    assert list(c0["rt_cluster"]) == [3, 2]         # A2 retuitou t1 duas vezes: conta 1
    assert list(c0["k"]) == [2, 2]


def test_graph_and_event_counts_are_reported():
    nodes, edges = _graph()
    out = _selector().select(nodes, edges, _retweets()).set_index(["community", "tweet_id"])
    row = out.loc[(0, "t1")]
    assert row["rt_cluster"] == 3      # A1, A2, A3
    assert row["rt_graph"] == 3        # nenhum nó de outro cluster retuitou t1
    assert row["rt_event"] == 4        # + X1 (periferia fora do grafo)


def test_low_weight_cluster_gets_k_small_and_tie_breaks_by_id():
    nodes, edges = _graph()
    out = _selector().select(nodes, edges, _retweets())
    c1 = out[out["community"] == 1]
    assert len(c1) == 1                              # K pequeno = 1
    assert c1.iloc[0]["k"] == 1
    assert c1.iloc[0]["tweet_id"] == "t8"            # empate 2×2 → id menor primeiro


def test_weight_rule_uses_total_graph_weight_as_denominator():
    nodes, edges = _graph()
    sel = _selector()
    sel.select(nodes, edges, _retweets())
    c1 = sel.stats["clusters"]["1"]
    assert abs(c1["intra_weight_frac"] - 0.1 / 3.6) < 1e-6
    assert c1["k"] == 1
    assert sel.stats["clusters"]["0"]["k"] == 2


def test_stats_summarize_slots_and_unique_ids():
    nodes, edges = _graph()
    sel = _selector()
    sel.select(nodes, edges, _retweets())
    s = sel.stats
    assert s["n_slots"] == 3               # 2 (c0) + 1 (c1)
    assert s["n_unique_ids"] == 3
    assert s["n_overlap"] == 0
    assert s["n_excluded_clusters"] == 1
    assert s["clusters"]["0"]["n_nodes"] == 3
    assert abs(s["clusters"]["0"]["frac_nodes"] - 0.5) < 1e-9


def test_tweet_ids_are_strings():
    nodes, edges = _graph()
    out = _selector().select(nodes, edges, _retweets())
    assert all(isinstance(t, str) for t in out["tweet_id"])


def test_run_persists_and_reloads_with_stats(tmp_path):
    nodes, edges = _graph()
    sel = _selector()
    out1 = sel.run(nodes, edges, _retweets(), out_dir=tmp_path)
    assert (tmp_path / "top_tweets.parquet").exists()
    stats = json.loads((tmp_path / "top_tweets_stats.json").read_text())
    assert stats["n_slots"] == 3

    sel2 = _selector()
    out2 = sel2.run(None, None, None, out_dir=tmp_path)   # cache hit: não recomputa
    pd.testing.assert_frame_equal(out1.reset_index(drop=True), out2.reset_index(drop=True))
    assert sel2.stats == sel.stats


def test_load_final_graph_reads_the_two_parquets(tmp_path):
    nodes, edges = _graph()
    nodes.to_parquet(tmp_path / "graph_nodes.parquet", index=False)
    edges.to_parquet(tmp_path / "graph_edges.parquet", index=False)
    n2, e2 = load_final_graph(tmp_path)
    assert list(n2.columns) == ["user_id", "community"]
    assert list(e2.columns) == ["src", "dst", "weight"]
    assert len(n2) == 6 and len(e2) == 5
