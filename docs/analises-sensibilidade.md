# Análises de Sensibilidade — calibração de parâmetros

> **Propósito:** registrar todos os testes feitos variando parâmetros da pipeline (N, τ, e
> outros) para, ao final, justificar cada valor escolhido com evidência. Este documento é
> **append-only**: cada rodada de teste vira um bloco datado em "Registro de experimentos";
> nada é apagado. A seção "Decisões de parâmetro" é a síntese viva que aponta para as
> evidências.

> **Evento de referência:** `invasao-3-poderes` (8 de janeiro de 2023), salvo indicação em
> contrário. Os experimentos ainda precisam ser repetidos nos demais eventos.

---

## 1. Métricas usadas

### Modularidade (Q)
Mede a qualidade de **uma** partição em comunidades: a fração do peso das arestas que cai
**dentro** das comunidades menos o que se esperaria se as arestas fossem aleatórias (preservando
os graus). Varia de ≈ −0,5 a 1. Referência usual: **Q ≈ 0** = sem estrutura (aleatório);
**Q > 0,3** = estrutura de comunidades real; **Q > 0,5** = estrutura forte. É a métrica que
responde "existe bolha?".

### ARI — Adjusted Rand Index
Compara **duas partições do mesmo conjunto de nós** (ex.: as comunidades obtidas com N=5 vs.
com N=10, restritas aos usuários comuns).

- **Como funciona:** olha todos os *pares* de nós e conta em quantos as duas partições
  *concordam* — isto é, pares que ficam **juntos** nas duas, ou **separados** nas duas. O Rand
  Index é essa fração de concordância. O ARI **corrige pelo acaso** (duas partições aleatórias
  já concordariam em alguns pares por sorte), subtraindo a concordância esperada.
- **Escala:** **1,0** = partições idênticas; **0** = concordância no nível do acaso; pode ser
  ligeiramente **negativo** (pior que o acaso).
- **Como se encaixa aqui:** é a régua para perguntar "mudar o parâmetro reorganiza as
  comunidades?". Comparamos a partição em um valor de parâmetro com a de outro, nos nós comuns.
  ARI alto = estrutura estável (mudar o parâmetro custou pouco em estrutura). **Cuidado:** o ARI
  precisa ser lido contra o **piso de ruído** (ver abaixo), porque o próprio Leiden tem
  aleatoriedade.

### NMI — Normalized Mutual Information
Também compara duas partições, por teoria da informação: "saber a comunidade de um nó em uma
partição reduz quanto a incerteza sobre a comunidade dele na outra?". Normalizada para **[0, 1]**:
**1** = idênticas, **0** = independentes. Complementar ao ARI (erram de formas diferentes; se
concordam, dá confiança).

### VI — Variation of Information
Distância entre duas partições: **0 = idênticas**, quanto maior, mais diferentes (direção oposta
ao ARI/NMI). Útil como verificação cruzada.

### Piso de ruído do Leiden
O Leiden é estocástico: rodá-lo duas vezes no **mesmo** grafo já dá ARI < 1. Antes de interpretar
qualquer ARI/NMI entre parâmetros, medimos esse piso (mesmo grafo, duas execuções). Se o piso é
≈ 1, diferenças abaixo dele são **reais**; se o piso já é baixo, a variação observada pode ser só
ruído do algoritmo.

---

## 2. Parâmetros sob calibração

| Parâmetro | O que é | Default atual | Status |
|---|---|---|---|
| **N** | mín. de retweets para um usuário virar nó (filtro M2) | 10 | **em aberto** (representatividade) |
| **τ** | peso Jaccard mínimo da aresta (backbone, embutido em M4) | 0,10 | provisório; sensibilidade 0,05/0,15 pendente |
| **resolution** | resolução do Leiden (M5) | 1,0 | controla a granularidade dos macroblocos (E6); não gera as comunidades pequenas |
| **block_size** | usuários por bloco na projeção | 2000 | técnico (memória), não metodológico |

---

## 3. Registro de experimentos

### E1 — Explosão de arestas por limiar τ (N=3) · 2026-06-18
**Método:** projeção em blocos sobre `bipartite_B` (N=3: 85.087 usuários, 24.104 tweets),
contando arestas por faixa de Jaccard sem materializar a matriz (memória segura).

| Faixa | Arestas (triângulo superior) |
|---|---|
| Pares candidatos (≥ 1 tweet em comum) | 436.558.846 |
| J ≥ 0,05 | 271.367.189 |
| J ≥ 0,10 | 125.541.899 |
| J ≥ 0,15 | 44.769.871 |

**Leitura:** com N=3 o grafo é intratável em qualquer τ (125M arestas em τ=0,10). Como o filtro
M2 garante grau ≥ 3, dois usuários grau-3 que compartilham 1 tweet popular têm J = 1/(3+3−1) =
0,2 — sobrevivem até a τ=0,15. O limiar sozinho não resolve a escala; o lever é o N.

### E2 — Varredura de N: nós e arestas · 2026-06-18
**Método:** para cada N, filtrar usuários por grau e contar arestas (em blocos) em τ=0,10 e 0,15.
*Proxy:* grau = nº de tweets distintos (o filtro real do M2 conta ações), então a contagem de nós
fica um pouco abaixo da real (ex.: N=3 dá 85.085 aqui vs. 85.087 no M2). Ordem de magnitude
idêntica.

| N | nós | arestas J≥0,10 | arestas J≥0,15 |
|---|---|---|---|
| 3 | 85.085 | 125.533.242 | 44.763.942 |
| 5 | 48.342 | 27.052.420 | 6.706.721 |
| 10 | 22.217 | 5.661.890 | 951.223 |
| 15 | 13.323 | 2.605.419 | 371.629 |
| 20 | 8.960 | 1.545.276 | 219.206 |

**Leitura:** N é o que torna o grafo tratável de ponta a ponta (Leiden, disco, visualização).
N=10 é o "joelho da curva": ~22k nós, ~5,7M arestas em τ=0,10 — processável e renderizável.

### E3 — Volume de retweets capturado por cada N-core · 2026-06-18
**Método:** soma das ações (retweets) dos usuários que sobrevivem a cada N, sobre `filtered_retweets`.

| N | usuários | % usuários | retweets | % do bruto (1.100.026) | % do pós-M2, N≥3 (813.100) |
|---|---|---|---|---|---|
| 3 | 85.087 | 100,0% | 813.100 | 73,9% | 100,0% |
| 5 | 48.342 | 56,8% | 689.283 | 62,7% | 84,8% |
| 10 | 22.217 | 26,1% | 520.582 | 47,3% | 64,0% |
| 15 | 13.323 | 15,7% | 416.765 | 37,9% | 51,3% |
| 20 | 8.960 | 10,5% | 343.593 | 31,2% | 42,3% |

**Leitura:** a concentração é moderada, não extrema. Em N=10, 26% dos usuários concentram 47%
de todos os retweets (64% do universo pós-M2). Os descartados não são cauda desprezível — fazem
~metade da amplificação. "Mantivemos quem amplifica" vale bem para N≤5; em N=10 mantemos ~metade.

### E4 — Estabilidade da estrutura de comunidades ao variar N · 2026-06-18
**Método:** para cada N, construir o grafo (τ=0,10), rodar Leiden, comparar as partições nos
**usuários comuns** via ARI/NMI/VI. Diagnóstico pontual (não usa a pipeline de produção).

**Piso de ruído** (mesmo grafo N=10, duas execuções do Leiden): **NMI = 0,997 · ARI = 0,999.**
O Leiden é praticamente determinístico aqui — qualquer ARI abaixo disso é diferença real.

| Comparação | nós comuns | NMI | ARI | VI |
|---|---|---|---|---|
| N=10 vs N=10 (ruído) | 22.097 | 0,997 | 0,999 | — |
| N=15 vs N=20 | 8.811 | 0,963 | 0,978 | 0,056 |
| N=10 vs N=15 | 13.171 | 0,815 | 0,785 | 0,322 |
| N=10 vs N=20 | 8.811 | 0,801 | 0,786 | 0,351 |
| N=5 vs N=10 | 22.097 | 0,702 | 0,759 | — |

**Leitura:** subir N **muda a estrutura de verdade** (ARI 0,759 entre N=5 e N=10, contra piso de
0,999). A instabilidade cresce conforme se desce o N (15↔20 ≈ estável; 5↔10 muda bastante), o que
sugere que os usuários de baixa atividade são os estruturalmente ambíguos (sinal fraco) —
argumento *a favor* de N maior. **Ressalva:** o ARI cheio mistura a macroestrutura (as 2–3
grandes bolhas, o que interessa) com a mesoestrutura (subcomunidades pequenas). Falta o teste no
nível macro (ver Pendências).

### E5 — Resultado estrutural no ponto N=10, τ=0,10 · 2026-06-18
**Método:** execução completa da pipeline (M1–M5) no ponto de trabalho atual.

- Nós: **22.097** · Arestas: **5.661.890** · **Modularidade Q = 0,5034** (estrutura forte).
- 14 comunidades, 3 dominantes (99,8% dos nós): com1 = 47%, com0 = 34%, com2 = 19%.
- **85,6% do peso das arestas é interno às comunidades**; 14,4% entre elas.
- Fluxo entre os 3 maiores blocos (% do peso total):

|  | com1 | com0 | com2 |
|---|---|---|---|
| **com1** | 44,6% | 0,01% | 0,00% |
| **com0** | 0,01% | 20,4% | 8,8% |
| **com2** | 0,00% | 5,6% | 20,6% |

**Leitura:** a maior comunidade (com1) é hermeticamente isolada das demais (fluxo ~0); com0 e
com2 trocam algum peso entre si. Retrato clássico de polarização. *Rótulos esquerda/direita só
saem da classificação ideológica (módulo ainda não construído) — por ora é estrutura pura.*

> **⚠ Correção (E8, 2026-06-19):** a matriz de fluxo acima está **assimétrica** (com0→com2 = 8,8%
> mas com2→com0 = 5,6%) por um artefato de cálculo, não da estrutura — o grafo é não-direcionado e
> esses dois números têm de ser iguais. A versão simétrica está em **E8**: o fluxo real com0↔com2
> é **14,4%** (= 8,8 + 5,6). A diagonal e as demais leituras de E5 seguem válidas.

### E6 — Sensibilidade à `resolution` do Leiden (N=10, τ=0,10) · 2026-06-19
**Motivação:** a partição N=10 produz 3 grandes blocos + ~11 comunidades minúsculas. Pergunta
levantada: essas comunidades extras seriam um artefato de `resolution=1,0` (parâmetro mal
calibrado)?
**Método:** Leiden no mesmo backbone N=10, variando `resolution`; medir nº de comunidades, nº com
≥ 10 nós, tamanho dos 3 maiores (% nós), Q e ARI contra a partição-base (resolution = 1,0).

| resolution | nº com. | com. ≥ 10 nós | top-3 (% nós) | Q | ARI vs base |
|---|---|---|---|---|---|
| 1,0 (base) | 14 | 3 | [47, 34, 19] | 0,503 | 0,999 |
| 0,7 | 11 | 3 | [53, 47, **0**] | 0,646 | 0,743 |
| 0,5 | 6 | 2 | [53, 47, 0] | 0,747 | 0,742 |
| 0,3 | 4 | 2 | [53, 47, 0] | 0,848 | 0,742 |
| 0,1 | 4 | 2 | [53, 47, 0] | 0,949 | 0,742 |

**Observação:** ao baixar `resolution`, a primeira mudança (já em 0,7) é **com0 (34%) e com2 (19%)
se fundirem** num bloco de 53% — os dois blocos que trocam fluxo entre si (E8) — e o ARI cai para
~0,74 (vs piso 0,999): reorganização **macro**. As comunidades minúsculas, por outro lado,
persistem ao longo do intervalo testado.

**Apontamento (contexto desta rodada):** a `resolution` controla a granularidade dos *grandes*
blocos, não o aparecimento das comunidades pequenas — então estas não aparentam ser artefato do
default 1,0; macroblocos e micro-comunidades vivem em escalas de granularidade diferentes. Leitura
a revisitar se N ou τ mudarem.

### E7 — Natureza das comunidades marginais (N=10) · 2026-06-19
**Pergunta:** qual a natureza dessas ~11 comunidades minúsculas — componentes desconexos (cliques
soltas) ou sub-clusters dentro do componente gigante?
**Método:** componentes conexos do backbone (scipy) + attachment de cada comunidade pequena (a
quem suas arestas externas se ligam).

- **Componentes conexos: 2.** Gigante = **22.095 nós (99,99%)**; só **1 par (2 nós)** fica de fora.
- Logo, **10 das 11 comunidades pequenas estão 100% dentro do componente gigante** — são bolsões
  densos (cliques pequenas, ex.: 5 nós com 7 arestas internas), **não** fragmentos desconexos.
- **Attachment:** a maioria liga-se predominantemente a um bloco (ex.: →com1 ou →com0), mas algumas
  são genuinamente ponte (ex.: clique de 8 com 6 arestas p/ com1, 4 p/ com0, 1 p/ com2).

**Apontamento (contexto desta rodada):** essas comunidades não são desconexas nem artefato de
resolução (E6) — são estruturas pequenas, densas e reais (cliques de co-retweet) fraca ou
ambiguamente presas aos grandes blocos. *O que* elas representam (micro-grupos coordenados?
comunidades de nicho? contas com repertório muito específico?) é uma pergunta de interpretação
social/política a explorar com os dados hidratados — observação a registrar, não estrutura a
descartar de antemão.

### E8 — Correção e leitura da matriz de fluxo entre comunidades · 2026-06-19
**Bug encontrado:** a matriz de fluxo de E5 (e do `relatorio-diagnostico`) é assimétrica
(com0→com2 = 8,8% ≠ com2→com0 = 5,6%) num grafo **não-direcionado**, onde têm de ser iguais.
**Causa raiz:** a projeção grava `W` **triangular superior** (`project.py`: `upper = user_j >
user_i`) — cada aresta aparece 1× orientada pelo índice do nó, arbitrário em relação à comunidade.
O cálculo da matriz jogava cada aresta numa única célula `(com[src], com[dst])`, partindo o
**único** fluxo com0↔com2 entre as duas células off-diagonal. Reproduzido no run N=10: célula a
célula dá 8,78 / 5,63; `8,78 + 5,63 = 14,41`.
**Correção:** simetrizar — `S = M + Mᵀ − diag(M)` (cada ponte conta dos dois lados). A diagonal
(intra-comunidade) já estava correta, então **as conclusões de E5 seguem de pé**; só a apresentação
off-diagonal muda. Matriz N=10 corrigida (% do peso total):

|  | com1 | com0 | com2 |
|---|---|---|---|
| **com1** | 44,6% | 0,01% | 0,01% |
| **com0** | 0,01% | 20,3% | **14,4%** |
| **com2** | 0,01% | **14,4%** | 20,7% |

**Implementação:** célula nova em `notebooks/pipeline.ipynb` (antes da limpeza) plota essa matriz
simetrizada a cada run (heatmap, com as comunidades pequenas agregadas numa faixa "outras").

**Leitura aprofundada (o "0%" não é zero literal):** o desconforto com "com1 troca 0% com as
outras" é justo. Decompondo as arestas que cruzam (snapshot do run N=7 atual; as ordens de
magnitude são estáveis entre re-execuções):

| par | nº de arestas | % do peso | J máx |
|---|---|---|---|
| com1 ↔ com0 | ~3,2 mil | 0,02% | 0,27 |
| com1 ↔ com2 | ~2,0 mil | 0,02% | 0,25 |
| **com0 ↔ com2** | **~2 milhões** | **16,5%** | 0,75 |

1. **Não é zero literal:** com1 tem ~5 mil arestas-ponte; mas valem ~0,04% do peso → arredonda a 0.
   "0%" = 0% do **peso de co-amplificação**, não "nunca viram o mesmo tweet".
2. **A história real é o contraste:** com0 e com2 são fortemente pontilhadas (16,5%, ~2M arestas);
   é **especificamente a com1** o polo isolado. Não são "3 ilhas" — é 1 polo + 1 região conectada.
3. **As pontes de com1 são fracas** (J ~0,12, colado no piso τ=0,10), contra arestas internas até 1,0.

**Ressalva metodológica:** parte do isolamento absoluto é **efeito do backbone** — o corte τ=0,10
remove laços fracos por construção (D4), amplificando a separação. Ler como estrutural/relativo, não
absoluto; reforça a necessidade da sensibilidade a τ (ver Pendências).
*(Ponto de trabalho atual migrou para N=7: 33.305 nós, 12,0M arestas, Q = 0,498, mesma estrutura de
3 blocos — a correção e a leitura valem igual.)*

---

## 4. Decisões de parâmetro (síntese viva)

| Parâmetro | Valor (provisório) | Justificativa | Evidência | Status |
|---|---|---|---|---|
| **N** | 10 (candidato) | tratável ponta a ponta e estrutura forte; mas descarta ~metade do volume e altera a partição vs. N menores | E2, E3, E4, E5 | **em aberto** — pende teste macro + representatividade |
| **τ** | 0,10 | corta ligações fracas; análise de sensibilidade exigida | E1 | provisório — falta rodar 0,05/0,15 com métricas estruturais |
| **resolution** | 1,0 | default do Leiden; E6 indica que controla a granularidade dos macroblocos, não o nº de comunidades pequenas | E6 | mantido no default; sem evidência que peça mudança |
| **block_size** | 2000 | pico de memória ~1 GB em N=10 | E5 (~13s, ~1 GB) | técnico, ok |

---

## 5. Pendências

- [ ] **Teste de estabilidade macro** (N=5 vs N=10): colapsar cada partição em {maior, 2ª maior,
      resto} e comparar nos nós comuns — verifica se as grandes bolhas são estáveis mesmo quando a
      partição fina muda.
- [ ] **Sensibilidade completa a τ** (0,05 / 0,10 / 0,15) no N escolhido, reportando Q, tamanho
      relativo dos 2 maiores clusters e fluxo inter-cluster.
- [x] **Sensibilidade à `resolution`** do Leiden — feito (E6): controla a granularidade dos
      macroblocos; as comunidades pequenas são estrutura à parte (E7), não artefato de resolução.
- [ ] **Caracterizar as comunidades pequenas** (E7) com os dados hidratados, pela ótica de
      computação social/política — o que são esses micro-clusters? (observação, não descarte).
- [ ] **Regerar a matriz de fluxo simetrizada** no `relatorio-diagnostico` com os números do N
      escolhido (ver E8); a célula nova do notebook já produz a versão correta a cada run.
- [ ] **Validar N contra a classificação ideológica** quando o módulo existir (a macroestrutura
      esquerda/direita deve ser estável no N escolhido).
- [ ] **Repetir E2–E5 nos outros três eventos** (7/9, Roberto Jefferson, debate da democracia).
