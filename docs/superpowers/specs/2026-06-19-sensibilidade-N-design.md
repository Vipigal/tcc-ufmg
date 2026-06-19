# Design — Análise de sensibilidade do parâmetro N (metade estrutural)

**Data:** 2026-06-19
**Escopo:** Calibração empírica do parâmetro **N** (mínimo de retweets por usuário, filtro M2) do pipeline de co-retweet, na sua **dimensão estrutural** — se e como a macroestrutura de comunidades depende de N. A dimensão **ideológica** (qual N separa esquerda/direita mais nítido) fica fora: depende da classificação por hidratação, ainda não construída.
**Evento de referência:** `invasao-3-poderes` (8 de janeiro de 2023).
**Referências:** `docs/analises-sensibilidade.md` (E1–E8), `docs/relatorio-diagnostico-n-pipeline.md`, `docs/analise-explosao-projecao-m4.md`, `docs/decisoes-metodologicas.md` (D4, D5, D14), `docs/especificacao-tecnica.md` (§2.2). Módulos: `modules/{filter,bipartite,project,community}.py`.

---

## 1. Contexto e objetivo

N é "o parâmetro mais frágil da pipeline" (D5): governa sozinho a tratabilidade (E1, E2) e descarta usuários de baixa atividade. O trade-off já está medido:

- **N≤3:** cobertura máxima, grafo intratável (~125M arestas em τ=0,10).
- **N=5:** tratável, mas perde ~37% do volume de retweets (E3).
- **N≥7:** confortável computacionalmente (ponto de trabalho atual: N=7), mas resta a dúvida de **representatividade**.

A pergunta de fundo, nas palavras do autor: *os usuários de retweets menos ativos alteram a macroestrutura das comunidades de forma relevante? Ou N maior mantém a mesma base estrutural, apenas com um filtro mais nítido? De que forma a estrutura muda com N?*

O E4 já mostrou que a partição **completa** muda de verdade com N (ARI 0,759 entre N=5 e N=10, contra piso de ruído 0,999) — mas o ARI cheio **mistura macroestrutura (as 2–3 grandes bolhas, que interessam) com mesoestrutura (subcomunidades pequenas)**. Este design fecha exatamente essa lacuna: separar o que é reorganização macro do que é ruído meso, e caracterizar o papel da periferia.

## 2. Pergunta e hipóteses

- **H0 (representatividade resolvida no nível que importa):** a macroestrutura é **invariante a N**. Operacionalmente: (a) os usuários do núcleo comum mantêm seu macro-polo quando N muda; (b) cada N produz nativamente o mesmo número de super-polos dominantes. Se confirmada → N é knob de tratabilidade/nitidez, não de substância.
- **H1 (estrutura N-dependente):** usuários migram de polo, ou o número de polos muda com N. Se confirmada → a escolha de N é decisão de primeira ordem e exige investigar a periferia.

## 3. O que adotamos e o que corrigimos do handoff anterior

Registrado para rastreabilidade da decisão metodológica.

**Adotado:** dois eixos ortogonais (resolução, feita em E6; N, este design); fixar τ=0,10 para isolar N; colapsar para rótulo macro e comparar só no **núcleo comum**; ARI/NMI (invariantes a permutação) + matriz de confusão alinhada; ancorar no **piso de ruído** do Leiden.

**Corrigido (4 pontos):**

1. **Não rodar Leiden em `resolution=0,5`.** O E6 mostra que γ=0,5 só produz 2 polos porque **funde com0+com2** (custo ARI 0,74 vs a partição nativa γ=1,0). Testar a estabilidade dessa bipartição *imposta pelo knob* é circular, e vicia o readout (b) ("cada N rende 2 polos?" — claro que sim, se você sintoniza γ para isso). **Correção:** rodar o Leiden na resolução **de produção (γ=1,0)** e derivar o rótulo macro por **colapso pós-hoc transparente**, mantendo a detecção fixa. O γ=0,5 vira **check de sanidade** do colapso L2, não método primário.
2. **Não usar `{maior, 2ª maior, resíduo}`.** Em N=10 nativo os tamanhos são [47, 34, 19, …]; essa regra jogaria **com2 (19%)** no resíduo, sendo com2 um bloco grande. O rótulo macro precisa acomodar o número real de blocos dominantes.
3. **Não pré-assumir 2 polos.** A leitura honesta do E8 é *"1 polo isolado (com1) + 1 região conectada (com0↔com2, ~16,5% de fluxo)"*. Rastreamos **dois níveis** (3 blocos nativos **e** 2 super-polos por fluxo) e testamos a estabilidade de cada — sem impor o número.
4. **Núcleo comum = interseção dos backbones, não "todos os usuários de N_hi".** Ver §4.2.

## 4. Setup comum

### 4.1. Grid e parâmetros

- **Métricas completas:** N ∈ **{5, 7, 10, 15, 20}**. (N=7 é o ponto de trabalho atual; N=5 é o limite inferior tratável; N=10 era o candidato anterior; N=15/20 são âncoras de estabilidade.)
- **Só contagens:** N=3 (E2/E3 já medidos; Leiden em ~125M arestas não compensa e não muda a leitura). Reportado na trajetória como linha sem Q/partição.
- **Fixos:** τ=0,10; `resolution=1,0`; `objective_function="modularity"`; `block_size=2000`.

### 4.2. Reuso da pipeline de produção e isolamento de saída

- **Reuso, não reimplementação.** O script chama os módulos reais — `NoiseFilter(N).apply` → `BipartiteBuilder().build` → `JaccardProjector(tau=0.10).project` → `CommunityDetector(resolution=1.0).detect` — para que o teste reflita o pipeline real (corrige a ressalva do E4, que usou diagnóstico pontual). `retweets.parquet` (M1) é **independente de N** e é carregado uma vez.
- **Isolamento.** Os módulos de produção persistem em `data/processed/<evento>/` com nomes fixos; rodar o grid sobrescreveria os artefatos N=7 em uso. **Logo, o grid roda em memória** (chamando os métodos `apply/build/project/detect` diretamente, sem o cache de `Stage.run`), persistindo apenas saídas **compactas por N** num diretório dedicado de análise. Os artefatos de produção (`graph_*.parquet` em N=7) ficam intactos.

### 4.3. Corolário que sustenta a interpretação (registrar no relatório)

Para um usuário que sobrevive ao filtro em qualquer N, o conjunto `T_u` (tweets que ele retuitou) é **idêntico** entre Ns — todo tweet que ele retuitou tem ao menos um retweetador sobrevivente (ele mesmo), logo nenhuma coluna dele some. Como `J(u,v)` depende só de `T_u, T_v`, **as arestas internas ao núcleo comum têm peso idêntico entre Ns**. Portanto o que reorganiza a partição do núcleo ao baixar N **não é o peso das arestas dele** — é a **periferia adicionada** mudando o cenário global de otimização da modularidade. Isso explica *por que* N mexe na estrutura e motiva a Peça 3.

**Consequência para o núcleo comum (corrige o handoff):** embora o filtro de usuário seja monotônico (N_hi ⊂ N_lo no nível de usuário), o **backbone** não é: um usuário ≥15 pode sobreviver em N=10 e ficar **isolado/removido** em N=15 (perdeu o único vizinho J≥τ, de atividade menor, presente só em N=10). O núcleo comum correto é a **interseção dos conjuntos de nós dos dois backbones**, não "todos os usuários de N_hi".

## 5. Peça 1 — Trajetória estrutural (descritiva)

*Responde "de que forma a estrutura muda com N".* Por N do grid completo, reportar:

- nº de nós e arestas (confirmação cruzada com E2);
- **modularidade Q**;
- nº total de comunidades; nº de **blocos dominantes** (≥1% dos nós) e seus tamanhos relativos (top-4);
- **% de peso intra-comunidade** (coesão);
- **matriz de fluxo simetrizada** entre blocos dominantes — método do E8: `S = M + Mᵀ − diag(M)`, normalizada pelo peso total; em especial, o polo isolado continua isolado? a região conectada persiste?
- **massa de fronteira:** distribuição do *participation coefficient* `P_i = 1 − Σ_c (k_{i,c}/k_i)²` (k = grau ponderado; c sobre blocos macro), que mede quão espalhado entre comunidades está o peso de cada nó.

**Saídas:** tabela por N; curvas Q vs N e nº de blocos vs N; heatmaps de fluxo por N.

## 6. Peça 2 — Estabilidade macro (confirmatória)

*Responde "altera a estrutura ou só filtra".* Rótulo macro derivado da partição **nativa γ=1,0**, em dois níveis:

- **L3 (blocos nativos):** os blocos dominantes (≥1% dos nós) mantêm sua identidade por tamanho; o resíduo (<1%) é **categoria própria** (não atribuído a um bloco).
- **L2 (super-polos por fluxo):** a partir da matriz de fluxo simetrizada entre blocos dominantes, definir "blocos co-amplificadores" — par de blocos cujo fluxo mútuo ≥ `θ_flow × min(peso interno dos dois)`. Os super-polos são os **componentes conexos** dos blocos dominantes sob essa relação. `θ_flow` é calibrado para que em N=10 o resultado reproduza `{com1} | {com0, com2}` (leitura do E8) e **bata com o split de γ=0,5 do E6** (check de sanidade). O **número de super-polos é determinado pelos dados**, não forçado em 2 — assim o readout (b) é informativo. Reportar sensibilidade a `θ_flow`.

**Comparação entre Ns.** Para cada par (N_hi, N_lo):

- núcleo comum = **interseção dos nós dos dois backbones** (§4.2);
- **ARI, NMI, VI** sobre L3 e sobre L2, restritos ao núcleo comum (invariantes a permutação — dispensam alinhamento);
- **matriz de confusão** após **alinhamento guloso por sobreposição máxima** (k×k; guloso resolve k pequeno); reportar **taxa de concordância** (soma da diagonal / total) e off-diagonal;
- **piso de ruído** por N: duas execuções do Leiden no mesmo grafo, ARI/NMI entre elas (E4 já deu 0,999 em N=10; refazer por N para calibrar cada comparação).

**Readouts.** (a) concordância macro alta (>0,9; off-diagonal <10%) em **todos** os pares? (b) o número de super-polos é o mesmo em **todo** N? Se (a)∧(b) → **H0**. Se a concordância degrada ao descer N, ou o nº de super-polos muda → **H1**.

## 7. Peça 3 — Faixa incremental (representatividade direta)

*Responde "o que os usuários menos ativos fazem".* Para cada degrau adjacente (20→15, 15→10, 10→7, 7→5):

- **faixa incremental** = usuários presentes no backbone de N_lo e **ausentes** no de N_hi (os que entram ao afrouxar o filtro);
- no grafo de N_lo (onde existem), medir:
  - **(i) distribuição de macro-polo** (L2) da faixa vs a do núcleo — enviesam para um polo ou se espalham nas mesmas proporções? (comparação de proporções / χ²);
  - **(ii) fronteira:** *participation coefficient* da faixa vs o do núcleo — são mais "ponte"? borram a fronteira?
  - **(iii) estrutura nova:** quanto da massa de comunidades não-dominantes (resíduo) a faixa explica? algum bloco dominante novo aparece por causa dela?
  - **(iv) atividade:** grau ponderado médio (confirma que são de baixa atividade).

**Leitura:** faixa que se encaixa nos polos existentes, nas mesmas proporções, sem virar ponte → leitura B (N é nitidez). Faixa que borra fronteiras / cria estrutura → leitura A (altera a macro).

## 8. Síntese e regra de decisão

Cruzar as evidências numa recomendação de N:

| Eixo | Fonte | Pergunta |
|---|---|---|
| Tratabilidade | E2 | grafo roda ponta a ponta? |
| Volume | E3 | quanto retweet se perde? |
| Estabilidade macro | Peça 2 | a bipartição/tripartição é robusta a N? |
| Periferia | Peça 3 | os menos ativos alteram ou só adensam? |
| Trajetória | Peça 1 | Q, nº de blocos, fluxo, fronteira vs N |

**Regra:** se H0 vale (P2 + P3 indicam que a macro é robusta e a periferia se encaixa), N pode ser escolhido **pelo eixo de tratabilidade/volume** com tranquilidade metodológica (favorece o menor N tratável que ainda dê estrutura forte). Se H1 vale, a escolha de N vira decisão de primeira ordem, com sensibilidade documentada e investigação da periferia. **Ressalva obrigatória:** esta é a metade estrutural; o N escolhido **deve ser revalidado contra a classificação ideológica** quando o módulo de hidratação existir.

## 9. Entregáveis

1. **`docs/analises-sensibilidade.md`** — novo(s) bloco(s) datado(s) **E9+** no formato append-only existente (E9 trajetória, E10 macro, E11 faixa incremental, ou agrupados); atualizar a tabela "Decisões de parâmetro" (síntese viva) e marcar as pendências cobertas como `[x]`.
2. **`docs/relatorio-sensibilidade-N.md`** — relatório standalone espelhando `relatorio-diagnostico-n-pipeline.md`: resumo executivo, método, resultados das 3 peças, recomendação, ressalvas.
3. **`assets/`** — plots: Q vs N, nº de blocos vs N, heatmaps de fluxo por N, matriz de confusão macro, distribuição de polo da faixa incremental.
4. **`scripts/sensitivity_N.py`** — script reproduzível que gera tudo (importa `modules/*`, roda o grid em memória, persiste saídas compactas + plots). Reprodutibilidade importa para a defesa.

## 10. Entregável diferido — HTML de resultados (banner)

**Após** concluir os entregáveis 1–4, criar um artefato HTML com as visualizações dos resultados, interpretações e o progresso geral do TCC até aqui. Motivação: o autor precisa montar um **banner de resultados em ~2 dias** (deadline ~2026-06-21). Fica como tarefa final, deliberadamente separada para não consumir contexto durante a análise.

## 11. Fora de escopo e ressalvas

- **Metade ideológica de N** (separação esquerda/direita) — depende da hidratação/classificação, não construída. É a outra metade da decisão e fica explicitamente pendente.
- **Sensibilidade a τ** (0,05/0,10/0,15) — pendência separada em `analises-sensibilidade.md`; aqui τ fica fixo em 0,10 para isolar N.
- **Repetição nos outros 3 eventos** — este design roda no 8 de janeiro; a generalização aos demais eventos é trabalho posterior.
- **N=3 com Leiden completo** — intratável e desnecessário; entra só nas contagens.

## 12. Abordagem de implementação

- **Forma:** script único `scripts/sensitivity_N.py`, parametrizado por evento e grid no topo. Funções puras por peça (`structural_trajectory`, `macro_stability`, `incremental_tier`) + um `main` que orquestra e escreve artefatos.
- **Saídas compactas por N:** `data/processed/<evento>/sensitivity/N{n}_nodes.parquet` (user_id, community) + `N{n}_metrics.json`. Edges grandes (N=5 ~27M) ficam em scratch, não committados.
- **Orçamento de compute:** N=5 é o run mais pesado (~27M arestas, Leiden); E4 já o rodou — viável. Grid completo estimado em alguns minutos por N. Memória dominada pela projeção em blocos (pico ~1 GB em N=10; maior em N=5, dentro do tratável).
- **Validação cruzada:** confirmar que nós/arestas por N batem com E2 e que N=7 reproduz os stats em disco (33.305 nós, 12,0M arestas, Q≈0,498) antes de confiar nas peças seguintes.
