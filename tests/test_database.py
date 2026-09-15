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
