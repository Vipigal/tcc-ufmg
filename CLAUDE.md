# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto do projeto

TCC do Vinicius sobre a **invasão do Congresso/STF/Planalto em 8 de janeiro de 2023** (atos golpistas em Brasília). O trabalho é uma análise de conteúdo do Twitter/X no período do evento — foco em aspectos políticos relevantes, não em memes virais.

## Dados disponíveis

### Dataset bruto — `dataset/invasao-3-poderes/`
7 CSVs cobrindo de 2023-01-08 06h até 2023-01-09 06h (janelas de 3h), totalizando **1.235.087 tweets**. Cada linha tem apenas: `conversation_id`, `Created_at_convert`, `author_id`, `referenced_tweets` (string com `<ReferencedTweet id=... type=retweeted|replied_to|quoted>` ou `NaN` se for original).

Distribuição:
- **101.600 originais** (sem `referenced_tweets`) → exportados para `original_tweets.csv`
- 1.100.026 retweets
- 20.870 replies
- 12.591 quotes

### Tweets originais — `original_tweets.csv`
Mesmas colunas do bruto, só os originais, sem `referenced_tweets`. Base para identificar tweets autorais feitos durante o evento.

### Tweets hidratados — `hydrated_tweets.csv` (+ `.jsonl`, + `hydrated_users.json`)
83 tweets hidratados via API do X (de 100 IDs solicitados — alguns foram apagados). Schema flat com 35 colunas: texto, métricas reais (`retweet_count`, `like_count`, `quote_count`, `reply_count`, `impression_count`), entidades (`hashtags`, `mentions`, `urls`, `annotations`) e dados do autor (`author_username`, `author_followers_count`, `author_verified`, etc).

**Composição dos 100 IDs hidratados (estratégia 50+50):**
- **Top 50 gerais** — IDs mais retweetados *no dataset* (extraídos dos `referenced_tweets` dos retweets). 40 desses tweets são externos ao dataset (figuras públicas, mídia tradicional) e 10 também estão em `original_tweets.csv`.
- **Top 50 originais** — IDs mais retweetados *entre os originais do dataset* (sem overlap com o top geral). Tweets autorais feitos durante a janela do evento.

**Distinção dos grupos no `hydrated_tweets.csv`:** não há coluna nativa marcando o grupo. Derivar via:
```python
original_ids = set(pd.read_csv("original_tweets.csv")["conversation_id"].astype(str))
hydrated["grupo"] = hydrated["tweet_id"].astype(str).apply(
    lambda tid: "originais" if tid in original_ids else "gerais"
)
```
O grupo `gerais` tende a ser dominado por memes/reações virais; o grupo `originais` é mais analisável politicamente (declarações de Lula, jornalistas, congressistas, etc).

### Outros arquivos
- `checkpoint_tweets.json` — checkpoint da hidratação (permite retomar sem repagar)
- `hydrated_users.json` — payload bruto dos usuários hidratados
- `test_tweet.json` — resultado de teste isolado da API

## Análise feita até agora (no notebook)

`exploratory-analysis.ipynb` contém:
1. Concatenação dos 7 CSVs e classificação original vs. referenciado
2. Exportação dos originais
3. Contagem de retweets por ID referenciado → ranking de tweets mais repercutidos no dataset
4. Curva cumulativa de RTs (top 100 captura ~X% dos RTs totais)
5. Estimativa de custo da hidratação (orçamento de $5; cada tweet = $0.005, cada user = $0.010)
6. Definição da estratégia 50+50 e execução da hidratação via `fetch_x_data.py`
7. Visualização dos top tweets hidratados com texto completo
8. **(novo)** Classificação `originais` vs. `gerais` dos hidratados e amostra ordenada por RT do grupo `originais`

## Pipeline de hidratação — `fetch_x_data.py`

Helpers para a API v2 do X. **A cobrança é por recurso retornado** ($0.005/tweet, $0.010/user), independente do número de campos pedidos.

Funções principais:
- `fetch_tweets_batch(ids)` / `fetch_users_batch(ids)` — chamada única, até 100 IDs
- `hydrate_tweets(ids, output_path, checkpoint_path)` — em lotes de 100, com checkpoint e retry de rate limit; grava JSONL
- `hydrate_users(ids, ...)` — idem para usuários; grava JSON único
- `merge_to_csv(...)` — junta tweets + users em `hydrated_tweets.csv` flat
- `estimate_cost(tweet_ids, author_ids)` — calcula custo antes de chamar a API
- `load_hydrated_tweets()` / `load_hydrated_users()` — readers

A API key vem de `.env` (`X_BEARER_TOKEN`). O `.env` está no `.gitignore`.

## Comandos comuns

```bash
# Ativar venv
source .venv/bin/activate

# Rodar o notebook
jupyter notebook exploratory-analysis.ipynb
# ou exportar:
jupyter nbconvert --to script exploratory-analysis.ipynb --stdout

# Inspecionar o notebook sem abrir Jupyter
python3 -c "import json; nb=json.load(open('exploratory-analysis.ipynb')); [print(i, c['cell_type']) for i,c in enumerate(nb['cells'])]"
```

## Convenções

- Manipular notebook programaticamente via `json` (preservar `metadata`, `execution_count: None`, `outputs: []` ao adicionar células novas).
- Toda nova hidratação deve passar por `estimate_cost` antes — o orçamento total disponível é US$ 5.00.
- Ao adicionar campos ao `merge_to_csv`, manter o schema flat (uma linha por tweet, autor embedado via prefixo `author_`).
- IDs do Twitter são inteiros grandes — sempre converter para `str` antes de comparar/fazer merge para evitar perda de precisão do pandas.
