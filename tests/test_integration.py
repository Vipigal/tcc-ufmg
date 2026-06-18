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


def _run_pipeline(df, out_dir, *, force=False):
    """Roda a pipeline inteira via Stage.run, devolvendo objetos-chave."""
    df_f = NoiseFilter(min_user_retweets=1).run(df, out_dir=out_dir, force=force)
    bg = BipartiteBuilder().run(df_f, out_dir=out_dir, force=force)
    pg = JaccardProjector().run(bg, out_dir=out_dir, force=force)
    bb = BackboneExtractor(tau=0.1)
    pg_bb = bb.run(pg, out_dir=out_dir, force=force)
    cr = CommunityDetector(resolution=1.0).run(pg_bb, out_dir=out_dir, force=force)
    return df_f, pg, bb, cr


def test_pipeline_run_is_idempotent(tmp_path):
    df = _two_group_retweets()

    # 1ª passada (frio): calcula e persiste todos os estágios
    _, pg1, bb1, cr1 = _run_pipeline(df, tmp_path)
    comms1 = dict(zip(cr1.user_index, cr1.membership))

    # 2ª passada: tudo vem do cache (hit). Resultado equivalente.
    _, pg2, bb2, cr2 = _run_pipeline(df, tmp_path)
    comms2 = dict(zip(cr2.user_index, cr2.membership))

    # projeção idêntica byte-a-byte (round-trip save/load)
    assert (pg1.W != pg2.W).nnz == 0
    # stats do backbone repostas na memória pelo _load (ponto 2 do design)
    assert bb2.stats == bb1.stats
    # estrutura de comunidades preservada
    assert comms2["A1"] == comms2["A2"] == comms2["A3"]
    assert comms2["B1"] == comms2["B2"] == comms2["B3"]
    assert comms2["A1"] != comms2["B1"]
