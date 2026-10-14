import pandas as pd
import pytest

from modules.database import Database
from modules.fetch_x_data import COST_PER_TWEET, COST_PER_USER, BATCH_SIZE
from modules.hydrate import TweetHydrator, UserHydrator, hydration_status


class FakeClient:
    """Cliente falso da API: devolve o que estiver em `tweets`/`users`, erros em `errors`.
    IDs desconhecidos simplesmente não voltam (como a API faria sem erro explícito)."""

    def __init__(self, tweets=None, users=None, errors=None):
        self.tweets = tweets or {}
        self.users = users or {}
        self.errors = errors or {}
        self.calls = []

    def _lookup(self, store, ids):
        self.calls.append(list(ids))
        data = [store[i] for i in ids if i in store]
        errors = [self.errors[i] for i in ids if i in self.errors and i not in store]
        return data, errors

    def lookup_tweets(self, ids):
        return self._lookup(self.tweets, ids)

    def lookup_users(self, ids):
        return self._lookup(self.users, ids)


def _tweet(tid, author="a1"):
    return {"id": tid, "author_id": author, "text": f"t{tid}", "public_metrics": {}}


def _err(rid, title="Not Found Error"):
    return {"resource_id": rid, "value": rid, "title": title,
            "detail": f"{title} for {rid}", "type": "https://api.twitter.com/2/problems/x"}


def _selection(rows):
    return pd.DataFrame(rows, columns=["community", "rank", "tweet_id",
                                       "rt_cluster", "rt_graph", "rt_event", "k"])


@pytest.fixture
def db(tmp_path):
    d = Database(tmp_path / "db.sqlite")
    d.replace_event_top_tweets("ev", _selection([(0, 1, "t1", 5, 5, 5, 100),
                                                 (0, 2, "t2", 4, 4, 4, 100),
                                                 (0, 3, "t3", 3, 3, 3, 100),
                                                 (1, 1, "t3", 2, 3, 3, 20),
                                                 (1, 2, "t4", 1, 1, 1, 20)]))
    d.upsert_tweets([_tweet("t1")])                   # t1 já em cache
    yield d
    d.close()


def test_hydrates_only_pending_ids_and_records_errors(db, tmp_path):
    client = FakeClient(tweets={"t2": _tweet("t2"), "t3": _tweet("t3", author="a2")},
                        errors={"t4": _err("t4", "Authorization Error")})
    rep = TweetHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)

    assert client.calls == [["t2", "t3", "t4"]]        # t1 não é pedido de novo
    assert db.cached_tweet_ids() == {"t1", "t2", "t3"}
    assert db.errored_ids("tweet") == {"t4"}
    row = db.conn.execute("SELECT title, detail, attempted_at FROM lookup_errors "
                          "WHERE resource_id='t4'").fetchone()
    assert row[0] == "Authorization Error" and row[2] is not None
    assert (rep.n_pending, rep.n_returned, rep.n_errors) == (3, 2, 1)
    assert rep.errors_by_title == {"Authorization Error": 1}
    assert abs(rep.cost_usd - 2 * COST_PER_TWEET) < 1e-9


def test_second_run_makes_no_api_calls(db, tmp_path):
    client = FakeClient(tweets={"t2": _tweet("t2"), "t3": _tweet("t3")}, errors={"t4": _err("t4")})
    TweetHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)
    client.calls.clear()
    rep = TweetHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)
    assert client.calls == []                          # erro registrado não é re-tentado
    assert rep.n_pending == 0 and rep.cost_usd == 0


def test_retry_errors_requests_errored_ids_and_clears_error_on_success(db, tmp_path):
    client = FakeClient(tweets={"t2": _tweet("t2"), "t3": _tweet("t3")}, errors={"t4": _err("t4")})
    TweetHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)
    client.tweets["t4"] = _tweet("t4")                 # o tweet "voltou"
    client.calls.clear()
    TweetHydrator(db, client, retry_errors=True, sleep=lambda s: None).run(out_dir=tmp_path)
    assert client.calls == [["t4"]]
    assert "t4" in db.cached_tweet_ids()
    assert db.errored_ids("tweet") == set()


def test_batches_respect_batch_size_and_pause(tmp_path):
    db = Database(tmp_path / "db.sqlite")
    ids = [f"t{i:03d}" for i in range(250)]
    db.replace_event_top_tweets("ev", _selection([(0, i + 1, t, 1, 1, 1, 100)
                                                  for i, t in enumerate(ids)]))
    client = FakeClient(tweets={t: _tweet(t) for t in ids})
    sleeps = []
    rep = TweetHydrator(db, client, pause_s=0.5, sleep=sleeps.append).run(out_dir=tmp_path)
    assert [len(c) for c in client.calls] == [BATCH_SIZE, BATCH_SIZE, 50]
    assert sleeps == [0.5, 0.5]                        # pausa só ENTRE lotes
    assert rep.n_returned == 250
    db.close()


def test_user_hydrator_takes_authors_of_cached_tweets(db, tmp_path):
    db.upsert_tweets([_tweet("t2", author="a2"), _tweet("t3", author=None)])
    client = FakeClient(users={"a1": {"id": "a1", "username": "x"}},
                        errors={"a2": _err("a2", "Not Found Error")})
    rep = UserHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)
    assert client.calls == [["a1", "a2"]]              # autor NULL não entra
    assert db.cached_user_ids() == {"a1"}
    assert db.errored_ids("user") == {"a2"}
    assert (rep.resource_type, rep.n_returned, rep.n_errors) == ("user", 1, 1)
    assert abs(rep.cost_usd - COST_PER_USER) < 1e-9


def test_hydration_status_per_cluster(db, tmp_path):
    client = FakeClient(tweets={"t2": _tweet("t2")},
                        errors={"t3": _err("t3", "Not Found Error"),
                                "t4": _err("t4", "Authorization Error")})
    TweetHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)
    st = hydration_status(db).set_index(["evento", "cluster"])
    c0, c1 = st.loc[("ev", 0)], st.loc[("ev", 1)]
    assert (c0["selecionados"], c0["hidratados"], c0["nao_encontrados"],
            c0["nao_autorizados"], c0["pendentes"]) == (3, 2, 1, 0, 0)
    assert (c1["selecionados"], c1["hidratados"], c1["nao_encontrados"],
            c1["nao_autorizados"], c1["pendentes"]) == (2, 0, 1, 1, 0)
    assert abs(c1["atricao"] - 1.0) < 1e-9 and abs(c0["atricao"] - 1 / 3) < 1e-9


def test_report_summary_is_a_readable_line(db, tmp_path):
    client = FakeClient(tweets={"t2": _tweet("t2"), "t3": _tweet("t3")}, errors={"t4": _err("t4")})
    rep = TweetHydrator(db, client, sleep=lambda s: None).run(out_dir=tmp_path)
    s = rep.summary()
    assert "3" in s and "2" in s and "1" in s and "US$" in s


class FakeMediaClient:
    def __init__(self, tweets, media, errors=None):
        self.tweets, self.media, self.errors = tweets, media, errors or {}
        self.calls = []

    def lookup_tweets_media(self, ids):
        self.calls.append(list(ids))
        data = [self.tweets[i] for i in ids if i in self.tweets]
        keys = {k for d in data for k in d.get("attachments", {}).get("media_keys", [])}
        return (data, [self.errors[i] for i in ids if i in self.errors],
                [self.media[k] for k in sorted(keys) if k in self.media])


def _media_tweet(tid, keys):
    return {"id": tid, "author_id": "a1", "text": "x", "public_metrics": {},
            "entities": {"urls": [{"url": "u", "media_key": k} for k in keys]}}


def test_media_hydrator_stores_media_and_mapping_without_touching_tweets(tmp_path):
    from modules.hydrate import MediaHydrator
    db = Database(tmp_path / "db.sqlite")
    db.upsert_tweets([_media_tweet("t1", ["3_1", "3_2"]), _media_tweet("t2", ["7_9"]),
                      _media_tweet("t3", ["3_5"])], hydrated_at="2026-09-15T00:00:00+00:00")
    client = FakeMediaClient(
        tweets={"t1": {"id": "t1", "attachments": {"media_keys": ["3_1", "3_2"]}},
                "t2": {"id": "t2"}},                                  # voltou sem attachments
        media={"3_1": {"media_key": "3_1", "type": "photo", "url": "a"},
               "3_2": {"media_key": "3_2", "type": "photo", "url": "b"}},
        errors={"t3": _err("t3")})
    rep = MediaHydrator(db, client, pause_s=0).run(out_dir=tmp_path)
    assert rep.n_pending == 3 and rep.n_returned == 2 and rep.n_errors == 1 and rep.n_media == 2
    maps = db.conn.execute("SELECT tweet_id, media_key FROM tweet_media ORDER BY 1, 2").fetchall()
    # t2 sem attachments: o mapeamento vem dos media_key das entities (mídia em si falta)
    assert [tuple(r) for r in maps] == [("t1", "3_1"), ("t1", "3_2"), ("t2", "7_9")]
    assert db.conn.execute("SELECT COUNT(*) FROM media").fetchone()[0] == 2
    assert db.conn.execute("SELECT hydrated_at FROM tweets WHERE tweet_id='t1'").fetchone()[0] \
        == "2026-09-15T00:00:00+00:00"                                # snapshot intocado
    assert "t3" in db.errored_ids("tweet")
    assert MediaHydrator(db, client, pause_s=0).run(out_dir=tmp_path).n_pending == 0
    db.close()
