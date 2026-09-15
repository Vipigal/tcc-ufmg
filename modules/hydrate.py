"""Módulo 9 — hidratação via API do X, com o banco como cache.

Estágios no padrão da pipeline (`Stage`), mas com uma diferença deliberada:
`FILES = ()`. O cache **é o banco** (`hydrated.sqlite`), não um arquivo em
`out_dir` — logo `run()` sempre executa, e o que ele executa é só o que falta:

  - `TweetHydrator`: IDs em `event_top_tweets` que não estão em `tweets` nem em
    `lookup_errors` (M8 → M9). Chama `/2/tweets` em lotes de 100, sem expansions,
    faz *upsert* do retorno em `tweets` e registra em `lookup_errors` os IDs que a
    API não devolveu, com o motivo (removido, não autorizado/suspenso...).
  - `UserHydrator`: autores dos tweets em cache que não estão em `users` nem em
    `lookup_errors` — passo separado, quando D7/D8 exigirem (D6).

Re-executar sem novidade não faz chamada alguma. `retry_errors=True` (ligado ao
`FORCE_FROM` do notebook) re-tenta os IDs com erro registrado — não custa nada,
porque só recursos devolvidos são cobrados; se um voltar, o erro é apagado.

Cada lote é gravado antes do próximo: o banco é o checkpoint (README, princípio 1).
A atrição por cluster — compromisso do D6 — sai de `hydration_status(db)`.
"""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from modules.fetch_x_data import BATCH_SIZE, COST_PER_TWEET, COST_PER_USER
from modules.stage import Stage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class HydrationReport:
    """O que uma rodada pediu, recebeu e pagou."""

    resource_type: str            # 'tweet' | 'user'
    n_pending: int                # IDs pedidos nesta rodada
    n_returned: int               # recursos devolvidos (cobrados)
    n_errors: int                 # IDs que a API não devolveu (com motivo)
    errors_by_title: dict = field(default_factory=dict)
    cost_usd: float = 0.0
    started_at: str = ""
    finished_at: str = ""

    def summary(self) -> str:
        unit = "tweets" if self.resource_type == "tweet" else "usuários"
        motivos = ", ".join(f"{k}: {v}" for k, v in self.errors_by_title.items()) or "nenhum"
        return (f"{self.n_pending} {unit} pendentes → {self.n_returned} devolvidos, "
                f"{self.n_errors} não devolvidos ({motivos}) · US$ {self.cost_usd:.2f}")


class _Hydrator(Stage):
    """Base: pendência → lotes → upsert + erros. Subclasses dizem qual recurso."""

    FILES = ()                    # o cache é o banco, não arquivo (ver docstring do módulo)
    resource_type: str = ""
    cost_per_item: float = 0.0

    def __init__(self, db, client, retry_errors: bool = False,
                 pause_s: float = 1.0, sleep=time.sleep):
        self.db = db
        self.client = client
        self.retry_errors = retry_errors
        self.pause_s = pause_s
        self._sleep = sleep

    # --- o que cada recurso define ---
    def _pending(self) -> list[str]:
        raise NotImplementedError

    def _lookup(self, ids: list[str]) -> tuple[list[dict], list[dict]]:
        raise NotImplementedError

    def _store(self, data: list[dict]) -> None:
        raise NotImplementedError

    # --- hidratação ---
    def hydrate(self) -> HydrationReport:
        started = _now()
        ids = self._pending()
        batches = [ids[i:i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
        print(f"[M9] {self.resource_type}: {len(ids)} pendentes em {len(batches)} lote(s)"
              + (" — re-tentando IDs com erro" if self.retry_errors else ""))

        n_returned = n_errors = 0
        by_title: Counter = Counter()
        for i, batch in enumerate(batches):
            data, errors = self._lookup(batch)
            attempted_at = _now()
            self._store(data)                                          # cache primeiro
            self.db.clear_lookup_errors(self.resource_type, [d["id"] for d in data])
            self.db.upsert_lookup_errors(self.resource_type, errors, attempted_at=attempted_at)
            n_returned += len(data)
            n_errors += len(errors)
            by_title.update(e.get("title") or "sem título" for e in errors)
            print(f"  lote {i + 1}/{len(batches)}: {len(batch)} pedidos → "
                  f"{len(data)} devolvidos, {len(errors)} não devolvidos")
            if i < len(batches) - 1:
                self._sleep(self.pause_s)

        return HydrationReport(resource_type=self.resource_type, n_pending=len(ids),
                               n_returned=n_returned, n_errors=n_errors,
                               errors_by_title=dict(by_title),
                               cost_usd=n_returned * self.cost_per_item,
                               started_at=started, finished_at=_now())

    # --- hooks de cache (Stage): FILES vazio → run() sempre computa ---
    def _compute(self) -> HydrationReport:
        return self.hydrate()

    def _save(self, report: HydrationReport, out_dir) -> None:
        pass                      # nada em disco: o estado está no banco

    def _load(self, out_dir):
        raise NotImplementedError("FILES vazio — este estágio nunca carrega de disco")


class TweetHydrator(_Hydrator):
    """M9 — tweets selecionados (M8) que ainda não estão no cache."""

    resource_type = "tweet"
    cost_per_item = COST_PER_TWEET

    def _pending(self) -> list[str]:
        return self.db.pending_tweet_ids(retry_errors=self.retry_errors)

    def _lookup(self, ids):
        return self.client.lookup_tweets(ids)

    def _store(self, data) -> None:
        self.db.upsert_tweets(data)


class UserHydrator(_Hydrator):
    """M9 (autores) — autores dos tweets em cache que ainda não estão em `users`."""

    resource_type = "user"
    cost_per_item = COST_PER_USER

    def _pending(self) -> list[str]:
        return self.db.pending_author_ids(retry_errors=self.retry_errors)

    def _lookup(self, ids):
        return self.client.lookup_users(ids)

    def _store(self, data) -> None:
        self.db.upsert_users(data)


def hydration_status(db) -> pd.DataFrame:
    """Situação da hidratação por (evento, cluster), direto do banco.

    `atricao` = (selecionados − hidratados) / selecionados — inclui pendentes, então
    só é a atrição final quando `pendentes` = 0. Motivos: `Not Found Error` (tweet
    removido) e `Authorization Error` (conta suspensa ou protegida).
    """
    sql = """
        SELECT e.event_slug AS evento, e.community AS cluster,
               COUNT(*)                                                         AS selecionados,
               SUM(t.tweet_id IS NOT NULL)                                      AS hidratados,
               SUM(t.tweet_id IS NULL AND le.title = 'Not Found Error')         AS nao_encontrados,
               SUM(t.tweet_id IS NULL AND le.title = 'Authorization Error')     AS nao_autorizados,
               SUM(t.tweet_id IS NULL AND le.resource_id IS NOT NULL
                   AND COALESCE(le.title, '') NOT IN ('Not Found Error', 'Authorization Error'))
                                                                                AS outros_erros,
               SUM(t.tweet_id IS NULL AND le.resource_id IS NULL)               AS pendentes
        FROM event_top_tweets e
        LEFT JOIN tweets t         ON t.tweet_id = e.tweet_id
        LEFT JOIN lookup_errors le ON le.resource_type = 'tweet' AND le.resource_id = e.tweet_id
        GROUP BY e.event_slug, e.community
        ORDER BY e.event_slug, e.community"""
    df = pd.read_sql(sql, db.conn)
    df["atricao"] = (df["selecionados"] - df["hidratados"]) / df["selecionados"]
    return df
