# Síntese de clusters por LLM — design (2026-10-13)

Etapa E3 da proposta do TCC2 (`docs/proposta-tcc2.md`), revisão de D8 desta data
(`docs/decisoes-metodologicas.md`). Produz, para cada par (evento, cluster), uma síntese em
texto livre do que circulou no cluster, como **ajuda de leitura para os rotuladores humanos**
— não como categorização. A categorização é humana e vem depois.

## 1. Objetivo e postura

- O LLM **condensa**; não categoriza. Não recebe nem impõe categorias, "tese central",
  "protagonistas/antagonistas" ou "lados". Se essa estrutura existir, aparece no texto e é
  mostrada no material.
- O que é **contável** é calculado pela pipeline, não estimado pelo LLM: contas mais
  retuitadas, tamanho do cluster, atrição. O LLM só as comenta.
- Toda afirmação sobre conteúdo cita `[tweet_id]` inline; as citações são checadas
  automaticamente contra o corpus do cluster.
- A inclinação política provável entra, em texto livre e com confiança (alta/média/baixa),
  por decisão com a orientadora (revisão de D8, 2026-10-13). Ela fica visível no app desde o
  início; o efeito de ancoragem sobre os rotuladores é trade-off assumido e registrado.

## 2. Corpus por (evento, cluster)

Dois blocos, os dois hidratados:

- **Bloco A — mais amplificados:** o top-K já existente (M8, `event_top_tweets`, intocado).
- **Bloco B — característicos (cauda):** novo M8b. Para cada tweet *t* e cluster *c*:

  ```
  lift(t, c) = (rt_c(t) / rt_graph(t)) / (RT_c / RT_graph)
  ```

  `rt_c(t)` = membros de *c* que retuitaram *t* (usuário×tweet distinto conta 1, como em M3);
  `rt_graph(t)` = nós do grafo que retuitaram *t*; `RT_c`, `RT_graph` = os mesmos totais somados
  sobre todos os tweets. Lift 1 = o tweet circula em *c* na proporção do peso de *c* no evento.
  Candidatos: `rt_c(t) ≥ min_rt`, `lift > 1` (sobrerrepresentado — a definição do bloco)
  e *t* fora do top-K de *c*. Seleção: top-`m` por
  lift desc → rt_cluster desc → tweet_id asc. Valores iniciais a ajustar: `m = 50`,
  `min_rt = 10`.

  *Por que lift, não exclusividade:* medido em 2026-10-13, o critério "≥ 90% dos RTs vêm de c"
  devolve centenas a milhares de tweets nos polos fechados e ~0 nas fatias de um polo
  subdividido — as fatias diferem em grau, não em exclusividade. O lift ordena os dois casos
  com uma regra só (D16).

## 3. Componentes e fluxo

```
M8  TopTweetSelector (existe)  → event_top_tweets   (top-K por rt_cluster)
M8b TailSelector (novo)        → tail_tweets.parquet + event_tail_tweets (top-m por lift)
M9  TweetHydrator/UserHydrator → tweets, users      (pendentes = união das duas seleções)
M11 ClusterSummarizer (novo)   → cluster_summaries  (evento × cluster × modelo × prompt)
M10 WebExporter (estendido)    → event.json: top_accounts + summary; tweets.json: slots da cauda
```

### M8b — `TailSelector` (`modules/select_tweets.py`)
`Stage` com `FILES = ("tail_tweets.parquet", "tail_tweets_stats.json")`. Entradas: `nodes`,
`retweets`, `top` (saída do M8). Clusters = os do top-K (mesmo `min_frac`). Saída por linha:
`community, rank, tweet_id, rt_cluster, rt_graph, rt_event, lift, m`. Gravada no banco por
*replace* por evento (`Database.replace_event_tail_tweets`), como o M8.

### M9 — sem mudança de código de hidratação
`Database.selected_tweet_ids()` passa a ser a união de `event_top_tweets` e
`event_tail_tweets`. Custo estimado: ≤ ~750 tweets × US$ 0,005 + autores novos × US$ 0,010.

### M11 — `ClusterSummarizer` (`modules/summarize.py`)
1. `build_input(db, slug, community, cluster_stats)` → dict com: evento (nome, data),
   tamanho do cluster, `top_accounts` (soma de `rt_cluster` por autor sobre os tweets
   hidratados dos dois blocos, com @handle, nome, bio, verificação), blocos A e B (cada tweet:
   `tweet_id`, @autor, rt_cluster, lift, texto), contagem de indisponíveis.
2. `render_prompt(template, input)` — template versionado em `prompts/sintese_cluster_v1.md`
   (placeholders `{{...}}`); grava-se o SHA-256 do prompt renderizado.
3. Runner injetável. O padrão, `ClaudeCliRunner`, chama
   `claude -p --model claude-sonnet-5-5 --output-format json --json-schema <schema>
   --tools "" --system-prompt <curto> --no-session-persistence --setting-sources ""`
   com o prompt no stdin, a partir de um diretório neutro (sem CLAUDE.md). Usa a assinatura.
   Lê `structured_output` e o ID canônico do modelo em `modelUsage`. `temperature` não é
   controlável por esse caminho: reprodutibilidade = prompt + modelo + resposta bruta salvos.
4. Falha (exit ≠ 0, `is_error`, saída fora do schema): 1 nova tentativa; persistindo, grava a
   linha com `status = 'error'` e a resposta bruta — nunca inventa saída.
5. `validate_citations(output, corpus_ids)` → IDs citados, IDs inválidos (fora do corpus do
   cluster). Inválidos ficam registrados, não são removidos do texto.
6. Cache = o banco: `run()` só chama o modelo para pares sem linha `ok` para
   (evento, cluster, modelo, versão do prompt). `force=True` refaz.

Schema da saída do modelo:

```json
{
  "sintese": "250–400 palavras, citações [tweet_id] inline",
  "contas_prevalentes": "texto, com [tweet_id]",
  "inclinacao_politica": { "texto": "...", "confianca": "alta|media|baixa" },
  "limites": "..."
}
```

Tabela `cluster_summaries` (PK `event_slug, community, model, prompt_version`):
`status ('ok'|'error'), output_json, raw_response, prompt_sha256, input_json,
cited_ids_json, invalid_ids_json, generated_at`.

### M10 — exportação
- `event.json`, por cluster: `top_accounts` (lista calculada) e `summary` (saída do modelo +
  `model`, `prompt_version`, `generated_at`, `invalid_ids`), ou `null` se não houver.
- `tweets.json`: slots ganham `origin` (`"amplified"` para o top-K, `"characteristic"` para a
  cauda) e `lift` (só na cauda). O app mostra a síntese no painel do cluster, com `[id]`
  clicáveis que levam ao card do tweet.

## 4. Prompt

Texto integral em `prompts/sintese_cluster_v1.md` (aprovado em 2026-10-13). Pontos de
desenho: só nome e data do evento (sem descrição nossa, que já enquadraria); regra "fique no
material", com conhecimento externo declarado; sem adjetivação avaliativa; "indeterminada" é
resposta válida para a inclinação; o eixo esquerda/direita não é obrigatório.

## 5. Testes

- `TailSelector`: lift calculado à mão num log de brinquedo; piso; exclusão do top-K;
  desempate; corte em `m`.
- `Database`: `replace_event_tail_tweets` idempotente; `selected_tweet_ids` = união;
  `cluster_summaries` upsert.
- `summarize`: montagem do input (top_accounts, blocos, indisponíveis); render sem
  placeholders restantes; validador de citações; summarizer com runner falso (sucesso,
  falha com retry, citação inválida, cache).
- `export`: `origin`/`lift` nos slots; `summary`/`top_accounts` no event.json.

## 6. Fora de escopo

- Chamada contrastiva por evento (comparar sínteses de clusters irmãos).
- Comparação com a leitura manual (`docs/relatorio-narrativa-preliminar.md`) — feita depois,
  com as sínteses prontas; é parte da validação de D8.
- Segundo modelo de comparação (decidido: só Sonnet 5.5).
