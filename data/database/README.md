# Banco de dados — `hydrated.sqlite`

Banco **SQLite** que consolida os dados **caros e insubstituíveis** do projeto — o que é
hidratado pela API do X (tweets e autores) e a classificação ideológica desses autores —
além de uma projeção analítica leve do resultado do pipeline (comunidades por usuário).

É um banco **global, único para os quatro eventos**: a chave de cada entidade hidratada é o
id estável do recurso (tweet/usuário), então um tweet ou autor buscado para um evento **nunca
é re-hidratado** em outro. Isso materializa o princípio de reaproveitamento entre eventos
(`docs/visao-projeto.md`) e o cache obrigatório de hidratação (`docs/especificacao-tecnica.md` §3.2).

- **Arquivo do banco:** `data/database/hydrated.sqlite`
- **Esta documentação:** `data/database/README.md` — evolui junto com o schema; ver o [Changelog](#changelog).

> Status (2026-09-15): schema completo e em uso pela fase 2 (`notebooks/pipeline_tcc2.ipynb`):
> `event_top_tweets` recebe a seleção por cluster (M8) e o M9 (`modules/hydrate.py`) hidrata
> pela API usando `tweets`/`users` como cache e registrando em `lookup_errors` o que a API não
> devolve. Autores hidratados em 2026-09-15 (`UserHydrator`: 313 devolvidos, 0 negados; `users`
> cobre os 379 autores dos tweets em cache). A hidratação de maio/2026 (83 tweets, 72 autores da
> invasão) foi migrada uma única vez por `scripts/migrate_legacy_hydration.py`. O M10
> (`modules/export.py`) exporta tudo para `data/export/` (JSON para o app web, D15).
> `community_membership` continua vazia.

---

## Princípios de design

Cada um desses pontos foi uma decisão consciente; estão aqui para não serem reabertos sem motivo.

1. **O banco é a fonte de verdade do cache de hidratação.** O M9 (`modules/hydrate.py`)
   consulta o banco antes de chamar a API — pede só `event_top_tweets ∖ tweets ∖ lookup_errors`
   — e faz *upsert* do retorno lote a lote. As linhas no banco **são** o checkpoint; não há
   checkpoint em arquivo. `modules/fetch_x_data.py` é apenas o cliente HTTP (`XClient`).

2. **Lossless por `raw_json`.** Toda linha hidratada guarda o payload **completo** da API em
   `raw_json`. As colunas "achatadas" existem por ergonomia de consulta; o `raw_json` garante
   que qualquer campo possa ser re-derivado depois **sem pagar a API de novo**.

3. **Hidratar uma vez (snapshot).** Métricas como `followers_count` mudam com o tempo, mas
   tratamos a primeira busca como o snapshot. `hydrated_at` registra quando foi, permitindo um
   refresh manual deliberado no futuro, se algum dia for necessário.

4. **Sem chaves estrangeiras — referências lógicas.** As relações entre tabelas (ex.:
   `tweets.author_id` → `users.user_id`) são **lógicas**, não impostas por `FOREIGN KEY`.
   Decisão deliberada: um tweet cujo autor foi suspenso/removido é uma realidade do dado, não
   um erro a ser "consertado" com linha-stub. Dado faltante fica faltante. Mantemos PKs,
   índices e `CHECK` de enum (qualidade de dado, não integridade referencial).

5. **Retweets ficam em Parquet, não aqui.** A relação bipartida usuário×tweet
   (`retweets.parquet`, ~1,1M linhas/evento) é **gratuita e determinística** de regenerar a
   partir dos CSVs brutos — não tem custo de API e não pertence a um cache cujo trabalho é
   "nunca pagar duas vezes". O pipeline já a usa eficientemente em Parquet (colunar + zstd,
   ver D13/D14). Para SQL ad-hoc sobre os retweets, aponte o **DuckDB** direto no Parquet
   (`SELECT ... FROM 'retweets.parquet'`) — sem duplicar dado.

6. **`community_membership` é uma projeção derivada, não a fonte de verdade.** O
   `graph_nodes.parquet` continua sendo o acumulador e a fonte de verdade dos atributos por
   usuário do pipeline (D14). Esta tabela é uma cópia de conveniência, populada por um *dump*
   no fim do pipeline, cujo único ganho é tornar trivial a consulta **longitudinal entre
   eventos** (mesmo usuário ao longo dos 4 eventos), que de outra forma exigiria juntar 4
   Parquets em pandas a cada vez.

### Convenções de tipo (SQLite)

- **Datas:** `TEXT` em ISO-8601 (formato que a própria API retorna). SQLite não tem tipo de data.
- **Booleanos:** `INTEGER` `0`/`1` (SQLite não tem `BOOLEAN`).
- **Enums:** `TEXT` com `CHECK (col IN (...))` (SQLite não tem `ENUM`).
- **Conexão:** se algum dia adotarmos FKs, lembrar que o SQLite exige `PRAGMA foreign_keys = ON`
  por conexão (hoje irrelevante — não usamos FKs).

---

## Tabelas

### `events` — dimensão de eventos
Os quatro eventos do recorte. `slug` segue a convenção das pastas `data/processed/<slug>/`.

| coluna | tipo | descrição |
|---|---|---|
| `slug` | TEXT PK | identificador do evento (= nome da pasta em `data/processed/`) |
| `name` | TEXT | nome legível |
| `event_date` | TEXT | data principal do evento (ISO-8601) |
| `notes` | TEXT | origem dos CSVs brutos / observações |

### `users` — cache de autores hidratados
O "cache de usuários" do projeto. Chave = id da conta. Atualizado por *upsert*.

| coluna | tipo | descrição |
|---|---|---|
| `user_id` | TEXT PK | id numérico da conta (como string) |
| `username` | TEXT | @handle |
| `name` | TEXT | nome de exibição |
| `description` | TEXT | bio |
| `location` | TEXT | localização declarada no perfil |
| `url` | TEXT | url do perfil |
| `profile_image_url` | TEXT | avatar |
| `protected` | INTEGER | conta privada? (0/1) |
| `verified` | INTEGER | verificado? (0/1) |
| `verified_type` | TEXT | `blue` / `business` / `government` / `none` |
| `account_created_at` | TEXT | criação da **conta** (ISO-8601) |
| `followers_count` | INTEGER | seguidores (snapshot da API) |
| `following_count` | INTEGER | seguindo |
| `tweet_count` | INTEGER | total de tweets da conta |
| `listed_count` | INTEGER | nº de listas em que aparece |
| `like_count` | INTEGER | likes dados pela conta |
| `media_count` | INTEGER | mídias publicadas |
| `raw_json` | TEXT | payload completo do user object (lossless) |
| `hydrated_at` | TEXT | quando foi hidratado (NULL = não hidratado) |

### `tweets` — cache de tweets hidratados
Os tweets originais mais retuitados, hidratados via `/2/tweets`.

| coluna | tipo | descrição |
|---|---|---|
| `tweet_id` | TEXT PK | id do tweet |
| `author_id` | TEXT | autor (referência lógica a `users.user_id`; indexado) |
| `text` | TEXT | texto do tweet |
| `created_at` | TEXT | criação do **tweet** (ISO-8601) |
| `lang` | TEXT | idioma detectado pela API |
| `conversation_id` | TEXT | id da conversa |
| `source` | TEXT | app de origem |
| `in_reply_to_user_id` | TEXT | usuário respondido, se houver |
| `possibly_sensitive` | INTEGER | marcado como sensível? (0/1) |
| `reply_settings` | TEXT | quem pode responder |
| `geo_place_id` | TEXT | id de local, se houver |
| `retweet_count` | INTEGER | métrica **global** da API (≠ contagem local do evento) |
| `reply_count` | INTEGER | respostas (público) |
| `like_count` | INTEGER | curtidas (público) |
| `quote_count` | INTEGER | citações (público) |
| `bookmark_count` | INTEGER | salvamentos (público) |
| `impression_count` | INTEGER | impressões (público) |
| `raw_json` | TEXT | payload completo do tweet object, incl. `entities` (lossless) |
| `hydrated_at` | TEXT | quando foi hidratado |

> **Entidades (hashtags/mentions/urls/annotations)** ficam dentro de `raw_json` por enquanto.
> Se a análise de hashtags virar protagonista, normalizamos em tabelas próprias — YAGNI até lá.

### `lookup_errors` — IDs que a API não devolveu
O array `errors` de `/2/tweets` e `/2/users`, uma linha por recurso pedido e não devolvido,
com o **motivo dado pela API**. É dado faltante com causa registrada — e é a base da atrição
por cluster que o D6 se compromete a reportar (`modules.hydrate.hydration_status`). Última
tentativa vale (*upsert*); se o recurso voltar num retry, a linha é apagada. Recursos não
devolvidos não são cobrados.

| coluna | tipo | descrição |
|---|---|---|
| `resource_type` | TEXT | `tweet` / `user` (CHECK) |
| `resource_id` | TEXT | id pedido (`resource_id` ou `value` do erro) |
| `title` | TEXT | `Not Found Error` (removido) / `Authorization Error` (conta suspensa ou protegida) / outros |
| `detail` | TEXT | mensagem da API |
| `type` | TEXT | URI do tipo de problema |
| `attempted_at` | TEXT | quando foi a tentativa (ISO-8601) |
| `raw_json` | TEXT | objeto de erro completo (lossless) |
| — | PK | `(resource_type, resource_id)` |

### `author_classification` — rótulo ideológico do autor
1:1 com `users`, **reusada entre eventos** (classificou num evento, vale nos demais).
Saída do LLM + revisão manual (`docs/especificacao-tecnica.md` §3.3, D8).

| coluna | tipo | descrição |
|---|---|---|
| `author_id` | TEXT PK | referência lógica a `users.user_id` |
| `classification` | TEXT | `left` / `right` / `media` / `neutral` / `unknown` (CHECK) |
| `confidence` | TEXT | `high` / `medium` / `low` (CHECK) |
| `justification` | TEXT | justificativa curta |
| `classified_by` | TEXT | `llm` / `manual` / `llm+manual` |
| `llm_model` | TEXT | modelo usado na 1ª passada |
| `classified_at` | TEXT | quando foi classificado |
| `notes` | TEXT | anotações da revisão manual |

### `event_top_tweets` — seleção top-K por (evento, cluster)
Saída do M8 (`modules/select_tweets.py`, D6 revisado em 2026-09-10) gravada por evento:
quais tweets são top-K **em cada cluster** de cada evento, ranqueados pelo nº de retweets
feitos por **membros do cluster**. É um fato derivado do grafo + parâmetros, por isso a
gravação é *replace por evento* (`Database.replace_event_top_tweets`), não upsert: o que
saiu do top-K numa re-seleção some. A cópia em Parquet fica em
`data/processed/<slug>/top_tweets.parquet` (+ `top_tweets_stats.json`).

| coluna | tipo | descrição |
|---|---|---|
| `event_slug` | TEXT | referência lógica a `events.slug` |
| `community` | INTEGER | id da comunidade Leiden (como em `graph_nodes.parquet`) |
| `tweet_id` | TEXT | referência lógica a `tweets.tweet_id` (pode ainda não estar hidratado) |
| `rank` | INTEGER | posição no ranking do cluster (1 = mais retuitado pelos membros) |
| `rt_cluster` | INTEGER | nº de membros do cluster que retuitaram (critério do ranking) |
| `rt_graph` | INTEGER | nº de nós do grafo (qualquer cluster) que retuitaram — pureza = rt_cluster/rt_graph |
| `rt_event` | INTEGER | nº de usuários do evento que retuitaram, inclusive periferia filtrada em M2 |
| `k` | INTEGER | K aplicado ao cluster (100, ou 20 para clusters com ≤5% do peso total) |
| `selected_at` | TEXT | quando a seleção foi gravada |
| — | PK | `(event_slug, community, tweet_id)` — o mesmo tweet pode rankear em vários clusters e eventos |

> Contagens são do **dataset** (usuário×tweet distinto conta 1), não a métrica pública da API,
> que vive em `tweets.retweet_count`.

### `community_membership` — *(fase 2)* projeção analítica por usuário
Cópia de conveniência do resultado do pipeline por `(evento, usuário, τ)`. **Vazia até a
análise comparativa começar.** O `user_id` aqui é um **nó do grafo (retweetador)** — população
muito maior (~33k/evento) e distinta dos autores hidratados em `users`; por isso **não** há
referência lógica a `users` (seria errado). Fonte de verdade continua sendo `graph_nodes.parquet`.

| coluna | tipo | descrição |
|---|---|---|
| `event_slug` | TEXT | referência lógica a `events.slug` |
| `user_id` | TEXT | nó do grafo (retweetador) — **não** referencia `users` |
| `community` | INTEGER | id da comunidade detectada (Leiden) |
| `ideological_score` | REAL | score(u) ∈ [-1,1]; NULL = indefinido (§3.4) |
| `weighted_degree` | REAL | grau ponderado no backbone |
| `tau` | REAL | threshold da rodada (default 0.1; suporta sensibilidade 0.05/0.10/0.15) |
| — | PK | `(event_slug, user_id, tau)` |

---

## Relações (todas lógicas, não impostas)

```
events.slug ─┬─< event_top_tweets.event_slug
             └─< community_membership.event_slug   (fase 2)

users.user_id ─┬─< tweets.author_id
               └─1:1─ author_classification.author_id

tweets.tweet_id ─< event_top_tweets.tweet_id
lookup_errors.(resource_type, resource_id)  →  tweets.tweet_id | users.user_id que a API não devolveu

community_membership.user_id  →  (nó do grafo / retweetador; população distinta de users)
retweets (bipartida usuário×tweet)  →  fora do banco, em data/processed/<slug>/retweets.parquet
```

## Como usar

```python
import sqlite3, pandas as pd
con = sqlite3.connect("data/database/hydrated.sqlite")

# já hidratados? (cache check antes de chamar a API)
have = {r[0] for r in con.execute("SELECT user_id FROM users")}

# ler como DataFrame
tweets = pd.read_sql("SELECT * FROM tweets", con)
```

```bash
# inspeção rápida
sqlite3 data/database/hydrated.sqlite ".schema users"
```

---

## Changelog

Toda mudança de schema é registrada aqui (mais recente no topo).

### 2026-09-15 — seleção por cluster + migração do legado
- `event_top_tweets` refeita para a seleção por **(evento, cluster)** do D6 revisado: PK
  `(event_slug, community, tweet_id)`; colunas `rank`, `rt_cluster`, `rt_graph`, `rt_event`,
  `k`, `selected_at`. Saem `retweet_count_dataset` e `selection_group` (critério do notebook
  exploratório, nunca gravado). `Database.ensure_schema` descarta a forma antiga se estiver
  vazia; se tiver dados, para e avisa.
- `Database.upsert_tweets/upsert_users` aceitam `hydrated_at` explícito (snapshot real na
  migração de dados antigos); `replace_event_top_tweets` e `table_counts` novos.
- Migrados para `tweets`/`users` os 83 tweets e 72 autores da hidratação de 2026-05-09
  (invasão, top-100 global — critério anterior), com `hydrated_at` = data do snapshot.
- `events`: slug `democracia-3010` renomeado para `eleicoes` (= pasta em `data/processed/`).
- Nova tabela `lookup_errors` (array `errors` da API, por recurso) e consultas de pendência
  (`pending_tweet_ids`, `pending_author_ids`, `errored_ids`, `clear_lookup_errors`) para o M9
  (`modules/hydrate.py`); `fetch_x_data.py` reescrito como cliente HTTP puro (`XClient`).

### 2026-06-19 — criação inicial
- Criado `data/database/hydrated.sqlite`.
- Tabelas: `events`, `users`, `tweets`, `author_classification`, `event_top_tweets`,
  `community_membership`. Índice `idx_tweets_author`.
- `events` semeada com os 4 eventos do recorte.
- Decisões: sem FKs (referências lógicas; dado faltante reflete a realidade); `raw_json`
  lossless em `users`/`tweets`; retweets permanecem em Parquet; `community_membership`
  (fase 2) como projeção derivada de `graph_nodes.parquet`.
- Pendente: migrar `hydrated_users.json` + `hydrated_tweets.jsonl` para o banco e reescrever
  `fetch_x_data.py` para usar o banco como cache (spec dedicado a seguir).
