import json

import numpy as np
import pandas as pd
import pytest

from modules.database import Database
from modules.export import WebExporter, write_index
from modules.layout import CommunityLayout, PALETTE
from modules.select_tweets import TopTweetSelector


# ---- fixture: um "evento" processado mínimo + banco com hidratação parcial ----
def _graph():
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
    rows = [("A1", "t1"), ("A1", "t2"), ("A1", "t3"), ("A2", "t1"), ("A2", "t2"), ("A3", "t1"),
            ("B1", "t9"), ("B1", "t8"), ("B2", "t9"), ("B2", "t8"), ("B1", "t1"),
            ("C1", "t5"), ("X1", "t1"), ("X1", "t7")]
    return pd.DataFrame(rows, columns=["author_id", "referenced_tweet_id"]).astype("string")


def _tweet(tid, author, text="olá #tag @alguem https://t.co/x", metrics=None):
    return {"id": tid, "author_id": author, "text": text, "created_at": "2023-01-08T12:00:00.000Z",
            "lang": "pt", "possibly_sensitive": False, "reply_settings": "everyone",
            "conversation_id": tid,
            "public_metrics": metrics or {"retweet_count": 100, "reply_count": 1, "like_count": 2,
                                          "quote_count": 3, "bookmark_count": 4, "impression_count": 5},
            "entities": {"hashtags": [{"start": 4, "end": 8, "tag": "tag"}],
                         "mentions": [{"start": 9, "end": 16, "username": "alguem", "id": "77"}],
                         "urls": [{"start": 17, "end": 40, "url": "https://t.co/x",
                                   "expanded_url": "https://ex.com/p", "display_url": "ex.com/p"}]},
            "edit_history_tweet_ids": [tid]}


def _user(uid, username):
    return {"id": uid, "username": username, "name": f"Nome {username}", "description": "bio",
            "location": "BR", "url": None, "profile_image_url": "https://pbs/img.jpg",
            "protected": False, "verified": True, "verified_type": "blue",
            "created_at": "2010-01-01T00:00:00.000Z",
            "public_metrics": {"followers_count": 10, "following_count": 5, "tweet_count": 3,
                               "listed_count": 1, "like_count": 0, "media_count": 0}}


@pytest.fixture
def processed(tmp_path):
    """data/processed/<ev>/ sintético: grafo final, run_config, seleção (M8) e layout DRL (M7)."""
    d = tmp_path / "processed" / "ev"
    d.mkdir(parents=True)
    nodes, edges = _graph()
    nodes.to_parquet(d / "graph_nodes.parquet", index=False)
    edges.to_parquet(d / "graph_edges.parquet", index=False)
    (d / "run_config.json").write_text(json.dumps({"evento": "ev", "min_user_retweets": 3, "tau": 0.1}))
    sel = TopTweetSelector(k=2, k_small=1, min_frac=0.2, small_weight_frac=0.05)
    selection = sel.run(nodes, edges, _retweets(), out_dir=d)
    layout = CommunityLayout(coords=np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.0], [10.0, 10.0], [12.0, 10.0]]),
                             community=np.array([0, 0, 0, 1, 1]),
                             sizes=pd.Series(nodes["community"]).value_counts(), n_nodes=6, top_k=12, seed=42)
    layout.save(d)
    return d, selection


@pytest.fixture
def db(tmp_path, processed):
    d, selection = processed
    db = Database(tmp_path / "db.sqlite")
    db.upsert_events([{"slug": "ev", "name": "Evento Teste", "event_date": "2023-01-08", "notes": ""}])
    db.replace_event_top_tweets("ev", selection)
    # c0 selecionou t1, t2 (k=2); c1 selecionou t8 (k=1). t1 hidratado com autor; t2 removido; t8 hidratado sem autor.
    db.upsert_tweets([_tweet("t1", "u1"), _tweet("t8", "u2")])
    db.upsert_users([_user("u1", "fulano")])
    db.upsert_lookup_errors("tweet", [{"resource_id": "t2", "title": "Not Found Error", "detail": "gone"}])
    db.upsert_lookup_errors("user", [{"resource_id": "u2", "title": "Authorization Error", "detail": "suspended"}])
    yield db
    db.close()


def _export(db, processed, tmp_path):
    d, _ = processed
    out = tmp_path / "export" / "ev"
    result = WebExporter(db).run(d, out_dir=out)
    return out, result


def test_export_writes_three_files(db, processed, tmp_path):
    out, _ = _export(db, processed, tmp_path)
    assert {p.name for p in out.iterdir()} == {"event.json", "tweets.json", "layout.json"}


def test_event_meta_has_clusters_with_group_numbering_and_hydration(db, processed, tmp_path):
    out, _ = _export(db, processed, tmp_path)
    ev = json.loads((out / "event.json").read_text())
    assert ev["slug"] == "ev" and ev["name"] == "Evento Teste" and ev["event_date"] == "2023-01-08"
    assert ev["n_nodes"] == 6 and ev["n_edges"] == 5 and ev["n_communities"] == 3
    assert ev["run_config"]["min_user_retweets"] == 3
    assert ev["selection"] == {"k": 2, "k_small": 1, "min_frac": 0.2, "small_weight_frac": 0.05}
    clusters = {c["community"]: c for c in ev["clusters"]}
    assert set(clusters) == {0, 1}                       # c2 (< min_frac) não é cluster selecionado
    c0, c1 = clusters[0], clusters[1]
    assert (c0["group"], c0["label"], c0["color"]) == (1, "Grupo 1", PALETTE[0])
    assert (c1["group"], c1["label"], c1["color"]) == (2, "Grupo 2", PALETTE[1])
    assert c0["n_nodes"] == 3 and abs(c0["frac_nodes"] - 0.5) < 1e-9 and c0["k"] == 2
    assert (c0["n_selected"], c0["n_hydrated"], c0["n_not_found"], c0["n_not_authorized"],
            c0["n_pending"]) == (2, 1, 1, 0, 0)
    assert abs(c0["attrition"] - 0.5) < 1e-9
    assert (c1["n_selected"], c1["n_hydrated"], c1["attrition"]) == (1, 1, 0.0)
    assert ev["files"] == {"tweets": "ev/tweets.json", "layout": "ev/layout.json"}


def test_tweets_json_slots_statuses_and_metadata(db, processed, tmp_path):
    out, _ = _export(db, processed, tmp_path)
    slots = json.loads((out / "tweets.json").read_text())
    assert [(s["community"], s["rank"], s["tweet_id"]) for s in slots] == [(0, 1, "t1"), (0, 2, "t2"), (1, 1, "t8")]
    t1, t2, t8 = slots

    # hidratado com autor
    assert t1["status"] == "hydrated" and t1["error"] is None
    assert t1["group"] == 1 and t1["k"] == 2
    assert (t1["rt_cluster"], t1["rt_graph"], t1["rt_event"]) == (3, 4, 5)   # B1 e X1 também retuitaram t1
    assert abs(t1["purity"] - 3 / 4) < 1e-9
    assert t1["tweet"]["text"].startswith("olá") and t1["tweet"]["metrics"]["retweet_count"] == 100
    assert t1["tweet"]["entities"]["hashtags"][0]["tag"] == "tag"
    assert t1["tweet"]["entities"]["urls"][0]["expanded_url"] == "https://ex.com/p"
    assert t1["tweet"]["url"] == "https://x.com/i/web/status/t1"
    assert t1["author"]["username"] == "fulano" and t1["author"]["metrics"]["followers_count"] == 10
    assert t1["author_status"] == "hydrated"
    assert t1["also_in"] == []

    # não devolvido pela API
    assert t2["status"] == "not_found" and t2["error"]["title"] == "Not Found Error"
    assert t2["tweet"] is None and t2["author"] is None and t2["author_status"] is None

    # hidratado, autor negado pela API
    assert t8["status"] == "hydrated" and t8["author"] is None and t8["author_status"] == "not_authorized"
    assert t8["author_id"] == "u2"


def test_also_in_lists_other_clusters_of_same_event(db, processed, tmp_path):
    # força t1 a aparecer também em c1 (rank 1) para testar a sobreposição
    sel = pd.DataFrame([(0, 1, "t1", 3, 4, 5, 2), (0, 2, "t2", 2, 2, 2, 2), (1, 1, "t1", 1, 4, 5, 1)],
                       columns=["community", "rank", "tweet_id", "rt_cluster", "rt_graph", "rt_event", "k"])
    db.replace_event_top_tweets("ev", sel)
    out, _ = _export(db, processed, tmp_path)
    slots = {(s["community"], s["tweet_id"]): s for s in json.loads((out / "tweets.json").read_text())}
    assert slots[(0, "t1")]["also_in"] == [{"community": 1, "group": 2, "rank": 1,
                                            "origin": "amplified"}]
    assert slots[(1, "t1")]["also_in"] == [{"community": 0, "group": 1, "rank": 1,
                                            "origin": "amplified"}]


def test_layout_json_has_coords_communities_and_centroids(db, processed, tmp_path):
    out, _ = _export(db, processed, tmp_path)
    lay = json.loads((out / "layout.json").read_text())
    assert lay["n_nodes"] == 6 and lay["n_plotted"] == 5 and lay["top_k"] == 12 and lay["seed"] == 42
    assert lay["x"] == [0.0, 1.0, 2.0, 10.0, 12.0] and lay["y"] == [0.0, 1.0, 0.0, 10.0, 10.0]
    assert lay["community"] == [0, 0, 0, 1, 1]
    assert lay["centroids"]["0"] == [1.0, 0.0] and lay["centroids"]["1"] == [11.0, 10.0]   # mediana
    assert lay["groups"]["0"] == 1 and lay["groups"]["1"] == 2 and lay["groups"]["2"] == 3


def test_export_is_deterministic_and_rerunnable(db, processed, tmp_path):
    out, _ = _export(db, processed, tmp_path)
    first = {p.name: p.read_text() for p in out.iterdir()}
    out2, _ = _export(db, processed, tmp_path)
    assert {p.name: p.read_text() for p in out2.iterdir()} == first


def test_write_index_collects_events_and_palette(db, processed, tmp_path):
    out, _ = _export(db, processed, tmp_path)
    idx_path = write_index(tmp_path / "export", ["ev"])
    idx = json.loads(idx_path.read_text())
    assert idx_path.name == "index.json"
    assert idx["palette"] == PALETTE and "generated_at" in idx
    assert [e["slug"] for e in idx["events"]] == ["ev"]
    assert idx["events"][0]["clusters"][0]["label"] == "Grupo 1"


# ---- cauda (M8b) e síntese (M11) ----
def _with_tail(db):
    tail = pd.DataFrame([(1, 1, "t1", 1, 4, 5, 1.25, 50)],
                        columns=["community", "rank", "tweet_id", "rt_cluster", "rt_graph",
                                 "rt_event", "lift", "m"])
    db.replace_event_tail_tweets("ev", tail)


def test_slots_carry_origin_and_tail_slots_carry_lift(db, processed, tmp_path):
    _with_tail(db)
    out, _ = _export(db, processed, tmp_path)
    slots = json.loads((out / "tweets.json").read_text())
    key = {(s["community"], s["origin"], s["tweet_id"]): s for s in slots}
    amp = key[(0, "amplified", "t1")]
    tail = key[(1, "characteristic", "t1")]
    assert amp["lift"] is None and amp["k"] == 2
    assert tail["lift"] == 1.25 and tail["rank"] == 1 and tail["k"] == 50
    assert tail["status"] == "hydrated" and tail["author"]["username"] == "fulano"
    assert {"community": 1, "group": 2, "rank": 1, "origin": "characteristic"} in amp["also_in"]
    # ordem: por cluster; dentro do cluster, amplificados antes dos característicos
    assert [(s["community"], s["origin"]) for s in slots] == [
        (0, "amplified"), (0, "amplified"), (1, "amplified"), (1, "characteristic")]


def test_clusters_carry_top_accounts_and_tail_counts(db, processed, tmp_path):
    _with_tail(db)
    out, _ = _export(db, processed, tmp_path)
    c = {c["community"]: c for c in json.loads((out / "event.json").read_text())["clusters"]}
    assert c[0]["top_accounts"][0]["username"] == "fulano"
    assert c[0]["top_accounts"][0]["rt_cluster"] == 3
    assert (c[1]["n_tail_selected"], c[1]["n_tail_hydrated"]) == (1, 1)
    assert c[0]["summary"] is None


def test_cluster_summary_is_the_latest_ok_row(db, processed, tmp_path):
    base = {"event_slug": "ev", "community": 0, "model": "claude-sonnet-5-5",
            "raw_response": "{}", "prompt_sha256": "x", "input_json": "{}",
            "cited_ids_json": '["t1"]', "invalid_ids_json": '["t9"]'}
    out_v1 = {"sintese": "s1 [t1]", "contas_prevalentes": "c", "limites": "l",
              "inclinacao_politica": {"texto": "i", "confianca": "media"}}
    db.upsert_cluster_summary(dict(base, prompt_version="v1", status="ok",
                                   output_json=json.dumps(out_v1),
                                   generated_at="2026-10-13T10:00:00+00:00"))
    db.upsert_cluster_summary(dict(base, prompt_version="v2", status="error", output_json=None,
                                   generated_at="2026-10-13T11:00:00+00:00"))
    out, _ = _export(db, processed, tmp_path)
    c0 = json.loads((out / "event.json").read_text())["clusters"][0]
    s = c0["summary"]
    assert s["sintese"] == "s1 [t1]" and s["inclinacao_politica"]["confianca"] == "media"
    assert (s["model"], s["prompt_version"]) == ("claude-sonnet-5-5", "v1")
    assert s["invalid_ids"] == ["t9"]


# ---- curadoria, conteúdo compartilhado e mídias (spec 2026-10-14) ----
def _summary_row(db, sintese, version="v1", when="2026-10-13T10:00:00+00:00"):
    out = {"sintese": sintese, "contas_prevalentes": "c", "limites": "l",
           "inclinacao_politica": {"texto": "i", "confianca": "media"}}
    db.upsert_cluster_summary({"event_slug": "ev", "community": 0, "model": "m",
                               "prompt_version": version, "status": "ok",
                               "output_json": json.dumps(out), "raw_response": "{}",
                               "prompt_sha256": "x", "input_json": "{}", "cited_ids_json": "[]",
                               "invalid_ids_json": "[]", "generated_at": when})


def _curation(tmp_path, trecho, eixo="esquerda", version="v1"):
    p = tmp_path / "clusters.json"
    p.write_text(json.dumps({"clusters": [{"event": "ev", "community": 0,
                                           "summary": {"model": "m", "prompt_version": version},
                                           "trecho": trecho, "eixo": eixo}]}))
    return p


def _export_with(db, processed, tmp_path, curation):
    d, _ = processed
    return WebExporter(db, curation_path=curation).run(d, out_dir=tmp_path / "export" / "ev")


def test_curated_excerpt_must_be_literal_fragments_of_the_synthesis(db, processed, tmp_path):
    _summary_row(db, "Primeira frase [123]. Segunda frase com [4, 5] citações. Terceira.")
    res = _export_with(db, processed, tmp_path,
                       _curation(tmp_path, ["Primeira frase.", "Segunda frase com citações."]))
    c0 = {c["community"]: c for c in res["event"]["clusters"]}[0]
    assert c0["curation"] == {"trecho": ["Primeira frase.", "Segunda frase com citações."],
                              "eixo": "esquerda", "stale": False}
    assert {c["community"]: c for c in res["event"]["clusters"]}[1]["curation"] is None
    with pytest.raises(ValueError, match="não é literal"):
        _export_with(db, processed, tmp_path, _curation(tmp_path, ["Frase inventada."]))


def test_curation_is_stale_when_a_newer_synthesis_exists(db, processed, tmp_path):
    _summary_row(db, "Texto antigo.")
    _summary_row(db, "Texto novo.", version="v2", when="2026-10-14T10:00:00+00:00")
    res = _export_with(db, processed, tmp_path, _curation(tmp_path, ["Texto antigo."]))
    assert res["event"]["clusters"][0]["curation"]["stale"] is True


def test_curation_rejects_unknown_axis(db, processed, tmp_path):
    _summary_row(db, "Texto.")
    with pytest.raises(ValueError, match="eixo"):
        _export_with(db, processed, tmp_path, _curation(tmp_path, ["Texto."], eixo="centro"))


def test_clusters_carry_content_overlap_when_computed(db, processed, tmp_path):
    d, _ = processed
    (d / "content_overlap.json").write_text(json.dumps({"clusters": {
        "0": {"n_retweets": 5, "shared": 0.25, "shared_with": {"1": 0.2, "2": 0.05}},
        "1": {"n_retweets": 4, "shared": 0.5, "shared_with": {"0": 0.5, "2": 0.0}}}}))
    out, _ = _export(db, processed, tmp_path)
    c = {c["community"]: c for c in json.loads((out / "event.json").read_text())["clusters"]}
    assert c[0]["shared"] == 0.25 and c[0]["shared_with"] == {"1": 0.2, "2": 0.05}


def test_tweet_view_carries_media_in_order(db, processed, tmp_path):
    db.upsert_media([{"media_key": "3_1", "type": "photo", "url": "https://pbs/a.jpg",
                      "width": 4, "height": 3},
                     {"media_key": "7_2", "type": "video", "preview_image_url": "https://pbs/v.jpg"}])
    db.replace_tweet_media("t1", ["7_2", "3_1", "16_9"])          # 16_9 não veio: fica de fora
    out, _ = _export(db, processed, tmp_path)
    t1 = next(s for s in json.loads((out / "tweets.json").read_text()) if s["tweet_id"] == "t1")
    assert [m["type"] for m in t1["tweet"]["media"]] == ["video", "photo"]
    assert t1["tweet"]["media"][1] == {"media_key": "3_1", "type": "photo", "url": "https://pbs/a.jpg",
                                       "preview_image_url": None, "width": 4, "height": 3,
                                       "alt_text": None}
    t8 = next(s for s in json.loads((out / "tweets.json").read_text()) if s["tweet_id"] == "t8")
    assert t8["tweet"]["media"] == []
