import sqlite3

import pandas as pd

from modules.database import Database


def _tweet(tid, author="u1"):
    return {"id": tid, "author_id": author, "text": f"texto {tid}",
            "created_at": "2023-01-08T12:00:00.000Z", "lang": "pt",
            "public_metrics": {"retweet_count": 10, "like_count": 3}}


def _user(uid):
    return {"id": uid, "username": f"user{uid}", "name": "Nome", "protected": False,
            "verified": True, "public_metrics": {"followers_count": 42}}


def _cols(conn, table):
    return {r[1]: r for r in conn.execute(f"PRAGMA table_info({table})")}


def test_schema_is_created_and_idempotent(tmp_path):
    path = tmp_path / "db.sqlite"
    Database(path).close()
    db = Database(path)                       # segunda abertura não falha nem duplica
    tables = {r[0] for r in db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"events", "users", "tweets", "author_classification",
            "event_top_tweets", "community_membership"} <= tables
    db.close()


def test_event_top_tweets_is_keyed_by_event_community_tweet(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    cols = _cols(db.conn, "event_top_tweets")
    pk = {name for name, r in cols.items() if r[5] > 0}
    assert pk == {"event_slug", "community", "tweet_id"}
    assert {"rank", "rt_cluster", "rt_graph", "rt_event", "k", "selected_at"} <= set(cols)
    assert "selection_group" not in cols
    db.close()


def test_upsert_tweets_keeps_explicit_hydrated_at(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    when = "2026-05-09T03:57:00+00:00"
    n = db.upsert_tweets([_tweet("1"), _tweet("2")], hydrated_at=when)
    assert n == 2
    assert db.cached_tweet_ids() == {"1", "2"}
    got = {r[0]: r[1] for r in db.conn.execute("SELECT tweet_id, hydrated_at FROM tweets")}
    assert got == {"1": when, "2": when}
    # flatten das colunas de ergonomia
    row = db.conn.execute("SELECT retweet_count, like_count, author_id FROM tweets "
                          "WHERE tweet_id='1'").fetchone()
    assert tuple(row) == (10, 3, "u1")
    db.close()


def test_upsert_users_defaults_hydrated_at_to_now(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.upsert_users([_user("9")])
    row = db.conn.execute("SELECT username, verified, followers_count, hydrated_at "
                          "FROM users WHERE user_id='9'").fetchone()
    assert row[0] == "user9" and row[1] == 1 and row[2] == 42
    assert row[3] is not None
    assert db.cached_user_ids() == {"9"}
    db.close()


def _selection(rows):
    return pd.DataFrame(rows, columns=["community", "rank", "tweet_id",
                                       "rt_cluster", "rt_graph", "rt_event", "k"])


def test_replace_event_top_tweets_replaces_the_event_selection(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.replace_event_top_tweets("ev-a", _selection([(0, 1, "t1", 5, 6, 9, 100),
                                                    (0, 2, "t2", 4, 4, 4, 100),
                                                    (1, 1, "t1", 3, 6, 9, 20)]))
    db.replace_event_top_tweets("ev-b", _selection([(0, 1, "t7", 2, 2, 2, 100)]))
    assert db.conn.execute("SELECT COUNT(*) FROM event_top_tweets").fetchone()[0] == 4

    # re-seleção menor para ev-a: linhas antigas do evento somem, ev-b fica intacto
    n = db.replace_event_top_tweets("ev-a", _selection([(0, 1, "t1", 5, 6, 9, 100)]))
    assert n == 1
    rows = db.conn.execute("SELECT event_slug, community, tweet_id FROM event_top_tweets "
                           "ORDER BY 1, 2, 3").fetchall()
    assert [tuple(r) for r in rows] == [("ev-a", 0, "t1"), ("ev-b", 0, "t7")]
    db.close()


def test_replace_event_top_tweets_stores_selected_at(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.replace_event_top_tweets("ev", _selection([(0, 1, "t1", 1, 1, 1, 100)]),
                                selected_at="2026-09-15T12:00:00+00:00")
    row = db.conn.execute("SELECT selected_at, rt_cluster, k FROM event_top_tweets").fetchone()
    assert tuple(row) == ("2026-09-15T12:00:00+00:00", 1, 100)
    db.close()


def test_table_counts(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.upsert_tweets([_tweet("1")])
    counts = db.table_counts()
    assert counts["tweets"] == 1 and counts["users"] == 0
    db.close()


def _old_shape_db(path):
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE event_top_tweets (
        event_slug TEXT, tweet_id TEXT, retweet_count_dataset INTEGER, rank INTEGER,
        selection_group TEXT CHECK (selection_group IN ('originais','gerais')),
        PRIMARY KEY (event_slug, tweet_id))""")
    con.commit()
    return con


def test_old_empty_event_top_tweets_is_recreated_in_new_shape(tmp_path):
    path = tmp_path / "db.sqlite"
    _old_shape_db(path).close()
    db = Database(path)
    cols = set(_cols(db.conn, "event_top_tweets"))
    assert "community" in cols and "selection_group" not in cols
    db.close()


def test_old_event_top_tweets_with_data_is_not_touched(tmp_path):
    import pytest
    path = tmp_path / "db.sqlite"
    con = _old_shape_db(path)
    con.execute("INSERT INTO event_top_tweets VALUES ('ev','t1',5,1,'gerais')")
    con.commit(); con.close()
    with pytest.raises(RuntimeError):
        Database(path)


def _err(rid, title="Not Found Error"):
    return {"resource_id": rid, "value": rid, "title": title, "detail": f"{title}: {rid}",
            "type": "https://api.twitter.com/2/problems/resource-not-found"}


def test_lookup_errors_upsert_and_clear(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    n = db.upsert_lookup_errors("tweet", [_err("t1"), _err("t2", "Authorization Error")],
                                attempted_at="2026-09-15T12:00:00+00:00")
    assert n == 2
    assert db.errored_ids("tweet") == {"t1", "t2"}
    assert db.errored_ids("user") == set()
    row = db.conn.execute("SELECT title, detail, type, attempted_at, raw_json FROM lookup_errors "
                          "WHERE resource_type='tweet' AND resource_id='t2'").fetchone()
    assert row[0] == "Authorization Error" and row[3] == "2026-09-15T12:00:00+00:00"
    assert '"resource_id": "t2"' in row[4]
    # nova tentativa do mesmo id sobrescreve (última tentativa vale)
    db.upsert_lookup_errors("tweet", [_err("t1", "Authorization Error")])
    assert db.conn.execute("SELECT COUNT(*) FROM lookup_errors").fetchone()[0] == 2
    assert db.clear_lookup_errors("tweet", ["t1", "nao-existe"]) == 1
    assert db.errored_ids("tweet") == {"t2"}
    db.close()


def test_lookup_errors_resource_type_is_checked(tmp_path):
    import pytest
    db = Database(tmp_path / "db.sqlite")
    with pytest.raises(sqlite3.IntegrityError):
        db.upsert_lookup_errors("post", [_err("x")])
    db.close()


def test_pending_tweet_ids_excludes_cached_and_errored(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.replace_event_top_tweets("ev", _selection([(0, 1, "t3", 1, 1, 1, 100),
                                                  (0, 2, "t1", 1, 1, 1, 100),
                                                  (1, 1, "t2", 1, 1, 1, 20),
                                                  (1, 2, "t1", 1, 1, 1, 20)]))
    db.upsert_tweets([_tweet("t1")])
    db.upsert_lookup_errors("tweet", [_err("t2")])
    assert db.selected_tweet_ids() == {"t1", "t2", "t3"}
    assert db.pending_tweet_ids() == ["t3"]
    assert db.pending_tweet_ids(retry_errors=True) == ["t2", "t3"]   # ordenado, sem repetição
    db.close()


def test_pending_author_ids_come_from_cached_tweets(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.upsert_tweets([_tweet("1", "a2"), _tweet("2", "a2"), _tweet("3", "a1"),
                      {"id": "4", "author_id": None}])
    db.upsert_users([_user("a1")])
    db.upsert_lookup_errors("user", [_err("a3")])      # erro de outro id não interfere
    assert db.pending_author_ids() == ["a2"]
    db.upsert_lookup_errors("user", [_err("a2")])
    assert db.pending_author_ids() == []
    assert db.pending_author_ids(retry_errors=True) == ["a2"]
    db.close()


def _tail(rows):
    return pd.DataFrame(rows, columns=["community", "rank", "tweet_id", "rt_cluster",
                                       "rt_graph", "rt_event", "lift", "m"])


def test_replace_event_tail_tweets_replaces_the_event_tail(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.replace_event_tail_tweets("ev", _tail([(0, 1, "t5", 12, 12, 13, 2.5, 50),
                                              (1, 1, "t6", 10, 20, 25, 1.4, 50)]),
                                 selected_at="2026-10-13T00:00:00+00:00")
    n = db.replace_event_tail_tweets("ev", _tail([(0, 1, "t5", 12, 12, 13, 2.5, 50)]))
    assert n == 1
    rows = db.conn.execute("SELECT tweet_id, lift FROM event_tail_tweets").fetchall()
    assert [tuple(r) for r in rows] == [("t5", 2.5)]
    db.close()


def test_selected_tweet_ids_is_union_of_top_and_tail(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.replace_event_top_tweets("ev", _selection([(0, 1, "t1", 1, 1, 1, 100)]))
    db.replace_event_tail_tweets("ev", _tail([(0, 1, "t5", 12, 12, 13, 2.5, 50),
                                              (1, 1, "t1", 10, 20, 25, 1.4, 50)]))
    assert db.selected_tweet_ids() == {"t1", "t5"}
    assert db.pending_tweet_ids() == ["t1", "t5"]
    db.close()


def _summary(**kw):
    row = {"event_slug": "ev", "community": 0, "model": "claude-sonnet-5-5",
           "prompt_version": "v1", "status": "ok", "output_json": '{"sintese": "x"}',
           "raw_response": "{}", "prompt_sha256": "abc", "input_json": "{}",
           "cited_ids_json": "[]", "invalid_ids_json": "[]",
           "generated_at": "2026-10-13T00:00:00+00:00"}
    row.update(kw)
    return row


def test_cluster_summaries_upsert_by_event_cluster_model_prompt(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.upsert_cluster_summary(_summary(status="error"))
    db.upsert_cluster_summary(_summary(status="ok"))
    db.upsert_cluster_summary(_summary(prompt_version="v2"))
    rows = db.conn.execute("SELECT prompt_version, status FROM cluster_summaries "
                           "ORDER BY prompt_version").fetchall()
    assert [tuple(r) for r in rows] == [("v1", "ok"), ("v2", "ok")]
    db.close()


def test_cluster_summaries_status_is_checked(tmp_path):
    import pytest
    db = Database(tmp_path / "db.sqlite")
    with pytest.raises(sqlite3.IntegrityError):
        db.upsert_cluster_summary(_summary(status="talvez"))
    db.close()


def _tweet_with_media(tid, keys):
    t = _tweet(tid)
    t["entities"] = {"urls": [{"url": f"https://t.co/{k}", "media_key": k} for k in keys]
                     + [{"url": "https://t.co/link", "expanded_url": "https://ex.com"}]}
    return t


def test_pending_media_tweet_ids_are_cached_tweets_with_media_keys(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    db.upsert_tweets([_tweet_with_media("t1", ["3_1"]), _tweet("t2"),
                      _tweet_with_media("t3", ["7_2"]), _tweet_with_media("t4", ["3_4"])])
    db.replace_tweet_media("t3", ["7_2"])
    db.upsert_lookup_errors("tweet", [{"resource_id": "t4", "title": "Not Found Error"}])
    assert db.pending_media_tweet_ids() == ["t1"]
    assert db.pending_media_tweet_ids(retry_errors=True) == ["t1", "t4"]
    db.close()


def test_media_and_tweet_media_are_stored(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    n = db.upsert_media([{"media_key": "3_1", "type": "photo", "url": "https://pbs/a.jpg",
                          "width": 10, "height": 20, "alt_text": "alt"},
                         {"media_key": "7_2", "type": "video", "preview_image_url": "https://pbs/v.jpg"}])
    assert n == 2
    db.replace_tweet_media("t1", ["7_2", "3_1"])
    db.replace_tweet_media("t1", ["7_2", "3_1"])                  # idempotente
    rows = db.conn.execute("SELECT media_key, position FROM tweet_media WHERE tweet_id='t1' "
                           "ORDER BY position").fetchall()
    assert [tuple(r) for r in rows] == [("7_2", 0), ("3_1", 1)]
    m = db.conn.execute("SELECT type, url, preview_image_url, raw_json FROM media "
                        "WHERE media_key='7_2'").fetchone()
    assert m["type"] == "video" and m["url"] is None and m["preview_image_url"] == "https://pbs/v.jpg"
    assert '"media_key": "7_2"' in m["raw_json"]
    db.close()
