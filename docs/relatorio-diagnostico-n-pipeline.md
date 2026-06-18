# Relatório de diagnóstico — calibração de N e execução da pipeline (evento 8 de janeiro)

> **Evento:** `invasao-3-poderes` (ataques de 8 de janeiro de 2023).
> **Data do relatório:** 2026-06-18.
> **Escopo:** (1) diagnóstico da escolha do parâmetro N (mínimo de retweets por usuário); (2) diagnóstico da execução completa da pipeline de grafo (M1–M6) com N=10, τ=0,10.

---

## 1. Resumo executivo

- A projeção de co-retweet com N=3 é **intratável** (≈125M de arestas em τ=0,10). O lever de tratabilidade é **N**, não o limiar τ.
- Com **N=10, τ=0,10**, a pipeline roda ponta a ponta e produz um grafo de **22.097 nós e 5,66M arestas**.
- O grafo tem **estrutura de comunidades forte (modularidade Q = 0,50)**: três blocos dominam (47% / 34% / 19% dos nós), **85,6% do peso é interno às comunidades**, e a maior comunidade é **hermeticamente isolada** das demais (fluxo ~0,01%). É o retrato esperado de polarização/câmara de eco.
- Subir N **muda a estrutura de comunidades de forma real** (não é ruído de algoritmo), então a escolha de N é metodologicamente relevante e ainda exige uma validação no **nível macro** (esquerda×direita) — pendente.

---

## 2. Métricas usadas (glossário)

- **Leiden** — algoritmo que divide o grafo em **comunidades** (grupos densamente conectados por dentro, esparsos entre si), maximizando a modularidade.
- **Modularidade (Q)** — quão "fechadas" são as comunidades. ~0 = sem estrutura (aleatório); >0,3 = estrutura real; >0,5 = forte.
- **ARI (Adjusted Rand Index)** — concordância entre **duas divisões dos mesmos nós**: 1 = idênticas, 0 = nível do acaso (corrige para a sorte).
- **NMI (Normalized Mutual Information)** — concordância entre duas divisões por teoria da informação: 1 = idênticas, 0 = independentes.
- **VI (Variation of Information)** — *distância* entre duas divisões: 0 = idênticas, maior = mais diferentes.

---

## 3. Diagnóstico de N

### 3.1. Volume de retweets capturado por cada N-core

Pergunta: ao subir N descartamos muitos usuários — mas eles importam para a amplificação?

| N | usuários | % usuários | retweets | % do bruto | % do pós-M2(N≥3) |
|---|---|---|---|---|---|
| 3 | 85.087 | 100% | 813.100 | 73,9% | 100% |
| 5 | 48.342 | 56,8% | 689.283 | 62,7% | 84,8% |
| 10 | 22.217 | 26,1% | 520.582 | 47,3% | 64,0% |
| 15 | 13.323 | 15,7% | 416.765 | 37,9% | 51,3% |
| 20 | 8.960 | 10,5% | 343.593 | 31,2% | 42,3% |

**Leitura:** a concentração é moderada, não extrema. Em N=10, 26% dos usuários concentram 47% de todos os retweets (64% do universo já filtrado por N≥3). Os usuários descartados **não** são uma cauda desprezível — fazem ~metade da amplificação. O argumento "mantivemos quem amplifica" vale bem para N≤5; em N=10 mantemos ~metade.

### 3.2. Estabilidade da estrutura de comunidades ao variar N

Método: para cada N, construir o grafo de co-retweet (τ=0,10), rodar Leiden, e comparar as partições nos **usuários comuns** via ARI/NMI/VI. Comparações feitas como diagnóstico pontual (não dependem de a pipeline de produção ser eficiente).

**Piso de ruído** (mesmo grafo N=10, duas rodadas de Leiden): **ARI = 0,999, NMI = 0,997.** O Leiden é praticamente determinístico aqui — então qualquer ARI abaixo disso é diferença real, não ruído.

| Comparação | nós comuns | NMI | ARI |
|---|---|---|---|
| N=10 vs N=10 (ruído) | 22.097 | 0,997 | 0,999 |
| N=15 vs N=20 | 8.811 | 0,963 | 0,978 |
| N=10 vs N=15 | 13.171 | 0,815 | 0,785 |
| N=10 vs N=20 | 8.811 | 0,801 | 0,786 |
| N=5 vs N=10 | 22.097 | 0,702 | 0,759 |

**Leituras:**
1. **Subir N muda a estrutura de verdade.** ARI 0,759 (N=5 vs N=10) contra um piso de ruído de 0,999 é uma diferença substancial — não é artefato do algoritmo.
2. **A instabilidade cresce conforme se desce o N** (15↔20: 0,978; 10↔15: 0,785; 5↔10: 0,759). Cada banda de atividade mais baixa adicionada mexe mais na partição. Isso sugere que os usuários de baixa atividade são os **estruturalmente ambíguos** (sinal de co-retweet fraco → comunidade mal-definida) — um argumento *a favor* de N mais alto.
3. **Ressalva:** o ARI cheio mistura a **macroestrutura** (as 2–3 grandes bolhas, que é o que interessa) com a **mesoestrutura** (subcomunidades pequenas). A reorganização pode estar concentrada nas comunidades pequenas, com a bipartição macro estável. **Teste decisivo pendente:** colapsar cada partição em {maior, 2ª maior, resto} e comparar nos nós comuns. A validação definitiva de representatividade virá da classificação ideológica (esquerda/direita), ainda não construída.

---

## 4. Diagnóstico da pipeline completa (N=10, τ=0,10)

### 4.1. Afunilamento por estágio

| Estágio | Resultado |
|---|---|
| M1 carga | 1.100.026 retweets |
| M2 filtro N≥10 | 520.582 ações · 22.217 usuários · 19.386 tweets |
| M3 bipartida | matriz 22.217 × 19.386 |
| M4 projeção (todas as arestas, J>0) | **80.536.314** arestas |
| M5 backbone (J ≥ 0,10) | **5.661.890** arestas · 22.097 nós (120 nós ficaram isolados e saíram) |
| M6 Leiden | 14 comunidades · **Q = 0,5034** |

### 4.2. Artefatos gerados e o que representam

| Arquivo | Módulo | Conteúdo | Tamanho |
|---|---|---|---|
| `retweets.parquet` | M1 | Retweets (autor → tweet referenciado) | 16M |
| `filtered_retweets.parquet` | M2 | Retweets após filtro de usuário (N≥10) | 3,1M |
| `bipartite_B.npz` (+ índices) | M3 | Matriz esparsa usuário×tweet | ~1,5M |
| `projection_W.npz` (+ índice) | M4 | Grafo de co-retweet completo (80,5M arestas), peso Jaccard | 236M |
| `backbone_W.npz` (+ índice) | M5 | Grafo após corte τ=0,10 (5,66M arestas) | 18M |
| `backbone_stats.json` | M5 | Contagens antes/depois do corte | — |
| `community_graph.graphml` | M6 | Grafo + comunidade por nó (formato XML) | 560M |
| `membership.parquet` | M6 | **Saída-chave**: usuário → comunidade | 345K |
| `filter_stats.json` | M2 | Contagens do filtro | — |

### 4.3. Estrutura de comunidades

- **Modularidade Q = 0,50** → estrutura forte; há bolhas reais.
- Três comunidades dominam (99,8% dos nós): com1 = 10.387 (47%), com0 = 7.541 (34%), com2 = 4.128 (19%). As outras 11 são resíduo (<0,2%).
- **85,6% do peso das arestas é interno às comunidades; 14,4% entre elas.**
- Matriz de fluxo (% do peso total) entre os três grandes blocos:

|  | com1 | com0 | com2 |
|---|---|---|---|
| **com1** | 44,6% | 0,01% | 0,00% |
| **com0** | 0,01% | 20,4% | 8,8% |
| **com2** | 0,00% | 5,6% | 20,6% |

**Leitura:** a maior comunidade (com1, 47%) está **hermeticamente isolada** das demais (fluxo ~0). com0 e com2 trocam algum peso entre si (~14%), mas são fechadas para com1. É o retrato clássico de polarização: blocos densos por dentro, quase sem pontes entre o maior e o resto.

**Ressalva de interpretação:** os rótulos "esquerda/direita" só surgem da **classificação ideológica** (não construída ainda). Até lá, esta é estrutura pura — há ~3 bolhas e a maior é totalmente isolada, mas não se sabe *qual* é qual. O contexto do evento sugere hipóteses, mas não substitui a rotulagem.

---

## 5. Pendências e recomendações

1. **Decisão de N (metodológica, em aberto).** N=10 entrega grafo tratável e estrutura forte, mas descarta ~metade do volume de retweets e muda a partição em relação a N menores. Falta o **teste de estabilidade no nível macro** (Seção 3.2, ponto 3) e, idealmente, validar contra a classificação ideológica. Considerar a representatividade junto ao restante da metodologia.
2. **Otimização do M4 ainda vale.** A projeção guardou 80,5M arestas (236M em disco) das quais o backbone manteve só 5,66M. Implementar a projeção em blocos com corte em `τ_floor` (≈0,05) reduz disco e memória drasticamente e é necessária para N menor / eventos maiores.
3. **`community_graph.graphml` (560M) é desperdício.** Todo o conteúdo já está em `backbone_W.npz` + `membership.parquet`. Recomenda-se descontinuar o graphml ou trocar por formato binário; e revisar a construção do grafo igraph no M6 para grandes volumes.
