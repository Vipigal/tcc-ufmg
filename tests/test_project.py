import numpy as np
import scipy.sparse as sp
from modules.bipartite import BipartiteGraph
from modules.project import JaccardProjector


def _bg():
    # U1:{T1,T2}, U2:{T1,T2}, U3:{T2,T3}
    B = sp.csr_matrix(np.array([
        [1, 1, 0],
        [1, 1, 0],
        [0, 1, 1],
    ], dtype=np.int8))
    return BipartiteGraph(
        B=B,
        user_index=np.array(["U1", "U2", "U3"]),
        tweet_index=np.array(["T1", "T2", "T3"]),
    )


def test_jaccard_weights():
    pg = JaccardProjector().project(_bg())
    W = pg.W.toarray()
    assert W[0, 1] == 1.0                 # U1,U2 idênticos
    assert abs(W[0, 2] - 1 / 3) < 1e-9    # U1,U3 -> 1/3
    assert abs(W[1, 2] - 1 / 3) < 1e-9


def test_projection_is_upper_triangular():
    pg = JaccardProjector().project(_bg())
    W = pg.W.toarray()
    assert W[1, 0] == 0.0                 # nada no triângulo inferior
    assert W[0, 0] == 0.0                 # sem diagonal
    assert list(pg.user_index) == ["U1", "U2", "U3"]


def test_projection_save(tmp_path):
    pg = JaccardProjector().project(_bg())
    pg.save(tmp_path)
    assert (tmp_path / "projection_W.npz").exists()
    assert (tmp_path / "projection_user_index.parquet").exists()
