import time

import pytest

import modules.fetch_x_data as fx
from modules.fetch_x_data import XClient, BATCH_SIZE


class _Resp:
    def __init__(self, status, payload=None, headers=None):
        self.status_code = status
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Session:
    """Sessão falsa: devolve as respostas na ordem e grava as chamadas."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers, "params": params})
        return self._responses.pop(0)


def _client(responses, sleeps=None):
    sess = _Session(responses)
    sleep = (lambda s: sleeps.append(s)) if sleeps is not None else (lambda s: None)
    return XClient(bearer_token="tok", session=sess, sleep=sleep), sess


def test_lookup_tweets_returns_data_and_errors_separately():
    payload = {"data": [{"id": "1", "text": "a"}, {"id": "2", "text": "b"}],
               "errors": [{"resource_id": "3", "title": "Not Found Error",
                           "detail": "Could not find tweet with ids: [3]."}]}
    client, sess = _client([_Resp(200, payload)])
    data, errors = client.lookup_tweets(["1", "2", "3"])
    assert [d["id"] for d in data] == ["1", "2"]
    assert errors[0]["resource_id"] == "3"
    call = sess.calls[0]
    assert call["url"].endswith("/2/tweets")
    assert call["headers"]["Authorization"] == "Bearer tok"
    assert call["params"]["ids"] == "1,2,3"
    assert "public_metrics" in call["params"]["tweet.fields"]
    assert "expansions" not in call["params"]          # sem expansions: custo só por tweet


def test_lookup_users_hits_users_endpoint_with_user_fields():
    client, sess = _client([_Resp(200, {"data": [{"id": "9", "username": "u"}]})])
    data, errors = client.lookup_users(["9"])
    assert data[0]["username"] == "u" and errors == []
    assert sess.calls[0]["url"].endswith("/2/users")
    assert "description" in sess.calls[0]["params"]["user.fields"]


def test_empty_payload_yields_empty_lists():
    client, _ = _client([_Resp(200, {"errors": [{"resource_id": "1", "title": "x"}]})])
    data, errors = client.lookup_tweets(["1"])
    assert data == [] and len(errors) == 1


def test_rate_limit_waits_until_reset_and_retries():
    reset = int(time.time()) + 3
    sleeps = []
    client, sess = _client([_Resp(429, headers={"x-rate-limit-reset": str(reset)}),
                            _Resp(200, {"data": [{"id": "1"}]})], sleeps)
    data, _ = client.lookup_tweets(["1"])
    assert [d["id"] for d in data] == ["1"]
    assert len(sess.calls) == 2
    assert len(sleeps) == 1 and 1 <= sleeps[0] <= 6


def test_http_error_propagates():
    client, _ = _client([_Resp(500)])
    with pytest.raises(RuntimeError):
        client.lookup_tweets(["1"])


def test_batch_size_is_enforced():
    client, _ = _client([])
    with pytest.raises(ValueError):
        client.lookup_tweets([str(i) for i in range(BATCH_SIZE + 1)])


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    monkeypatch.setattr(fx, "load_dotenv", lambda *a, **k: False)
    with pytest.raises(RuntimeError):
        XClient()
