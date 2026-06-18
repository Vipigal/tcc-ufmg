import pandas as pd
from modules.filter import NoiseFilter
from modules.bipartite import BipartiteBuilder
from modules.project import JaccardProjector
from modules.backbone import BackboneExtractor
from modules.community import CommunityDetector


def _two_group_retweets():
    rows = []
    for u in ["A1", "A2", "A3"]:
        for t in ["a1", "a2", "a3"]:
            rows.append((u, t))
    for u in ["B1", "B2", "B3"]:
        for t in ["b1", "b2", "b3"]:
            rows.append((u, t))
    return pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"])


def test_pipeline_recovers_two_communities():
    df = _two_group_retweets()

    # filtro frouxo para preservar o sinal sintético
    df_f = NoiseFilter(min_user_retweets=1).apply(df)
    bg = BipartiteBuilder().build(df_f)
    pg = JaccardProjector().project(bg)
    pg_bb = BackboneExtractor(tau=0.1).extract(pg)
    cr = CommunityDetector(resolution=1.0).detect(pg_bb)

    comm = dict(zip(cr.user_index, cr.membership))
    assert len(set(cr.membership)) == 2
    assert comm["A1"] == comm["A2"] == comm["A3"]
    assert comm["B1"] == comm["B2"] == comm["B3"]
    assert comm["A1"] != comm["B1"]
