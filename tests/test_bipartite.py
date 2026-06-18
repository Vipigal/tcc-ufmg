import scipy.sparse as sp
import pandas as pd
from modules.bipartite import BipartiteBuilder


def test_build_binary_matrix():
    df = pd.DataFrame(
        [("U1", "T1"), ("U1", "T2"), ("U2", "T1"), ("U2", "T1")],
        columns=["author_id", "referenced_tweet_id"],
    )
    bg = BipartiteBuilder().build(df)
    assert bg.B.shape == (2, 2)
    assert bg.B.nnz == 3
    assert bg.B.max() == 1
    assert set(bg.user_index) == {"U1", "U2"}
    assert set(bg.tweet_index) == {"T1", "T2"}


def test_build_matrix_alignment():
    df = pd.DataFrame(
        [("U1", "T1"), ("U1", "T2"), ("U2", "T1")],
        columns=["author_id", "referenced_tweet_id"],
    )
    bg = BipartiteBuilder().build(df)
    u = list(bg.user_index).index("U1")
    t = list(bg.tweet_index).index("T2")
    assert bg.B[u, t] == 1
    u2 = list(bg.user_index).index("U2")
    assert bg.B[u2, t] == 0


def test_bipartite_save(tmp_path):
    df = pd.DataFrame([("U1", "T1")], columns=["author_id", "referenced_tweet_id"])
    bg = BipartiteBuilder().build(df)
    bg.save(tmp_path)
    assert (tmp_path / "bipartite_B.npz").exists()
    B2 = sp.load_npz(tmp_path / "bipartite_B.npz")
    assert B2.shape == bg.B.shape
    idx = pd.read_parquet(tmp_path / "bipartite_user_index.parquet")
    assert list(idx["user_id"]) == ["U1"]
