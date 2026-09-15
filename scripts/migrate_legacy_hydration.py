#!/usr/bin/env python
"""Migração ÚNICA da hidratação de maio/2026 (JSON) para o banco `hydrated.sqlite`.

Antes do banco existir, o `fetch_x_data.py` antigo gravou a primeira hidratação em
`data/processed/invasao-3-poderes/` — invasão dos 3 Poderes, top-100 **global**
(critério anterior ao D6 revisado): 100 IDs pedidos, 83 tweets e 72 autores
devolvidos (17% de atrição, ver D6). Esse material é cache pago: entra em
`tweets`/`users` com o `hydrated_at` do snapshot original, não o de hoje.

Idempotente: só grava o que ainda não está no banco. Não é parte da pipeline —
roda uma vez e pronto (`python scripts/migrate_legacy_hydration.py`).

Os 17 IDs não devolvidos em maio NÃO entram em `lookup_errors`: o motivo não foi
registrado à época, e re-pedir um ID não devolvido não custa nada — se estiverem
na seleção atual, o M9 os pede de novo e grava o motivo real.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.database import Database  # noqa: E402

LEGACY_DIR = ROOT / "data" / "processed" / "invasao-3-poderes"
LEGACY_HYDRATED_AT = "2026-05-09T00:57:00-03:00"   # mtime original dos JSON (git não preserva mtime)
DB_PATH = ROOT / "data" / "database" / "hydrated.sqlite"


def _jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    tweets = _jsonl(LEGACY_DIR / "hydrated_tweets.jsonl")
    with open(LEGACY_DIR / "hydrated_users.json", encoding="utf-8") as f:
        users = list(json.load(f).values())

    with Database(DB_PATH) as db:
        before = db.table_counts()
        cached_t, cached_u = db.cached_tweet_ids(), db.cached_user_ids()
        new_t = [t for t in tweets if str(t["id"]) not in cached_t]
        new_u = [u for u in users if str(u["id"]) not in cached_u]
        db.upsert_tweets(new_t, hydrated_at=LEGACY_HYDRATED_AT)
        db.upsert_users(new_u, hydrated_at=LEGACY_HYDRATED_AT)
        after = db.table_counts()

    print(f"Legado nos JSON:  {len(tweets)} tweets, {len(users)} autores")
    print(f"Migrados agora:   {len(new_t)} tweets, {len(new_u)} autores")
    print(f"tweets: {before['tweets']} -> {after['tweets']}   users: {before['users']} -> {after['users']}")


if __name__ == "__main__":
    main()
