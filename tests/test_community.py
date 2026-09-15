import numpy as np
import pandas as pd
import scipy.sparse as sp
from modules.project import ProjectedGraph
from modules.community import CommunityDetector


def _two_cliques():
    # {0,1,2} clique e {3,4,5} clique, sem pontes
    edges = [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)]
    rows = [e[0] for e in edges]
    cols = [e[1] for e in edges]
    data = [1.0] * len(edges)
    W = sp.coo_matrix((data, (rows, cols)), shape=(6, 6)).tocsr()
    return ProjectedGraph(W=W, user_index=np.array(["U%d" % i for i in range(6)]))


def test_detects_two_communities():
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    assert len(set(cr.membership)) == 2
    assert cr.membership[0] == cr.membership[1] == cr.membership[2]
    assert cr.membership[3] == cr.membership[4] == cr.membership[5]
    assert cr.membership[0] != cr.membership[3]


def test_partition_modularity_positive():
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    assert cr.partition.modularity > 0
    assert cr.g.vcount() == 6


def test_community_save_two_parquets(tmp_path):
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    cr.save(tmp_path)
    assert not (tmp_path / "community_graph.graphml").exists()   # graphml descontinuado
    nodes = pd.read_parquet(tmp_path / "graph_nodes.parquet")
    edges = pd.read_parquet(tmp_path / "graph_edges.parquet")
    assert set(nodes.columns) == {"user_id", "community"}
    assert set(edges.columns) == {"src", "dst", "weight"}
    assert len(nodes) == 6
    assert len(edges) == 6


def test_community_roundtrip(tmp_path):
    det = CommunityDetector(resolution=1.0)
    cr1 = det.run(_two_cliques(), out_dir=tmp_path)        # compute + save
    cr2 = det.run(_two_cliques(), out_dir=tmp_path)        # cache hit -> _load
    assert cr2.W.nnz == cr1.W.nnz
    assert list(map(str, cr2.user_index)) == list(map(str, cr1.user_index))
    assert len(set(cr2.membership)) == 2
    assert cr2.partition.modularity > 0


def test_community_result_load_without_graph(tmp_path):
    """Fase 2 precisa de W + membership sem pagar a construção do igraph (M7 usa só isso)."""
    import numpy as np
    import pandas as pd
    from modules.community import CommunityResult
    pd.DataFrame({"user_id": ["u0", "u1", "u2"], "community": np.array([0, 0, 1], dtype=np.int32)}
                 ).to_parquet(tmp_path / "graph_nodes.parquet", index=False)
    pd.DataFrame({"src": np.array([0, 1], dtype=np.int32), "dst": np.array([1, 2], dtype=np.int32),
                  "weight": np.array([0.5, 0.2], dtype=np.float32)}
                 ).to_parquet(tmp_path / "graph_edges.parquet", index=False)
    cr = CommunityResult.load(tmp_path, build_graph=False)
    assert cr.g is None and cr.partition is None
    assert cr.membership == [0, 0, 1]
    assert list(cr.user_index) == ["u0", "u1", "u2"]
    assert cr.W.shape == (3, 3) and cr.W.nnz == 2
    full = CommunityResult.load(tmp_path)                     # padrão: com igraph
    assert full.g.vcount() == 3 and full.g.ecount() == 2
