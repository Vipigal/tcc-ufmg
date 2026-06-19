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

> Status (2026-06-19): schema criado e tabela `events` semeada. As tabelas de hidratação
> ainda estão **vazias** — a migração dos dados atuais (`hydrated_users.json`,
> `hydrated_tweets.jsonl`) e a reescrita do `fetch_x_data.py` para gravar direto no banco
> serão tratadas num spec dedicado. `community_membership` é da **fase 2** (análise comparativa).

---

## Princípios de design

Cada um desses pontos foi uma decisão consciente; estão aqui para não serem reabertos sem motivo.

1. **O banco é a fonte de verdade do cache de hidratação.** O `fetch_x_data.py` passará a
   consultar o banco antes de chamar a API e a fazer *upsert* do retorno. As linhas no banco
   **são** o checkpoint — o mecanismo de checkpoint em arquivo (`checkpoint_*.json`) deixa de
   ser necessário. *(A reescrita em si é trabalho do próximo spec.)*

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

### `event_top_tweets` — seleção top-N por evento
Liga `events` × `tweets`: quais tweets foram top-N **em cada evento** e seu rank/contagem
**local**. Separa o fato por-evento do fato global (que vive em `tweets`).

| coluna | tipo | descrição |
|---|---|---|
| `event_slug` | TEXT | referência lógica a `events.slug` |
| `tweet_id` | TEXT | referência lógica a `tweets.tweet_id` |
| `retweet_count_dataset` | INTEGER | nº de retweets **dentro do evento** (do dataset, não da API) |
| `rank` | INTEGER | posição no ranking do evento |
| `selection_group` | TEXT | `originais` / `gerais` (critério do notebook exploratório) (CHECK) |
| — | PK | `(event_slug, tweet_id)` — o mesmo tweet pode rankear em vários eventos |

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
