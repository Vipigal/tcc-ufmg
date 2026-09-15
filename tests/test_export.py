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
    assert slots[(0, "t1")]["also_in"] == [{"community": 1, "group": 2, "rank": 1}]
    assert slots[(1, "t1")]["also_in"] == [{"community": 0, "group": 1, "rank": 1}]


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
