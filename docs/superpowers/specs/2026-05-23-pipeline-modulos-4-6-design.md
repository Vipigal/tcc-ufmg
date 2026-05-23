# Design — Pipeline de Co-retweet: Módulos 4 a 6

**Data:** 2026-05-23
**Escopo:** Projeção unipartida com peso Jaccard, backbone extraction e detecção de comunidades (Leiden) da pipeline de análise de polarização do TCC.
**Continuação de:** `docs/superpowers/specs/2026-05-23-pipeline-modulos-1-3-design.md`
**Referências:** `docs/especificacao-tecnica.md` (§2.2 passos 4–6), `docs/decisoes-metodologicas.md` (D3, D4).

---

## 1. Contexto e objetivo

Este design cobre os passos 4 a 6 da pipeline, que consomem o `BipartiteGraph` produzido pelo Módulo 3:

4. Projeção da matriz bipartida em grafo unipartido usuário–usuário com peso Jaccard.
5. Backbone extraction por universal threshold.
6. Detecção de comunidades com o algoritmo de Leiden.

O cálculo curado de métricas estruturais (passo 7 da especificação técnica) fica **fora deste escopo**, em um futuro Módulo 7 dedicado, esboçado na §8. Hidratação, score ideológico, análise narrativa e serialização final para o frontend também ficam de fora.

## 2. Princípios de design (herdados do spec 1–3)

Mantidos sem alteração:

- **Operação em memória, persistência opcional** via `.save(out_dir)`.
- **Parâmetros via construtor.**
- **Formato de persistência: Parquet + NPZ**, acrescido de **GraphML** para o grafo do Módulo 6 (formato nativo portável, conforme §2.3 da especificação técnica).
- **Um arquivo `.py` por etapa, uma classe principal por arquivo, na pasta `modules/`.**

## 3. Fluxo de dados

```
BipartiteGraph (B csr, user_index, tweet_index)   ← saída do Módulo 3
   │  modules/project.py    →  JaccardProjector
   ▼
ProjectedGraph (W esparsa simétrica, user_index)
   │  modules/backbone.py   →  BackboneExtractor   (τ)
   ▼
ProjectedGraph (W filtrada, user_index reindexado)
   │  modules/community.py  →  CommunityDetector
   ▼
CommunityResult (igraph.Graph, partition, membership, user_index)
```

Os Módulos 4 e 5 produzem **o mesmo tipo** (`ProjectedGraph`); o backbone é uma transformação da projeção. O `igraph` só entra no Módulo 6.

## 4. Papel do `user_index`

O `user_index` é a tabela de tradução **posição inteira → `author_id` original**. Matrizes esparsas (`scipy`) e grafos (`igraph`) operam com índices inteiros contíguos `0..n-1`; o `user_index`, criado pelo `pd.factorize` no Módulo 3, preserva o ID real de cada posição. Ele atravessa os Módulos 4→5→6 porque:

- a projeção (Módulo 4) produz uma matriz usuário×usuário cujas linhas correspondem às mesmas posições;
- o backbone (Módulo 5) remove nós isolados e **renumera** as posições, exigindo reindexação do `user_index`;
- o Módulo 6 anexa o `user_index` como atributo `user_id` dos vértices, permitindo rastrear cada nó do grafo final de volta ao `author_id`.

O `tweet_index` **não** se propaga além do Módulo 3 (a projeção colapsa a dimensão de tweets); ele serve a um ramo paralelo de hidratação, fora deste escopo.

## 5. Módulo 4 — `modules/project.py` → `JaccardProjector`

**Propósito:** projetar a matriz bipartida em grafo unipartido usuário–usuário com peso Jaccard (D3).

**Interface:**

- `.project(bg: BipartiteGraph) -> ProjectedGraph`.
- `ProjectedGraph` — dataclass com:
  - `W`: `scipy.sparse` **triangular superior** (i < j, sem diagonal), forma `(n_users, n_users)`, peso = Jaccard.
  - `user_index`: repassado do `BipartiteGraph`.
  - `.save(out_dir)`: escreve `projection_W.npz` + `user_index.parquet`.

**Decisões internas:**

- Cálculo vetorizado, sem loop em Python sobre pares (§2.2[4]):
  - `C = B · Bᵀ` — matriz esparsa de interseções `|T_u ∩ T_v|`.
  - `deg = B.sum(axis=1)` — nº de tweets distintos por usuário, `|T_u|`.
  - `J(u,v) = C[u,v] / (deg_u + deg_v − C[u,v])`, calculado apenas sobre os pares com `C > 0`.
- Apenas o triângulo superior é materializado, evitando dupla contagem (grafo não-direcionado).
- A diagonal (`u == v`) é descartada.

**Risco anotado:** `B·Bᵀ` pode gerar muitos pares não-nulos. O filtro de virais (Módulo 2) já removeu colunas densas; nesta versão o cálculo é feito direto, e o risco fica registrado para reavaliação na calibração preliminar (chunking ou poda antecipada, se necessário).

## 6. Módulo 5 — `modules/backbone.py` → `BackboneExtractor`

**Propósito:** universal threshold (D4).

**Interface:**

- `__init__(self, tau=0.1)` — default da especificação técnica.
- `.extract(pg: ProjectedGraph) -> ProjectedGraph`:
  - Mantém apenas as arestas com peso `W ≥ tau`.
  - Descarta nós isolados (sem arestas remanescentes).
  - Reindexa o `user_index` para refletir a nova numeração de posições.
- `.stats` — dict com nº de arestas e de nós antes e depois da extração.
- `.save(out_dir)` — escreve `backbone_W.npz` + `user_index.parquet` + `backbone_stats.json`.

**Decisões internas:**

- A saída é do mesmo tipo `ProjectedGraph`, agora com `W` filtrada e `user_index` reindexado.
- **Análise de sensibilidade (D4, τ = 0,05 e 0,15):** o módulo recebe um único `tau`; a varredura de valores é orquestrada no notebook, coerente com a decisão de calibração via construtor.

## 7. Módulo 6 — `modules/community.py` → `CommunityDetector`

**Propósito:** detecção de comunidades com Leiden (§2.2[6]).

**Interface:**

- `__init__(self, resolution=1.0, objective_function="modularity", n_iterations=-1)`.
- `.detect(pg: ProjectedGraph) -> CommunityResult`:
  - Converte `ProjectedGraph` → `igraph.Graph` não-direcionado ponderado (vértices com atributo `user_id` = `user_index`; arestas com atributo `weight`).
  - Roda `g.community_leiden(weights="weight", objective_function=..., resolution=..., n_iterations=...)`.
- `CommunityResult` — dataclass com:
  - `g`: o `igraph.Graph`, com atributo de vértice `community` preenchido.
  - `partition`: o `VertexClustering` do igraph (dele saem `.modularity` e `.sizes()` triviais).
  - `membership`: lista de comunidade por posição, alinhada ao `user_index`.
  - `user_index`: repassado adiante.
  - `.save(out_dir)`: escreve `community_graph.graphml` (atributos `user_id`, `community`, `weight`) + `membership.parquet`.

**Decisões internas:**

- **`objective_function="modularity"` fixado.** O `community_leiden` do igraph usa `"CPM"` como default, que com resolução 1.0 produz comunidades singleton. Modularidade corresponde ao "reportar modularidade Q" da especificação técnica.
- O Módulo 6 expõe apenas a partição crua; o cálculo curado de métricas é responsabilidade do Módulo 7.
- O GraphML é escolhido como formato de persistência do grafo por ser portável (Gephi, para layout ForceAtlas2 futuro) e carregar atributos de vértice e aresta.

## 8. Esboço do Módulo 7 (fora de escopo, para o próximo spec)

`modules/metrics.py` → `MetricsCalculator`, consumindo `CommunityResult`. Produzirá: modularidade Q, tamanho relativo dos dois maiores clusters, fluxo inter-cluster (soma dos pesos entre os dois maiores clusters / soma total), top-K usuários por degree ponderado em cada cluster, e coeficiente de assortatividade por cluster. Saída prevista: `metrics_<evento>.json`.

## 9. Dependências

A instalar nesta etapa:

- **`python-igraph`** — construção do grafo e `community_leiden` embutido.

**Reconciliação com o spec 1–3:** aquele documento (§8) mencionava instalar "igraph, leidenalg" depois. Como usamos o `community_leiden` embutido do igraph, **`leidenalg` não é necessário**. Não há conflito; este spec apenas precisa a dependência efetiva.

## 10. Uso esperado no notebook (`notebooks/pipeline.ipynb`)

```python
from modules.project import JaccardProjector
from modules.backbone import BackboneExtractor
from modules.community import CommunityDetector

# bg = BipartiteGraph vindo do Módulo 3

pg = JaccardProjector().project(bg)

bb = BackboneExtractor(tau=0.1)
pg_bb = bb.extract(pg)
print(bb.stats)

cd = CommunityDetector(resolution=1.0)
cr = cd.detect(pg_bb)
print("Q =", cr.partition.modularity, "| comunidades:", len(cr.partition))
cr.save(f"data/processed/{EVENT}")
```

## 11. Fora de escopo (4–6)

- Métricas estruturais curadas (Módulo 7).
- Layout ForceAtlas2 e serialização final para Sigma.js (`graph_<evento>.json`).
- Hidratação, classificação, score ideológico, rotulagem de clusters e análise narrativa.
- Arquivo de configuração externo e script `run_all`.
