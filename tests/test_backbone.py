import json
import numpy as np
import scipy.sparse as sp
from modules.project import ProjectedGraph
from modules.backbone import BackboneExtractor


def _pg():
    # arestas: (0,1)=0.5 e (2,3)=0.05  -> tau=0.1 mantém só (0,1)
    W = sp.csr_matrix(np.array([
        [0.0, 0.5, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.05],
        [0.0, 0.0, 0.0, 0.0],
    ]))
    return ProjectedGraph(W=W, user_index=np.array(["U0", "U1", "U2", "U3"]))


def test_backbone_thresholds_and_drops_isolates():
    bb = BackboneExtractor(tau=0.1)
    pg2 = bb.extract(_pg())
    assert pg2.W.shape == (2, 2)             # U2,U3 viraram isolados e saíram
    assert list(pg2.user_index) == ["U0", "U1"]
    assert pg2.W.toarray()[0, 1] == 0.5


def test_backbone_stats():
    bb = BackboneExtractor(tau=0.1)
    bb.extract(_pg())
    assert bb.stats["before"] == {"nodes": 4, "edges": 2}
    assert bb.stats["after"] == {"nodes": 2, "edges": 1}


def test_backbone_save_stats(tmp_path):
    bb = BackboneExtractor(tau=0.1)
    bb.extract(_pg())
    bb.save_stats(tmp_path)
    s = json.loads((tmp_path / "backbone_stats.json").read_text())
    assert s["after"]["nodes"] == 2
