# Especificação Técnica — Pipeline e Visualização

Este arquivo é o guia técnico para a implementação do projeto. Destina-se a agentes (humanos ou de IA) que vão escrever código para o pipeline de processamento, análise de grafos e visualização. O documento é descritivo, não prescritivo no detalhe — alguns parâmetros são deliberadamente deixados para ajuste empírico.

## 1. Dataset de entrada

### 1.1. Origem

Dataset **Tweet_Eleições_2022** (Silva et al., 2024), disponível no Zenodo sob licença CC-BY 4.0.
DOI: 10.5281/zenodo.11206577

### 1.2. Estrutura dos arquivos

O dataset contém ~9,47 milhões de tweets organizados em **110 arquivos CSV**, cada um correspondendo a um evento político específico do período abril/2022 a janeiro/2023.

**Colunas de cada CSV:**

| Coluna | Tipo | Descrição |
|---|---|---|
| `created_at_convert` | datetime | Data/hora de criação do tweet |
| `author_id` | int | ID do autor da ação (quem retuitou, replicou, citou ou postou original) |
| `conversation_id` | int | ID da conversa à qual o tweet pertence |
| `referenced_tweets` | string/JSON | Lista de referências a outros tweets (vazio para tweets originais) |

### 1.3. Estrutura do campo `referenced_tweets`

Este é o campo crítico. Para cada tweet, indica se ele é resposta, citação, retweet ou original, e qual é o tweet referenciado.

- **Vazio/null:** tweet original (não referencia outro tweet)
- **`[{"type": "retweeted", "id": "..."}]`**: é um retweet
- **`[{"type": "replied_to", "id": "..."}]`**: é uma resposta
- **`[{"type": "quoted", "id": "..."}]`**: é uma citação

**Importante:** o dataset preserva apenas o ID do tweet referenciado, **não o autor original**. Recuperar o autor exige hidratação via API.

### 1.4. Eventos selecionados para análise

| # | Evento | Pasta(s) no dataset | Volume aprox. |
|---|---|---|---|
| 1 | Mobilização 7 de setembro 2022 | `0709_mobilizacao` | ~242 mil |
| 2 | Caso Roberto Jefferson | `2310_robertojefferson_08h-12h`, `_12h-15h`, `_15h-19h`, `_19h-23h` | ~966 mil |
| 3 | Debate "democracia" no 2º turno | `3010_democracia` | ~299 mil |
| 4 | Ataques de 8 de janeiro | `0801_invasao_06hr-09hr`, `_09hr-12hr`, `_12hr-15hr`, `_15hr-18hr`, `_18hr-21hr`, `_21hr-01hr`, `0901_invasao_01hr-06hr` | ~1,23 milhão |

## 2. Pipeline de processamento

### 2.1. Visão geral

A pipeline transforma os arquivos CSV de um evento em um grafo de co-retweet com comunidades detectadas e métricas associadas. A saída é serializada para alimentar a visualização web.

```
CSV(s) do evento
    ↓
[1] Carga e filtragem para retweets
    ↓
[2] Filtragem de ruído (usuários e tweets)
    ↓
[3] Construção da matriz bipartida usuário × tweet
    ↓
[4] Projeção em grafo unipartido com peso Jaccard
    ↓
[5] Backbone extraction (universal threshold)
    ↓
[6] Detecção de comunidades (Leiden)
    ↓
[7] Cálculo de métricas estruturais
    ↓
Saída: grafo + métricas + lista de top tweets por comunidade
```

### 2.2. Etapas detalhadas

**[1] Carga e filtragem para retweets**

- Ler o(s) CSV(s) do evento com pandas.
- Parsear o campo `referenced_tweets`.
- Filtrar apenas linhas com `type=retweeted`.
- Manter as colunas: `author_id` (retweetador), `referenced_tweet_id` (ID do tweet retuitado), `created_at_convert`.

**[2] Filtragem de ruído**

Dois filtros, aplicados em sequência:

- **Filtragem de usuários inativos:** descartar usuários que aparecem como retweetadores menos de N vezes no evento. Valor inicial sugerido: N=3. Ajustar empiricamente.
- **Filtragem de tweets virais espúrios:** descartar tweets que foram retuitados por uma fração muito grande dos usuários do evento (sob a hipótese de que carregam pouca informação ideológica). Valor inicial sugerido: tweets retuitados por mais de 30% dos usuários do evento. Ajustar empiricamente.

Estes dois parâmetros são os mais frágeis da pipeline. Antes de aplicar a pipeline aos quatro eventos, fazer **uma rodada de validação preliminar em um arquivo do 8 de janeiro** (sugestão: `0801_invasao-18hr-21hr` por ser o de maior volume) para calibrar os parâmetros.

**[3] Construção da matriz bipartida usuário × tweet**

- Construir uma matriz esparsa B com dimensões (nº de usuários × nº de tweets retuitados).
- `B[u, t] = 1` se o usuário u retuitou o tweet t no evento, 0 caso contrário.
- Usar formato esparso (`scipy.sparse.csr_matrix` ou equivalente do igraph) para suportar a escala do dataset.

**[4] Projeção em grafo unipartido com peso Jaccard**

- Para cada par (u, v) de usuários com pelo menos um tweet em comum, calcular:

  ```
  J(u, v) = |T_u ∩ T_v| / |T_u ∪ T_v|
  ```

  onde T_u é o conjunto de tweets retuitados pelo usuário u.

- Implementação recomendada: usar operações matriciais sobre B para calcular B·Bᵀ (matriz de interseções), depois dividir elemento a elemento pelos tamanhos das uniões. Evitar loop em Python sobre todos os pares.

**[5] Backbone extraction (universal threshold)**

- Reter apenas arestas com peso Jaccard `≥ τ`.
- Valor inicial: τ = 0,1.
- **Análise de sensibilidade obrigatória:** rodar a pipeline também com τ = 0,05 e τ = 0,15 e documentar como os resultados variam. Os resultados desta análise vão no apêndice do TCC.

**[6] Detecção de comunidades (Leiden)**

- Aplicar Leiden via igraph: `igraph.Graph.community_leiden()`.
- Parâmetro de resolução: começar com o default (1.0). Ajustar se as comunidades resultantes estiverem fragmentadas demais ou agregadas demais.
- Reportar:
  - Número total de comunidades detectadas
  - Tamanho das duas maiores comunidades (% do grafo)
  - Modularidade Q

**[7] Cálculo de métricas estruturais**

Para cada execução:

- **Modularidade Q** do particionamento
- **Tamanho relativo** dos dois maiores clusters
- **Fluxo inter-cluster:** soma dos pesos das arestas entre os dois maiores clusters / soma total dos pesos
- **Top-K usuários por centralidade** (degree ponderado) em cada cluster — útil para identificar quem ancora a bolha
- **Coeficiente de assortatividade** com respeito ao cluster

### 2.3. Serialização da saída

Para cada evento, salvar os seguintes artefatos:

- **`graph_<evento>.json`**: nós (com cluster, score ideológico, atributos temporais) e arestas (com peso). Formato compatível com Sigma.js.
- **`metrics_<evento>.json`**: métricas estruturais.
- **`top_tweets_<evento>.json`**: lista dos tweets mais retuitados, com texto hidratado, autor, classificação ideológica do autor, cluster ao qual está associado.

Salvar também o estado intermediário do grafo (após Leiden) em formato igraph nativo (`pickle` ou `graphml`) para permitir re-análise sem reprocessar do zero.

## 3. Hidratação e rotulagem ideológica

### 3.1. Ranking sem hidratação

Para cada evento, antes de qualquer chamada à API:

- Agregar os `referenced_tweets` por ID e contar quantas vezes cada tweet foi retuitado.
- Selecionar os **top-200** tweets do evento por contagem de retweets.

### 3.2. Hidratação via API do X

- Endpoint: `/2/tweets` (lookup de IDs em lote, até 100 por chamada).
- Para cada tweet hidratado, salvar em cache: `tweet_id`, `text`, `author_id_original`, `author_username`, `created_at`, `lang`.
- **Cache obrigatório em SQLite.** Schema sugerido:

  ```sql
  CREATE TABLE hydrated_tweets (
    tweet_id TEXT PRIMARY KEY,
    text TEXT,
    author_id TEXT,
    author_username TEXT,
    created_at TEXT,
    lang TEXT,
    hydrated_at TEXT
  );

  CREATE TABLE author_classification (
    author_id TEXT PRIMARY KEY,
    author_username TEXT,
    classification TEXT CHECK (classification IN ('left', 'right', 'media', 'neutral', 'unknown')),
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    classified_at TEXT,
    classified_by TEXT,  -- 'llm', 'manual', 'llm+manual'
    notes TEXT
  );
  ```

- **Nunca hidratar o mesmo tweet duas vezes.** Antes de qualquer chamada à API, verificar o cache.
- **Custo estimado:** ~US$ 0,03 por tweet × 200 tweets × 4 eventos = ~US$ 24. Esse é o teto. Reaproveitamento entre eventos pode reduzir esse valor.

### 3.3. Classificação dos autores

Para cada autor recuperado pela hidratação:

1. **Primeira passada por LLM.** Enviar ao modelo o handle do autor, o texto do tweet mais retuitado, e pedir classificação em uma das categorias: `left`, `right`, `media`, `neutral`, `unknown`. Solicitar também o nível de confiança e uma justificativa curta.
2. **Revisão manual.** Verificar manualmente, especialmente os casos de baixa confiança ou de classificação ambígua. Editar no cache.
3. **Documentação.** Manter uma planilha de classificações no repositório, com critério explícito por categoria, para incluir como apêndice do TCC.

### 3.4. Score ideológico por usuário

Para cada usuário u do grafo, computar:

```
score(u) = (R_right(u) − R_left(u)) / (R_right(u) + R_left(u))
```

onde `R_right(u)` é o número de retweets de u a tweets cujos autores foram classificados como `right`, e análogo para `left`. Retweets a autores classificados como `media`, `neutral` ou `unknown` não entram no cálculo.

- O score varia de -1 (puramente esquerda) a +1 (puramente direita).
- Usuários com poucos retweets a autores classificados podem ficar sem score; tratar como "indefinido".

### 3.5. Rotulagem dos clusters

- Calcular o score médio (e mediano) dos usuários de cada cluster.
- Cluster com mediana significativamente positiva → rotulado como "predominantemente direita".
- Cluster com mediana significativamente negativa → "predominantemente esquerda".
- Outros → "misto" ou "indefinido".

## 4. Análise narrativa

Para cada par (evento, cluster), produzir uma síntese curta do conteúdo amplificado:

1. **Filtrar os top-50 tweets internos ao cluster.** Pegar os top-N tweets já hidratados (Seção 3.1) e reordenar por contagem de retweets feitos apenas por usuários do cluster.
2. **Sumarização via LLM.** Enviar os 50 textos ao modelo, pedir 3-5 categorias narrativas predominantes e exemplos representativos.
3. **Revisão manual.** Verificar coerência, ajustar categorias, escrever versão final em ~150-200 palavras por par (evento, cluster).
4. **Salvar.** No formato:

   ```json
   {
     "event": "08_janeiro",
     "cluster": "right",
     "narratives": [
       {
         "label": "Infiltração esquerdista",
         "description": "...",
         "example_tweet_ids": [...]
       },
       ...
     ],
     "summary_paragraph": "..."
   }
   ```

## 5. Visualização interativa

### 5.1. Stack

- **Framework:** React (TypeScript recomendado)
- **Renderização de grafo:** Sigma.js (suporta grafos grandes via WebGL; layout precomputado)
- **Estilo:** Tailwind CSS
- **Dados:** arquivos JSON estáticos (gerados pela pipeline), servidos via CDN
- **Hospedagem:** Vercel ou equivalente (gratuito)

### 5.2. Componentes principais

**A. Mapa de grafo**
- Renderização do grafo de cada evento, layout ForceAtlas2 pré-computado (pelo igraph ou Gephi).
- Nós coloridos por cluster ideológico.
- Tamanho do nó proporcional ao grau ponderado.
- Hover em nó: mostra usuário (handle se disponível) e cluster.
- Clique em região do grafo: foca naquela comunidade.

**B. "Habite a bolha" — comparação lado a lado**
- Duas colunas, uma por cluster principal.
- Em cada coluna, os 15 tweets mais retuitados internamente, hidratados.
- Ao lado: a síntese narrativa (Seção 4) do cluster naquele evento.
- Permite seleção de evento via dropdown ou abas.

**C. Filtro temporal (apenas para o 8 de janeiro)**
- Slider de hora controlando opacidade dos nós/arestas conforme a hora de primeira atividade.
- Grafo estrutural fixo; o slider só altera a visualização.
- Painel adjacente: gráfico de linha mostrando modularidade Q calculada por janela de 3h ao longo do dia.

### 5.3. Dados que a visualização consome

Os arquivos JSON gerados pela pipeline (Seção 2.3) são consumidos diretamente. Não há backend dinâmico — todos os dados são pré-computados e servidos como assets estáticos.

## 6. Estrutura sugerida do repositório

```
tcc/
├── README.md
├── data/
│   ├── raw/                    # CSVs originais do dataset
│   ├── processed/              # graphml/pickle por evento
│   └── hydrated.sqlite         # cache de hidratação e classificação
├── pipeline/
│   ├── __init__.py
│   ├── load.py                 # carga e filtragem dos CSVs
│   ├── graph.py                # construção do grafo bipartido + projeção
│   ├── backbone.py             # backbone extraction
│   ├── community.py            # detecção de comunidades + métricas
│   ├── hydrate.py              # hidratação via API + cache
│   ├── classify.py             # classificação de autores via LLM
│   ├── score.py                # cálculo de score ideológico + rotulagem
│   ├── narrative.py            # análise narrativa via LLM
│   └── export.py               # serialização para JSON
├── notebooks/
│   └── exploration.ipynb       # exploração e validação preliminar
├── web/                        # aplicação React
│   ├── src/
│   ├── public/
│   │   └── data/               # JSONs gerados pela pipeline
│   └── package.json
├── docs/
│   ├── 01_visao_projeto.md
│   ├── 02_especificacao_tecnica.md
│   └── 03_decisoes_metodologicas.md
└── scripts/
    └── run_all.py              # roda pipeline completa em todos os eventos
```

## 7. Sequência sugerida de implementação

A ordem importa porque etapas posteriores dependem do que vem antes:

1. **Validação preliminar.** Carregar um arquivo do 8 de janeiro, fazer projeção bipartida sem otimizações, plotar com qualquer ferramenta (Gephi serve), olhar com os olhos se há bimodalidade visível.
2. **Pipeline de grafo (etapas 1-6 da Seção 2.2).** Sem hidratação, sem rotulagem ainda.
3. **Aplicar aos 4 eventos.** Gerar artefatos brutos de grafo.
4. **Pipeline de hidratação + classificação.** Construir cache.
5. **Score ideológico + rotulagem dos clusters.** Reaplicar aos 4 eventos.
6. **Análise narrativa via LLM.**
7. **Aplicação web.** Consumir os JSONs prontos.
8. **Análise de sensibilidade ao threshold.** Documentar no apêndice.

## 8. Critérios de aceitação técnica

A pipeline está pronta quando:

- [ ] Roda end-to-end nos 4 eventos sem intervenção manual entre etapas
- [ ] Produz os 3 artefatos JSON por evento (Seção 2.3)
- [ ] É parametrizada por arquivo de configuração (não hardcoded)
- [ ] Reaproveita cache de hidratação entre eventos
- [ ] Inclui scripts de análise de sensibilidade ao threshold
- [ ] Está documentada com docstrings e um README de uso
- [ ] Os artefatos alimentam a visualização web sem transformação adicional