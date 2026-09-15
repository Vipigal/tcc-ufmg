"""Cliente da API do X (v2) — lookups em lote de tweets e usuários.

Só HTTP: autenticação (bearer token do `.env`), lotes de até 100 IDs, espera
por rate limit (429) e separação do retorno em `data` (recursos devolvidos) e
`errors` (IDs que a API **não** devolveu, com o motivo — tweet removido, conta
suspensa/protegida, etc.). Quem decide o que buscar e onde guardar é o M9
(`modules/hydrate.py`), que usa o banco (`modules/database.py`) como cache.

Custo (pay-per-use, 2026): cobra-se por recurso **devolvido** — US$ 0,005/tweet
e US$ 0,010/user. Pedir mais ou menos campos não altera o custo; *expansions*
(autor, mídia) trariam recursos extras cobrados, por isso não são pedidas.
"""
from __future__ import annotations

import os
import time

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.x.com/2"
BATCH_SIZE = 100            # limite da API por chamada de lookup

COST_PER_TWEET = 0.005      # USD por tweet devolvido
COST_PER_USER = 0.010       # USD por user devolvido

TWEET_FIELDS = ",".join([
    "author_id", "conversation_id", "created_at",
    "entities",             # hashtags, mentions, urls, annotations — sem expansion
    "geo", "in_reply_to_user_id", "lang", "public_metrics", "possibly_sensitive",
    "referenced_tweets", "reply_settings", "source", "text", "withheld",
])

USER_FIELDS = ",".join([
    "created_at", "description", "entities", "location", "name",
    "profile_image_url", "protected", "public_metrics", "url", "username",
    "verified", "verified_type",
])


class XClient:
    """Lookups em lote em `/2/tweets` e `/2/users`.

    `session` e `sleep` são injetáveis para teste (sessão falsa, sem esperar).
    """

    def __init__(self, bearer_token: str | None = None, session=None, sleep=time.sleep):
        if bearer_token is None:
            load_dotenv()
            bearer_token = os.getenv("X_BEARER_TOKEN")
        if not bearer_token:
            raise RuntimeError("X_BEARER_TOKEN ausente — defina no .env da raiz do projeto")
        self._headers = {"Authorization": f"Bearer {bearer_token}"}
        self._session = session or requests.Session()
        self._sleep = sleep

    def lookup_tweets(self, ids) -> tuple[list[dict], list[dict]]:
        """Até 100 tweets, sem expansions. Retorna (data, errors)."""
        return self._lookup("tweets", {"tweet.fields": TWEET_FIELDS}, ids)

    def lookup_users(self, ids) -> tuple[list[dict], list[dict]]:
        """Até 100 usuários. Retorna (data, errors)."""
        return self._lookup("users", {"user.fields": USER_FIELDS}, ids)

    # --- internos ---
    def _lookup(self, path: str, fields: dict, ids) -> tuple[list[dict], list[dict]]:
        ids = [str(i) for i in ids]
        if len(ids) > BATCH_SIZE:
            raise ValueError(f"lote de {len(ids)} IDs excede o máximo de {BATCH_SIZE}")
        if not ids:
            return [], []
        payload = self._get(path, {"ids": ",".join(ids), **fields})
        return payload.get("data", []), payload.get("errors", [])

    def _get(self, path: str, params: dict) -> dict:
        while True:
            resp = self._session.get(f"{BASE_URL}/{path}", headers=self._headers, params=params)
            if resp.status_code == 429:
                reset = int(resp.headers.get("x-rate-limit-reset", 0))
                wait = max(reset - int(time.time()), 1) + 1
                print(f"  rate limit atingido — aguardando {wait}s")
                self._sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
