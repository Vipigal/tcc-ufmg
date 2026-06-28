"""Camada de dados do projeto — cache de hidratação em SQLite (standalone).

NÃO estende `Stage` (não é um estágio de pipeline). Encapsula a conexão com o
banco (`data/database/hydrated.sqlite`), garante o schema de forma idempotente e
oferece *upserts* que nunca perdem dados (`INSERT ... ON CONFLICT DO UPDATE`) e
checagens de cache para a hidratação ("já tenho esse tweet/usuário?").

Esta classe é a fonte de verdade do schema em código; a documentação humana das
tabelas/colunas (e o changelog) vive em `data/database/README.md`.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = "data/database/hydrated.sqlite"

# DDL idempotente — espelha data/database/README.md. Sem FKs (referências
# lógicas); dado faltante reflete a realidade (ver README, princípio 4).
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
  slug TEXT PRIMARY KEY, name TEXT, event_date TEXT, notes TEXT
);

CREATE TABLE IF NOT EXISTS users (
  user_id            TEXT PRIMARY KEY,
  username TEXT, name TEXT, description TEXT, location TEXT, url TEXT,
  profile_image_url TEXT,
  protected INTEGER, verified INTEGER, verified_type TEXT,
  account_created_at TEXT,
  followers_count INTEGER, following_count INTEGER, tweet_count INTEGER,
  listed_count INTEGER, like_count INTEGER, media_count INTEGER,
  raw_json TEXT, hydrated_at TEXT
);

CREATE TABLE IF NOT EXISTS tweets (
  tweet_id            TEXT PRIMARY KEY,
  author_id TEXT, text TEXT, created_at TEXT, lang TEXT, conversation_id TEXT,
  source TEXT, in_reply_to_user_id TEXT,
  possibly_sensitive INTEGER, reply_settings TEXT, geo_place_id TEXT,
  retweet_count INTEGER, reply_count INTEGER, like_count INTEGER,
  quote_count INTEGER, bookmark_count INTEGER, impression_count INTEGER,
  raw_json TEXT, hydrated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_tweets_author ON tweets(author_id);

CREATE TABLE IF NOT EXISTS author_classification (
  author_id      TEXT PRIMARY KEY,
  classification TEXT CHECK (classification IN ('left','right','media','neutral','unknown')),
  confidence     TEXT CHECK (confidence IN ('high','medium','low')),
  justification  TEXT, classified_by TEXT, llm_model TEXT,
  classified_at  TEXT, notes TEXT
);

CREATE TABLE IF NOT EXISTS event_top_tweets (
  event_slug TEXT, tweet_id TEXT,
  retweet_count_dataset INTEGER, rank INTEGER,
  selection_group TEXT CHECK (selection_group IN ('originais','gerais')),
  PRIMARY KEY (event_slug, tweet_id)
);

CREATE TABLE IF NOT EXISTS community_membership (
  event_slug TEXT, user_id TEXT,
  community INTEGER, ideological_score REAL, weighted_degree REAL,
  tau REAL DEFAULT 0.1,
  PRIMARY KEY (event_slug, user_id, tau)
);
"""


def _as_int_bool(v):
    """API booleans (true/false) -> 0/1; preserva None."""
    return None if v is None else int(bool(v))


def _str_or_none(v):
    return None if v is None else str(v)


class Database:
    """Conexão e operações sobre `hydrated.sqlite`."""

    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ── construção de linhas (objeto da API -> dict de colunas) ──────────
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _user_row(o: dict) -> dict:
        m = o.get("public_metrics") or {}
        return {
            "user_id": str(o["id"]),
            "username": o.get("username"),
            "name": o.get("name"),
            "description": o.get("description"),
            "location": o.get("location"),
            "url": o.get("url"),
            "profile_image_url": o.get("profile_image_url"),
            "protected": _as_int_bool(o.get("protected")),
            "verified": _as_int_bool(o.get("verified")),
            "verified_type": o.get("verified_type"),
            "account_created_at": o.get("created_at"),
            "followers_count": m.get("followers_count"),
            "following_count": m.get("following_count"),
            "tweet_count": m.get("tweet_count"),
            "listed_count": m.get("listed_count"),
            "like_count": m.get("like_count"),
            "media_count": m.get("media_count"),
            "raw_json": json.dumps(o, ensure_ascii=False),
            "hydrated_at": Database._now(),
        }

    @staticmethod
    def _tweet_row(o: dict) -> dict:
        m = o.get("public_metrics") or {}
        geo = o.get("geo") or {}
        return {
            "tweet_id": str(o["id"]),
            "author_id": _str_or_none(o.get("author_id")),
            "text": o.get("text"),
            "created_at": o.get("created_at"),
            "lang": o.get("lang"),
            "conversation_id": _str_or_none(o.get("conversation_id")),
            "source": o.get("source"),
            "in_reply_to_user_id": _str_or_none(o.get("in_reply_to_user_id")),
            "possibly_sensitive": _as_int_bool(o.get("possibly_sensitive")),
            "reply_settings": o.get("reply_settings"),
            "geo_place_id": geo.get("place_id"),
            "retweet_count": m.get("retweet_count"),
            "reply_count": m.get("reply_count"),
            "like_count": m.get("like_count"),
            "quote_count": m.get("quote_count"),
            "bookmark_count": m.get("bookmark_count"),
            "impression_count": m.get("impression_count"),
            "raw_json": json.dumps(o, ensure_ascii=False),
            "hydrated_at": Database._now(),
        }

    # ── upsert genérico ──────────────────────────────────────────────────
    def _upsert(self, table: str, pk_cols: list[str], rows: list[dict]) -> int:
        if not rows:
            return 0
        cols = list(rows[0].keys())
        placeholders = ",".join("?" * len(cols))
        non_pk = [c for c in cols if c not in pk_cols]
        conflict = ",".join(pk_cols)
        action = (f"DO UPDATE SET {','.join(f'{c}=excluded.{c}' for c in non_pk)}"
                  if non_pk else "DO NOTHING")
        sql = (f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders}) "
               f"ON CONFLICT({conflict}) {action}")
        self.conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
        self.conn.commit()
        return len(rows)

    def upsert_users(self, user_objs: list[dict]) -> int:
        return self._upsert("users", ["user_id"], [self._user_row(o) for o in user_objs])

    def upsert_tweets(self, tweet_objs: list[dict]) -> int:
        return self._upsert("tweets", ["tweet_id"], [self._tweet_row(o) for o in tweet_objs])

    def upsert_events(self, rows: list[dict]) -> int:
        return self._upsert("events", ["slug"], rows)

    def upsert_event_top_tweets(self, rows: list[dict]) -> int:
        return self._upsert("event_top_tweets", ["event_slug", "tweet_id"], rows)

    def upsert_author_classifications(self, rows: list[dict]) -> int:
        return self._upsert("author_classification", ["author_id"], rows)

    def upsert_community_membership(self, rows: list[dict]) -> int:
        return self._upsert("community_membership", ["event_slug", "user_id", "tau"], rows)

    # ── checagens de cache ────────────────────────────────────────────────
    def cached_user_ids(self) -> set[str]:
        return {r[0] for r in self.conn.execute("SELECT user_id FROM users")}

    def cached_tweet_ids(self) -> set[str]:
        return {r[0] for r in self.conn.execute("SELECT tweet_id FROM tweets")}
