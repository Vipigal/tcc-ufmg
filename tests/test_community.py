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


def test_community_save(tmp_path):
    cr = CommunityDetector(resolution=1.0).detect(_two_cliques())
    cr.save(tmp_path)
    assert (tmp_path / "community_graph.graphml").exists()
    m = pd.read_parquet(tmp_path / "membership.parquet")
    assert set(m.columns) == {"user_id", "community"}
    assert len(m) == 6
