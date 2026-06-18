# Análise — Explosão de arestas na projeção de co-retweet (Módulo 4)

> **Status:** análise concluída; decisão metodológica de calibração (valor de N) **em aberto**.
> **Objetivo deste documento:** registrar o problema, o que foi medido experimentalmente, e as opções de solução discutidas, para orientar a implementação posterior.
> **Data:** 2026-06-17.

## 1. Contexto

O Módulo 4 da pipeline projeta a matriz bipartida usuário × tweet (`B`) em um grafo unipartido usuário × usuário, onde o peso de cada aresta é o índice de **Jaccard** entre os conjuntos de tweets retuitados por cada par de usuários:

```
J(u, v) = |T_u ∩ T_v| / |T_u ∪ T_v|
```

A implementação inicial calcula `C = B · Bᵀ` (matriz de interseções) de uma vez e depois converte para Jaccard. O Módulo 5 (backbone) em seguida descarta toda aresta com `J < τ` (τ inicial = 0,10), e o Módulo 6 roda Leiden sobre o que sobra.

## 2. O problema

`C = B · Bᵀ` materializa, de uma só vez, **uma aresta para cada par de usuários que compartilha ao menos um tweet**. Cada tweet retuitado por `k` usuários gera `C(k, 2)` pares — crescimento quadrático na popularidade do tweet. Em escala real isso estoura a memória (OOM) antes mesmo de chegar ao backbone.

Ponto crucial: o backbone descarta >99% dessas arestas logo em seguida. Ou seja, a implementação atual **gasta toda a memória construindo arestas que são imediatamente jogadas fora**.

## 3. Dados do evento de teste (`invasao-3-poderes`)

Após Módulo 1 (carga de retweets) e Módulo 2 (filtro de usuários com < N=3 retweets; **sem** filtro de tweets virais — ver D5):

| Métrica | Valor |
|---|---|
| Usuários (nós em potencial) | 85.087 |
| Tweets distintos retuitados | 24.104 |
| Retweets (não-zeros em `B`) | 813.089 |
| Popularidade de tweet (máx / média / p99) | 9.201 / 33,7 / 676 |
| Atividade por usuário, em tweets distintos (máx / média / p99) | 385 / 9,6 / 67 |

**Observação importante sobre representatividade.** No stream bruto, o tweet mais retuitado tinha ~22.976 retweets. Após o filtro de usuários (N≥3), esse mesmo tweet aparece com **9.201** retuitadores. A queda **não** vem de cortar tweets (o filtro viral foi removido), e sim do filtro de **usuários**: ao remover ~74% dos usuários (os de baixa atividade), todo tweet popular perde esses retuitadores. Subir N continua corroendo a contagem efetiva de retweets de cada tweet.

## 4. O que medimos experimentalmente

### 4.1. Quantas arestas a projeção gera, e quantas sobrevivem ao limiar

Rodando a projeção **em blocos** (para medir sem estourar a memória) e contando as arestas do triângulo superior por faixa de Jaccard, com N=3:

| Faixa | Arestas |
|---|---|
| Pares candidatos (≥ 1 tweet em comum) | **436.558.846** |
| J ≥ 0,05 | **271.367.189** |
| J ≥ 0,10 | **125.541.899** |
| J ≥ 0,15 | **44.769.871** |

**O limiar sozinho não resolve.** Como o Módulo 2 garante que todo usuário tem grau ≥ 3, dois usuários de grau 3 que compartilham **um único** tweet popular têm `J = 1/(3+3−1) = 0,2` — sobrevive folgado a τ = 0,05, 0,10 e até 0,15. Um tweet com milhares de retuitadores de grau baixo ainda gera dezenas de milhões de arestas que passam o limiar. O custo de **cálculo** é inevitável (≈ Σ pop² ≈ 1,2 bilhão de incidências par×tweet; isso é só CPU, ~1 min), mas o número de arestas **sobreviventes** permanece grande.

### 4.2. Efeito do parâmetro N (mínimo de retweets por usuário)

O número de sobreviventes — e portanto a viabilidade de todo o resto da pipeline — é governado principalmente por **N**, não pelo τ:

| N | nós | arestas J≥0,10 | arestas J≥0,15 |
|---|---|---|---|
| 3 | 85.085 | 125,5M | 44,8M |
| 5 | 48.342 | 27,0M | 6,7M |
| 10 | 22.217 | **5,7M** | 951k |
| 15 | 13.323 | 2,6M | 372k |
| 20 | 8.960 | 1,5M | 219k |

*(Proxy de medição: grau = nº de tweets distintos; o filtro real do M2 conta ações, então a contagem real de nós fica um pouco acima. A ordem de magnitude se mantém.)*

## 5. A questão de fundo (decisão em aberto)

O particionamento em blocos resolve o OOM **da etapa de cálculo**, mas **não** a escala do resultado. O número de arestas sobreviventes governa tudo a jusante:

- **Disco:** um grafo de centenas de milhões de arestas ocupa vários GB serializado.
- **Leiden (M6):** carrega o grafo inteiro em memória; com 125M de arestas, sofre o mesmo problema.
- **Visualização (Sigma.js/WebGL):** não renderiza milhões de arestas.

Logo, **o que torna a pipeline viável de ponta a ponta é a escolha de N**, e essa é uma decisão metodológica, não técnica. O trade-off:

- **N baixo (ex.: 3)** → máxima cobertura de usuários, grafo intratável.
- **N alto (ex.: 10–15)** → grafo tratável e visualizável, mas restrito ao "núcleo engajado" (com N=10, ~26% dos usuários).

**A pergunta a responder antes de implementar:** a amostra que sobra após subir N ainda é **representativa** para a pergunta de pesquisa (como comunidades de esquerda e direita amplificaram narrativas)? Há uma tensão real: o sinal de co-retweet vem de tweets compartilhados, e subir N reduz quantos usuários compartilham cada tweet — ou seja, mexe na própria fonte do sinal. Vale checar a literatura sobre construção de redes de co-retweet / co-sharing e os critérios de filtragem usados (qual N/threshold é típico, como justificam a representatividade).

## 6. Opções de solução discutidas

### 6.1. Projeção em blocos (técnico — necessário em qualquer cenário)

Em vez de `C = B · Bᵀ` inteiro, processar por blocos de usuários:

```
para cada bloco de linhas [a:b]:
    C_blk = B[a:b] · Bᵀ            # (block_size × n_users), esparso
    converte para COO; calcula Jaccard das entradas não-zero
    mantém triângulo superior (col > linha global) e J ≥ τ_floor
    acumula (ou grava) os sobreviventes
monta W final a partir dos sobreviventes
```

`block_size` limita o pico de memória do `C_blk` transitório (sugestão: parâmetro com default ~2000). O custo de CPU é o mesmo; o ganho é nunca segurar a matriz inteira de uma vez.

Esboço de medição/cálculo usado nos experimentos (reproduzível):

```python
import numpy as np, scipy.sparse as sp

B  = sp.load_npz('.../bipartite_B.npz').astype(np.int32).tocsr()
BT = B.T.tocsr()
deg = np.asarray(B.sum(axis=1)).ravel().astype(np.int64)
n = B.shape[0]

block = 2000
for a in range(0, n, block):
    b = min(a + block, n)
    C = (B[a:b] @ BT).tocoo()
    gr = C.row + a
    m = C.col > gr                       # triângulo superior
    r, c = gr[m], C.col[m]
    inter = C.data[m].astype(np.int64)
    jac = inter / (deg[r] + deg[c] - inter)
    keep = jac >= TAU_FLOOR
    # ... acumular (r[keep], c[keep], jac[keep]) ...
```

### 6.2. Embutir o limiar na projeção (técnico — preserva análise de sensibilidade)

Em vez de a projeção gerar todas as arestas e o backbone cortar depois, a projeção já corta em um **`τ_floor`** (sugestão: 0,05, o menor τ da análise de sensibilidade). O backbone (M5) continua um estágio separado, apenas **estreitando** de `τ_floor` para o τ real (0,10) — barato, sem reprojetar. Assim:

- A análise de sensibilidade (τ = 0,05 / 0,10 / 0,15) roda variando só o M5, sem refazer a projeção.
- Resultado idêntico ao da pipeline original para qualquer τ ≥ τ_floor.

### 6.3. Calibração de N (metodológico — decisão em aberto, ver Seção 5)

O lever de tratabilidade. Precisa da reflexão sobre representatividade antes de fixar. Candidatos plausíveis pela tabela: N na faixa 10–15.

### 6.4. Storage dos sobreviventes (técnico — depende de N)

- Se N for escolhido de modo que o grafo seja pequeno (ex.: N=10 → poucos M de arestas), basta **acumular em memória** e salvar como `.npz` (dezenas de MB). Carga em memória no M6 é tranquila.
- Se for necessário rodar com N baixo (grafo grande), seria preciso **gravar sobreviventes por bloco em arquivos intermediários** (parquet) e montar `W` no final — mas isso só adia o problema, porque o M6 e a visualização não suportam o volume. Reforça que N é a decisão central.

### 6.5. Alternativas mais pesadas (consideradas, não recomendadas para o TCC)

- **Backbone por disparity filter** (Serrano et al., 2009) em vez de limiar universal: poda arestas considerando a heterogeneidade de grau de cada nó, o que poderia preservar mais usuários cortando as arestas espúrias de forma diferente. A metodologia (D4) optou pelo limiar universal pela simplicidade, mas isto é uma alternativa real caso se queira manter N baixo. Aumenta a complexidade de justificativa.
- **Jaccard aproximado via MinHash/LSH:** escala melhor para achar pares de alta similaridade sem materializar todos os pares, ao custo de erro de aproximação e bastante complexidade adicional. Provavelmente desproporcional para um TCC.

## 7. Resumo / próximos passos

1. **Decidir N** (metodológico) — pendente de estudo de representatividade. É o que destrava o resto.
2. **Reescrever o M4** com projeção em blocos (6.1) + corte em `τ_floor` (6.2). Isso é seguro e necessário independentemente do N.
3. **Storage** conforme o N escolhido (6.4).
4. **Revisar o M6** se o grafo, mesmo após N, tiver muitos milhões de arestas: a construção atual do grafo igraph via `list(zip(...))` é ineficiente para esse volume e deve usar arrays.
