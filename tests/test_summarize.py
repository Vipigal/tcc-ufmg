import json

import pandas as pd
import pytest

from modules.database import Database
from modules.summarize import (ClusterSummarizer, RunnerError, build_input,
                               extract_citations, render_prompt)

TEMPLATE = ("{{evento_nome}} {{evento_data}} c{{cluster_id}} {{n_usuarios}} {{frac_usuarios}}\n"
            "{{tabela_contas}}\n{{n_indisponiveis}}/{{n_selecionados}}\n"
            "A:\n{{bloco_amplificados}}\nB:\n{{bloco_caracteristicos}}\n")

STATS = {"0": {"n_nodes": 300, "frac_nodes": 0.25, "baseline_share": 0.5}}


def _tweet(tid, author, text):
    return {"id": tid, "author_id": author, "text": text, "lang": "pt"}


def _db(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.upsert_events([{"slug": "ev", "name": "Evento X", "event_date": "2023-01-08",
                       "notes": None}])
    db.replace_event_top_tweets("ev", pd.DataFrame(
        [(0, 1, "101", 40, 50, 60, 100), (0, 2, "102", 30, 30, 31, 100),
         (0, 3, "103", 20, 20, 20, 100),                       # 103 não devolvido pela API
         (1, 1, "901", 9, 9, 9, 100)],                          # outro cluster
        columns=["community", "rank", "tweet_id", "rt_cluster", "rt_graph", "rt_event", "k"]))
    db.replace_event_tail_tweets("ev", pd.DataFrame(
        [(0, 1, "201", 12, 12, 12, 2.0, 50)],
        columns=["community", "rank", "tweet_id", "rt_cluster", "rt_graph", "rt_event",
                 "lift", "m"]))
    db.upsert_tweets([_tweet("101", "u1", "primeiro\ntexto"), _tweet("102", "u2", "segundo"),
                      _tweet("201", "u1", "cauda"), _tweet("901", "u9", "alheio")])
    db.upsert_users([{"id": "u1", "username": "ana", "name": "Ana", "description": "dep. federal",
                      "verified": True}])                       # u2 sem perfil hidratado
    db.upsert_lookup_errors("tweet", [{"resource_id": "103", "title": "Not Found Error"}])
    return db


def test_build_input_splits_blocks_and_counts_unavailable(tmp_path):
    inp = build_input(_db(tmp_path), "ev", 0, STATS["0"])
    assert inp["evento_nome"] == "Evento X" and inp["n_usuarios"] == 300
    assert [t["tweet_id"] for t in inp["amplificados"]] == ["101", "102"]
    assert [t["tweet_id"] for t in inp["caracteristicos"]] == ["201"]
    assert inp["n_selecionados"] == 4 and inp["n_indisponiveis"] == 1
    assert set(inp["corpus_ids"]) == {"101", "102", "201"}


def test_lift_of_top_k_tweets_uses_cluster_baseline(tmp_path):
    inp = build_input(_db(tmp_path), "ev", 0, STATS["0"])
    t101 = inp["amplificados"][0]
    assert abs(t101["lift"] - (40 / 50) / 0.5) < 1e-9
    assert inp["caracteristicos"][0]["lift"] == 2.0


def test_top_accounts_sum_rt_cluster_by_author_across_blocks(tmp_path):
    inp = build_input(_db(tmp_path), "ev", 0, STATS["0"])
    acc = inp["top_accounts"]
    assert [a["author_id"] for a in acc] == ["u1", "u2"]
    assert acc[0]["rt_cluster"] == 52 and acc[0]["n_tweets"] == 2      # 40 + 12
    assert acc[0]["username"] == "ana" and acc[0]["verified"] is True
    assert acc[1]["username"] is None                                  # perfil faltante fica faltante


def test_render_fills_every_placeholder(tmp_path):
    inp = build_input(_db(tmp_path), "ev", 0, STATS["0"])
    text = render_prompt(TEMPLATE, inp)
    assert "{{" not in text
    assert "[101] @ana (RTs na comunidade: 40; lift 1,60) — primeiro texto" in text
    assert "@ana | Ana | dep. federal | sim | 52" in text
    assert "25,0%" in text and "1/4" in text


def test_render_rejects_unknown_placeholder(tmp_path):
    inp = build_input(_db(tmp_path), "ev", 0, STATS["0"])
    with pytest.raises(KeyError):
        render_prompt(TEMPLATE + "{{inexistente}}", inp)


def test_extract_citations_reads_all_fields_and_grouped_ids():
    out = {"sintese": "a [101] b [102, 201] c [101]", "contas_prevalentes": "x [999]",
           "inclinacao_politica": {"texto": "y [102; 103]", "confianca": "alta"},
           "limites": "sem citação"}
    assert extract_citations(out) == ["101", "102", "103", "201", "999"]


class FakeRunner:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.prompts = []

    def __call__(self, prompt, schema):
        self.prompts.append(prompt)
        o = self.outputs.pop(0)
        if isinstance(o, Exception):
            raise o
        return {"output": o, "raw": json.dumps({"structured_output": o})}


GOOD = {"sintese": "fala de X [101] e Y [201]", "contas_prevalentes": "políticos [101]",
        "inclinacao_politica": {"texto": "indeterminada [102]", "confianca": "baixa"},
        "limites": "pouco material"}


def _summarizer(db, runner, **kw):
    return ClusterSummarizer(db, runner, template=TEMPLATE, model="m", prompt_version="v1", **kw)


def _row(db):
    return db.conn.execute("SELECT * FROM cluster_summaries WHERE community = 0").fetchone()


def test_summarize_stores_output_and_citation_check(tmp_path):
    db = _db(tmp_path)
    bad = dict(GOOD, limites="ver [555]")
    _summarizer(db, FakeRunner([bad])).summarize("ev", {"0": STATS["0"]})
    r = _row(db)
    assert r["status"] == "ok"
    assert json.loads(r["output_json"]) == bad
    assert json.loads(r["cited_ids_json"]) == ["101", "102", "201", "555"]
    assert json.loads(r["invalid_ids_json"]) == ["555"]
    assert len(r["prompt_sha256"]) == 64


def test_summarize_retries_once_then_records_error(tmp_path):
    db = _db(tmp_path)
    runner = FakeRunner([RunnerError("falhou 1"), RunnerError("falhou 2")])
    rep = _summarizer(db, runner).summarize("ev", {"0": STATS["0"]})
    assert len(runner.prompts) == 2
    assert _row(db)["status"] == "error" and "falhou 2" in _row(db)["raw_response"]
    assert rep[0]["status"] == "error"


def test_summarize_rejects_output_outside_schema(tmp_path):
    db = _db(tmp_path)
    broken = dict(GOOD, inclinacao_politica={"texto": "x", "confianca": "certeza"})
    _summarizer(db, FakeRunner([broken, GOOD])).summarize("ev", {"0": STATS["0"]})
    assert _row(db)["status"] == "ok" and json.loads(_row(db)["output_json"]) == GOOD


def test_summarize_skips_pairs_already_ok_unless_redo(tmp_path):
    db = _db(tmp_path)
    _summarizer(db, FakeRunner([GOOD])).summarize("ev", {"0": STATS["0"]})
    runner = FakeRunner([GOOD])
    rep = _summarizer(db, runner).summarize("ev", {"0": STATS["0"]})
    assert runner.prompts == [] and rep[0]["status"] == "cached"
    _summarizer(db, runner, redo=True).summarize("ev", {"0": STATS["0"]})
    assert len(runner.prompts) == 1
