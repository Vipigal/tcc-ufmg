import numpy as np
import scipy.sparse as sp
from modules.bipartite import BipartiteGraph
from modules.project import JaccardProjector


def _bg(B, users=None):
    B = sp.csr_matrix(np.array(B, dtype=np.int8))
    n, m = B.shape
    users = users or ["U%d" % i for i in range(n)]
    return BipartiteGraph(
        B=B,
        user_index=np.array(users),
        tweet_index=np.array(["T%d" % j for j in range(m)]),
    )


def _edges_by_user(pg):
    """Arestas de um ProjectedGraph como {(user_a, user_b): peso}."""
    W = pg.W.tocoo()
    return {
        tuple(sorted((str(pg.user_index[r]), str(pg.user_index[c])))): round(float(v), 9)
        for r, c, v in zip(W.row, W.col, W.data)
    }


def _brute(bg, tau):
    """Referência força-bruta: todos os pares i<j com J >= tau."""
    Bd = bg.B.toarray().astype(bool)
    n = Bd.shape[0]
    out = {}
    for i in range(n):
        for j in range(i + 1, n):
            inter = int((Bd[i] & Bd[j]).sum())
            union = int((Bd[i] | Bd[j]).sum())
            if inter > 0 and inter / union >= tau:   # aresta só se compartilham ≥1 tweet
                key = tuple(sorted((str(bg.user_index[i]), str(bg.user_index[j]))))
                out[key] = round(inter / union, 9)
    return out


_SIMPLE = [
    [1, 1, 0],
    [1, 1, 0],
    [0, 1, 1],
]

_DROP = [
    [1, 1, 1, 0, 0],
    [1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1],
    [0, 0, 0, 1, 0],
]


def test_jaccard_weights():
    e = _edges_by_user(JaccardProjector(tau=0.0).project(_bg(_SIMPLE)))
    assert e[("U0", "U1")] == 1.0                  # idênticos
    assert e[("U0", "U2")] == round(1 / 3, 9)
    assert e[("U1", "U2")] == round(1 / 3, 9)


def test_projection_is_upper_triangular_no_diag():
    W = JaccardProjector(tau=0.0).project(_bg(_SIMPLE)).W.tocoo()
    assert all(r < c for r, c in zip(W.row, W.col))


def test_blocked_matches_bruteforce():
    rng = np.random.default_rng(0)
    B = (rng.random((12, 8)) < 0.4).astype(np.int8)
    B[B.sum(1) == 0, 0] = 1                          # ninguém com grau 0
    bg = _bg(B.tolist())
    for tau in (0.0, 0.1, 0.3):
        pg = JaccardProjector(tau=tau, block_size=3).project(bg)
        assert _edges_by_user(pg) == _brute(bg, tau)


def test_block_size_invariant():
    rng = np.random.default_rng(1)
    B = (rng.random((10, 6)) < 0.5).astype(np.int8)
    B[B.sum(1) == 0, 0] = 1
    bg = _bg(B.tolist())
    small = _edges_by_user(JaccardProjector(tau=0.1, block_size=1).project(bg))
    big = _edges_by_user(JaccardProjector(tau=0.1, block_size=100).project(bg))
    assert small == big


def test_threshold_drops_isolated_and_reindexes():
    pg = JaccardProjector(tau=0.9).project(_bg(_DROP))
    # sobra só a aresta U0-U1 (J=1); U2,U3 ficam isolados e saem
    assert set(str(u) for u in pg.user_index) == {"U0", "U1"}
    assert pg.W.nnz == 1


def test_stats():
    pj = JaccardProjector(tau=0.9)
    pj.project(_bg(_DROP))
    assert pj.stats["before"] == {"nodes": 4, "edges": 1}
    assert pj.stats["after"] == {"nodes": 2, "edges": 1}


def test_save_uses_backbone_prefix(tmp_path):
    JaccardProjector(tau=0.0).project(_bg(_SIMPLE)).save(tmp_path)
    assert (tmp_path / "backbone_W.npz").exists()
    assert (tmp_path / "backbone_user_index.parquet").exists()
