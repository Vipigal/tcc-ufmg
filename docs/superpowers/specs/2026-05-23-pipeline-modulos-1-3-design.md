# Design — Pipeline de Co-retweet: Módulos 1 a 3

**Data:** 2026-05-23
**Escopo:** Primeira versão dos módulos de ingestão, filtragem de ruído e construção da matriz bipartida da pipeline de análise de polarização do TCC.
**Referências:** `docs/especificacao-tecnica.md` (§2.2 passos 1–3), `docs/decisoes-metodologicas.md` (D2, D3, D5).

---

## 1. Contexto e objetivo

A pipeline transforma os CSVs de um evento político do dataset Silva et al. (2024) em um grafo de co-retweet. Este design cobre os **três primeiros passos** dessa pipeline:

1. Carga e filtragem para retweets.
2. Filtragem de ruído (usuários inativos + tweets virais espúrios).
3. Construção da matriz bipartida usuário × tweet.

Os passos seguintes (projeção Jaccard, backbone, Leiden, métricas) ficam fora deste escopo e serão projetados depois, consumindo a saída do Módulo 3.

## 2. Princípios de design (decididos no brainstorming)

- **Operação em memória, persistência opcional.** Cada classe recebe e retorna objetos em memória. Persistir em `data/processed/<evento>/` é um método `.save(out_dir)` separado, chamado explicitamente no notebook. Isso dá agilidade na fase de calibração de parâmetros.
- **Parâmetros via construtor.** Os parâmetros calibráveis (N de usuário inativo, X% de tweet viral) são argumentos de `__init__`, explícitos no notebook. Evolução para arquivo de config fica para depois.
- **Formato de persistência: Parquet + NPZ.** DataFrames em Parquet (compacto, tipado, escala para ~1,2M linhas); matriz esparsa em `.npz` (scipy); mapeamentos em Parquet.
- **Um arquivo `.py` por etapa, uma classe principal por arquivo.** Mantém cada classe com propósito único.
- **Localização: `modules/`.** O projeto já usa essa pasta (`modules/fetch_x_data.py`). A spec técnica sugeria `pipeline/`, mas seguimos a convenção existente.

## 3. Fluxo de dados

```
CSV(s) do evento
   │  modules/load.py        →  RetweetLoader
   ▼
DataFrame de retweets  (author_id, referenced_tweet_id, created_at)
   │  modules/filter.py      →  NoiseFilter
   ▼
DataFrame filtrado     (+ stats de filtragem)
   │  modules/bipartite.py   →  BipartiteBuilder
   ▼
BipartiteGraph  (B esparsa  +  user_index  +  tweet_index)
```

## 4. Descoberta importante sobre os dados

O campo `referenced_tweets` no dataset **não é JSON**, ao contrário do que a §1.3 da especificação técnica sugere. O valor real é um repr de objeto Python:

```
[<ReferencedTweet id=1612168393779720192 type=retweeted]
```

Logo, o parsing é feito por **expressão regular** extraindo `id` e `type`, e não com `json.loads`. Os tipos observados são `retweeted`, `replied_to` e `quoted`; linhas de tweets originais têm o campo vazio.

Colunas reais do CSV: `conversation_id`, `Created_at_convert`, `author_id`, `referenced_tweets`.

## 5. Módulo 1 — `modules/load.py` → `RetweetLoader`

**Propósito:** ler um evento (1 ou mais CSVs), parsear `referenced_tweets`, manter apenas retweets.

**Interface:**

- `__init__(self, csv_paths)` — aceita:
  - um caminho de arquivo (`str`/`Path`),
  - uma lista de caminhos,
  - ou um diretório (carrega todos os `.csv` dentro). Um evento pode ter vários CSVs (invasão: 7; Roberto Jefferson: 4).
- `.load() -> pd.DataFrame` — concatena os CSVs, parseia, filtra para `type == retweeted`. Colunas de saída:
  - `author_id` (`string`) — quem retuitou.
  - `referenced_tweet_id` (`string`) — ID do tweet retuitado.
  - `created_at` (`datetime64`, tz-aware) — derivado de `Created_at_convert`.
- `.save(out_dir)` — escreve `retweets.parquet` em `out_dir` (cria o diretório se necessário).

**Decisões internas:**

- IDs (`author_id`, `referenced_tweet_id`) tratados como `string` para evitar perda de precisão em IDs de 64 bits e facilitar operações de conjunto a jusante.
- `created_at` parseado com timezone preservado (será usado no filtro temporal do 8 de janeiro).
- Linhas com `referenced_tweets` vazio ou de outros tipos são descartadas silenciosamente; a contagem de descartados fica disponível para inspeção.

## 6. Módulo 2 — `modules/filter.py` → `NoiseFilter`

**Propósito:** aplicar os dois filtros de ruído da especificação (§2.2 passo 2; D5), em sequência.

**Interface:**

- `__init__(self, min_user_retweets=3, viral_user_fraction=0.30)` — defaults vindos da spec, ajustáveis na calibração preliminar.
- `.apply(df) -> pd.DataFrame`:
  1. **Filtro de usuários inativos:** descarta usuários com menos de `min_user_retweets` retweets (contagem de ações, isto é, de linhas).
  2. **Filtro de tweets virais:** sobre o conjunto de usuários remanescente, descarta tweets retuitados por mais de `viral_user_fraction` dos usuários distintos do evento.
- `.stats` — dict populado por `.apply()` com contagens antes/depois de cada filtro: nº de usuários, nº de tweets distintos, nº de linhas. Material direto para a calibração.
- `.save(out_dir)` — escreve `filtered_retweets.parquet` + `filter_stats.json`.

**Decisões internas:**

- Ordem fixa: usuários primeiro, depois tweets virais (sequência da spec). A fração de viralidade é computada sobre a base de usuários **já filtrada**.
- Versão atual faz **uma passada** (sem re-aplicar o filtro de usuários após remover tweets virais). A re-aplicação iterativa fica registrada como possível ajuste futuro, caso a calibração mostre necessidade.
- "Retweets do usuário" = número de linhas (ações) atribuídas a ele, antes da deduplicação de pares.

## 7. Módulo 3 — `modules/bipartite.py` → `BipartiteBuilder`

**Propósito:** construir a matriz de incidência esparsa binária usuário × tweet.

**Interface:**

- `.build(df) -> BipartiteGraph`.
- `BipartiteGraph` — dataclass com:
  - `B`: `scipy.sparse.csr_matrix` de forma `(n_users, n_tweets)`, com `B[u, t] = 1` se o usuário `u` retuitou o tweet `t`.
  - `user_index`: mapeamento linha → `author_id` original.
  - `tweet_index`: mapeamento coluna → `referenced_tweet_id` original.
  - `.save(out_dir)`: escreve `bipartite_B.npz` (`scipy.sparse.save_npz`) + `user_index.parquet` + `tweet_index.parquet`.

**Decisões internas:**

- Índices construídos com `pd.factorize` sobre `author_id` e `referenced_tweet_id`.
- Pares (user, tweet) deduplicados: um retweet repetido conta como 1 (matriz binária), pré-requisito do peso Jaccard (D3).
- Construção via `coo_matrix` a partir dos códigos do factorize, convertida para `csr_matrix`.
- `BipartiteGraph` é a fronteira de saída deste escopo; é o que o futuro Módulo 4 (projeção Jaccard) consumirá.

## 8. Dependências

A instalar nesta etapa:

- `scipy` — matriz esparsa.
- `pyarrow` — leitura/escrita de Parquet.

Para etapas posteriores (fora deste escopo): `igraph`, `leidenalg`.

## 9. Uso esperado no notebook (`notebooks/pipeline.ipynb`)

```python
from modules.load import RetweetLoader
from modules.filter import NoiseFilter
from modules.bipartite import BipartiteBuilder

EVENT = "invasao-3-poderes"

loader = RetweetLoader(f"data/raw/{EVENT}")
rt = loader.load()

nf = NoiseFilter(min_user_retweets=3, viral_user_fraction=0.30)
rt_f = nf.apply(rt)
print(nf.stats)

bg = BipartiteBuilder().build(rt_f)
bg.save(f"data/processed/{EVENT}")
```

## 10. Fora de escopo

- Projeção Jaccard, backbone, Leiden, métricas estruturais (passos 4–7).
- Hidratação, classificação, score ideológico, narrativa (seções 3–4 da spec).
- Arquivo de configuração externo e script `run_all`.
- Validação preliminar de parâmetros (será feita no notebook usando estes módulos).
