# RASCUNHO DA PROPOSTA — TCC

## 1. Capa

**Título proposto** (três opções, escolhe a que te soa melhor):

A. *Bolhas em colisão: análise comparativa e visualização interativa das comunidades políticas no Twitter brasileiro em torno dos ataques de 8 de janeiro de 2023*

B. *Duas realidades, um mesmo fato: análise de bolhas de eco no Twitter brasileiro durante eventos políticos de 2022 e 2023*

C. *Como dois lados enxergam o mesmo evento: análise estrutural e visualização das comunidades polarizadas no Twitter brasileiro durante o 8 de janeiro de 2023*

**Tipo de Pesquisa:** Mista (científica e tecnológica). A frente científica corresponde à análise quantitativa de redes sociais e à comparação de métricas estruturais entre eventos; a frente tecnológica corresponde ao desenvolvimento de uma pipeline computacional reutilizável e de uma aplicação web interativa para visualização dos resultados.

**Orientadora:** Eliane

**Coorientador:** não há

---

## 2. Introdução

### 2.1. Problema e justificativa

A polarização política nas redes sociais é um fenômeno bem documentado, e o Brasil viveu uma das suas manifestações mais intensas no ciclo eleitoral de 2022 e seu desdobramento em 8 de janeiro de 2023, quando apoiadores do ex-presidente Jair Bolsonaro invadiram as sedes dos três poderes em Brasília. O Twitter (atualmente X) foi um dos canais centrais em que esse processo se manifestou publicamente, servindo simultaneamente como meio de mobilização, de disseminação de narrativas e de formação de opinião.

Este trabalho parte de uma observação simples e bastante reconhecível por qualquer usuário de redes sociais brasileiro: dois usuários do Twitter, expostos ao mesmo evento político, podem ter experiências de leitura completamente diferentes da realidade. Um pode ver linhas do tempo dominadas por mensagens descrevendo o 8 de janeiro como um ataque à democracia; o outro pode ver linhas do tempo dominadas por mensagens descrevendo o mesmo evento como uma manifestação patriótica infiltrada por agentes da esquerda. Essa divergência informacional não é apenas uma curiosidade — ela tem efeitos diretos sobre como o debate público se organiza e sobre a possibilidade de consenso mínimo sobre o que aconteceu.

O problema que este trabalho aborda é, portanto: **como caracterizar e tornar visível, de forma defensável e replicável, a divergência informacional entre comunidades políticas opostas no Twitter brasileiro em torno do 8 de janeiro de 2023?**

A importância do problema é tripla. Em primeiro lugar, há uma motivação técnica: a análise estruturada de grafos de retweet é uma aplicação concreta de conceitos centrais da computação (estruturas de dados em grafos, algoritmos de detecção de comunidade, projeções bipartidas, processamento de grandes volumes de dados), aplicada a um problema do mundo real. Em segundo lugar, há uma motivação social: tornar visível a estrutura das bolhas pode ajudar leitores não-técnicos a compreender melhor sua própria exposição informacional. Em terceiro lugar, há uma motivação de delimitação: ao escolher um evento polarizador específico e bem documentado, é possível conduzir uma análise focada e factível dentro do escopo de um TCC, sem precisar resolver o problema geral da polarização nas redes.

### 2.2. Pergunta central

*Como apoiadores de esquerda e de direita no Twitter brasileiro construíram e amplificaram narrativas distintas sobre o mesmo evento — os ataques de 8 de janeiro de 2023 — e como essa divergência pode ser tornada visível e navegável para um leitor?*

### 2.3. Objetivo geral

Caracterizar a estrutura das comunidades políticas no Twitter brasileiro em torno do 8 de janeiro de 2023, e desenvolver uma visualização interativa que torne essa estrutura compreensível para um público não-técnico, usando como dataset os tweets coletados por Silva et al. (2024).

### 2.4. Objetivos específicos

1. Desenvolver uma pipeline computacional reutilizável que receba como entrada um arquivo do dataset Silva et al. (2024) e produza como saída um grafo de co-retweet com comunidades detectadas e métricas estruturais associadas.

2. Aplicar essa pipeline a quatro eventos políticos do dataset, escolhidos por compor um arco narrativo que culmina no 8 de janeiro: a mobilização de 7 de setembro de 2022, o caso Roberto Jefferson (outubro de 2022), o debate sobre democracia no dia do segundo turno (30 de outubro de 2022) e os ataques de 8 de janeiro de 2023.

3. Hidratar seletivamente um conjunto reduzido de tweets originais mais retuitados em cada evento para permitir a classificação manual de fontes ideológicas e a caracterização das narrativas predominantes em cada comunidade.

4. Construir uma aplicação web interativa que permita a um leitor explorar os grafos resultantes, comparar lado a lado os tweets dominantes em cada comunidade, e observar a evolução temporal do grafo do 8 de janeiro ao longo do dia.

5. Documentar criticamente as limitações metodológicas da abordagem, incluindo o que o grafo de co-retweet permite e não permite afirmar.

---

## 3. Referencial Teórico

### 3.1. Bolhas de eco e câmaras de eco

O termo *filter bubble*, popularizado por Pariser (2011), descreve o efeito da personalização algorítmica em criar ambientes informacionais individualizados que limitam a exposição a perspectivas divergentes. Sunstein (2017) trabalha o conceito complementar de *echo chambers*, enfatizando o componente de autossegregação voluntária dos usuários, não apenas o algorítmico. Bruns (2019) apresenta um contraponto importante, argumentando que as evidências empíricas das bolhas são mais fracas do que o discurso popular sugere, e que o grau de hermetismo varia significativamente por plataforma e contexto. Bail et al. (2018) acrescentam um paradoxo relevante: a exposição a conteúdo de visão oposta pode, em certos casos, aumentar a polarização em vez de reduzi-la.

Este trabalho adota uma postura intencionalmente moderada nessa discussão: a existência de bolhas não é tratada como hipótese a ser provada, mas como ferramenta de leitura para entender como comunidades distintas processam o mesmo evento. O foco está na visualização da divergência observável, não em afirmações fortes sobre causalidade algorítmica.

### 3.2. Análise de polarização em redes de retweet

Conover et al. (2011) estabeleceram que redes de retweet refletem alinhamento ideológico de forma mais fiel do que redes de menção ou reply — retweet funciona como proxy de endosso, enquanto menções frequentemente representam confronto. Essa distinção justifica a escolha deste trabalho de construir o grafo exclusivamente sobre retweets. Garimella et al. (2018) propuseram o *Random Walk Controversy score* (RWC) como métrica para quantificar polarização em grafos bipartidos, baseado na probabilidade de que um random walk iniciado em uma comunidade permaneça nela.

No contexto brasileiro, Recuero et al. (2019) aplicaram análise de redes sociais para identificar papéis de usuários em conversas polarizadas no Twitter. Silva et al. (2024) desenvolveram o pipeline de coleta que originou o dataset utilizado neste trabalho. Bastos e Recuero (2023) analisaram especificamente as narrativas que sustentaram a tentativa de insurreição de 8 de janeiro, com foco em pronunciamentos de parlamentares. Ozawa et al. (2024) analisaram a interação entre WhatsApp, Twitter e mídia jornalística no mesmo evento, com técnicas de modelagem de tópicos.

### 3.3. Co-retweet networks e projeções bipartidas

A construção clássica de uma rede de retweet — em que uma aresta dirigida liga o usuário A ao usuário B se A retuitou B — exige conhecer o autor original do tweet retuitado. No dataset Silva et al. (2024), essa informação não está disponível diretamente, porque o dataset preserva apenas o ID do tweet referenciado, e não o ID de seu autor. Recuperar o autor exigiria hidratação massiva via API, com custo proibitivo para o escopo deste trabalho.

A alternativa adotada é a construção de uma *co-retweet network*, em que dois usuários são ligados por uma aresta se compartilham retweets de tweets em comum. Formalmente, trata-se de uma projeção unipartida de uma rede bipartida usuário-tweet. Essa abordagem foi utilizada, entre outros, por Tien et al. (2020) para analisar a polarização em torno do evento de Charlottesville, por Pena et al. (2025) para o referendo do aborto irlandês, e em estudo recente sobre a eleição americana de 2020 publicado em *Frontiers in Political Science*. A justificativa metodológica é direta: usuários que amplificam consistentemente o mesmo material habitam o mesmo ambiente informacional, mesmo que não interajam diretamente entre si.

Projeções bipartidas tendem a gerar redes densas e ruidosas, problema bem reconhecido na literatura (Neal et al., 2021). A solução padrão é a aplicação de uma técnica de *backbone extraction*, que mantém apenas as arestas estatisticamente mais significativas. Este trabalho adota um *universal threshold* sobre o peso de Jaccard como técnica de backbone, por sua simplicidade e adequação ao escopo de um TCC.

### 3.4. Limitações reconhecidas pela literatura

Duas limitações importantes da abordagem precisam ser registradas desde já. Em primeiro lugar, Guerra et al. (2017), trabalhando com datasets brasileiros do Twitter sobre política e futebol, demonstraram empiricamente que comunidades antagônicas podem retweetar umas às outras com frequência alta — seja por citação irônica, exposição ao ridículo ou contestação direta. Isso questiona a premissa simples de que retweet equivale a endosso. Em segundo lugar, Rao et al. (2022) mostraram que grafos de retweet tendem a *superestimar* o efeito de câmara de eco em comparação com grafos baseados em relações de following. Ambas as limitações serão explicitadas e discutidas como ressalvas da análise, não como problemas a serem resolvidos no escopo deste trabalho.

---

## 4. Metodologia

### 4.1. Dataset

O trabalho utiliza o dataset Tweet_Eleições_2022 (Silva et al., 2024), disponível publicamente no Zenodo sob licença CC-BY 4.0. O dataset contém aproximadamente 9,47 milhões de tweets coletados entre abril de 2022 e janeiro de 2023, organizados em 110 arquivos por evento político. O dataset está desidratado por razões éticas; cada registro contém apenas: data de criação, ID do autor da ação, ID da conversa, e campo `referenced_tweets` com o ID e o tipo de tweet referenciado (retweeted, replied_to, quoted).

Quatro eventos foram selecionados para análise, escolhidos por compor um arco narrativo de tensionamento institucional progressivo:

| Evento | Pasta no dataset | Volume aproximado |
|---|---|---|
| Mobilização do 7 de setembro de 2022 | `0709_mobilizacao` | ~242 mil tweets |
| Caso Roberto Jefferson (out/2022) | `2310_robertojefferson_*` (4 arquivos) | ~966 mil tweets |
| Debate "democracia" no 2º turno (30/10/2022) | `3010_democracia` | ~299 mil tweets |
| Ataques de 8 de janeiro de 2023 | `0801_invasao_*` e `0901_invasao_*` (7 arquivos) | ~1,23 milhão de tweets |

### 4.2. Construção do grafo de co-retweet

Para cada evento, a pipeline executa os seguintes passos:

1. **Filtragem.** Carregar o(s) arquivo(s) CSV do evento; selecionar apenas registros com `type=retweeted`; descartar usuários que aparecem como retweetadores menos de N vezes no evento (N a ser definido empiricamente, candidato inicial N=3).

2. **Filtragem de tweets virais espúrios.** Descartar tweets que foram retuitados por uma fração muito grande do grafo, sob a hipótese de que tweets retuitados por todos os lados carregam pouca informação ideológica e funcionam como ruído. Critério inicial: tweets retuitados por mais de 30% dos usuários do evento. Este parâmetro será revisitado após a validação preliminar (seção 4.5).

3. **Construção da bipartida.** Montar uma matriz esparsa B de dimensões (usuários × tweets), com B[u,t] = 1 se o usuário u retuitou o tweet t no evento, 0 caso contrário.

4. **Projeção unipartida com peso Jaccard.** Para cada par (u, v) de usuários, calcular o peso da aresta como J(u,v) = |T_u ∩ T_v| / |T_u ∪ T_v|, onde T_u é o conjunto de tweets retuitados pelo usuário u. Pares com peso zero não geram aresta.

5. **Backbone extraction via universal threshold.** Reter apenas arestas com J(u,v) ≥ τ. O valor inicial proposto é τ = 0,1, com análise de sensibilidade documentada no apêndice (rodar a pipeline também com τ = 0,05 e τ = 0,15 para verificar robustez).

6. **Detecção de comunidades.** Aplicar o algoritmo de Leiden sobre o grafo resultante. Reportar modularidade Q, número de comunidades, tamanho relativo das duas maiores comunidades, e fluxo de arestas entre elas.

### 4.3. Rotulagem ideológica dos clusters

A rotulagem dos clusters em "esquerda", "direita", "neutro" ou outras categorias é feita em três passos:

1. **Ranking dos tweets mais retuitados.** Para cada evento, agregar o campo `referenced_tweets` por ID de tweet e contar quantas vezes cada tweet foi retuitado dentro do dataset. Selecionar os top-200 tweets por evento.

2. **Hidratação via API do X.** Recuperar o texto e o autor desses 200 tweets via endpoint `/2/tweets`. Custo estimado: $0,03 por lookup × 200 tweets × 4 eventos ≈ $24 no total. Os autores recuperados são salvos em um cache local, permitindo reaproveitamento entre eventos quando o mesmo autor aparece.

3. **Classificação manual + LLM das fontes.** Para cada autor recuperado, atribuir uma das categorias: esquerda, direita, mídia jornalística institucional, neutro/indefinido. Um modelo de linguagem (LLM) será usado para uma primeira passada de classificação automática a partir do texto do tweet e do handle do autor; a classificação será revisada manualmente. Os critérios e a planilha de classificação serão incluídos como apêndice.

4. **Cálculo do score ideológico por usuário.** Para cada usuário u do grafo, computar:

   ```
   score(u) = (R_dir(u) − R_esq(u)) / (R_dir(u) + R_esq(u))
   ```

   onde R_dir(u) é o número de retweets de u a tweets de autores classificados como direita, e análogo para esquerda. O score varia entre −1 e +1.

5. **Rotulagem do cluster.** Cada cluster detectado pelo Leiden é rotulado como "predominantemente direita", "predominantemente esquerda" ou "misto" com base no score médio de seus membros.

### 4.4. Análise narrativa por cluster

Para cada um dos dois principais clusters de cada evento, selecionar os top-50 tweets originais mais retuitados *internamente* àquele cluster (filtrando o ranking de retweets pelos retweets feitos por usuários daquele cluster). Esses 50 tweets já estão hidratados dentre os 200 do passo anterior — sem chamada extra à API. Para cada conjunto de 50 tweets, fazer uma análise qualitativa de enquadramento: usar o LLM para sugerir 3 a 5 categorias narrativas predominantes, revisar manualmente e produzir uma síntese curta de "o que esse cluster amplificou neste evento". O produto é, para cada par (evento, cluster), uma página descritiva curta com exemplos.

### 4.5. Validação metodológica preliminar

Antes de aplicar a pipeline aos quatro eventos, será realizada uma validação preliminar em um único arquivo do 8 de janeiro (provavelmente `0801_invasao-18hr-21hr`, por ser o de maior volume). O objetivo é verificar empiricamente se a estrutura bimodal emerge de forma visível, ou se ajustes adicionais nos filtros são necessários. Os resultados dessa validação serão documentados no TCC como apêndice e justificarão eventuais ajustes nos parâmetros default (N, threshold de tweets virais, τ do backbone).

### 4.6. Visualização interativa

A entrega final do trabalho inclui uma aplicação web desenvolvida em React, hospedada publicamente, com três componentes principais:

- **Mapa de grafo**: visualização do grafo de cada evento, com nós coloridos por cluster e tamanho proporcional ao grau ponderado, layout ForceAtlas2 pré-computado e renderização via Sigma.js.

- **"Habite a bolha"**: para cada evento e cada cluster, uma lista lado a lado dos 15 tweets mais retuitados internamente, permitindo ao leitor comparar diretamente o que cada comunidade amplificou.

- **Filtro temporal (apenas para o 8 de janeiro)**: slider de hora que controla a opacidade dos nós e arestas conforme a janela horária em que o usuário esteve ativo. O grafo é estático, mas a visualização revela como a rede se preenche ao longo do dia. Um painel adicional mostra a modularidade Q calculada por janela de 3 horas, indicando se a polarização cresce, decresce ou permanece estável durante o evento.

### 4.7. Stack técnica

| Camada | Ferramenta |
|---|---|
| Processamento de dados | Python, pandas |
| Construção e análise de grafos | igraph |
| Detecção de comunidades | Leiden (via igraph) |
| Hidratação | API v2 do X, requests, cache local em SQLite |
| Classificação assistida | API de LLM (Claude ou equivalente) |
| Layout do grafo | ForceAtlas2 (precomputado) |
| Frontend | React, Sigma.js, Tailwind |
| Hospedagem | Vercel ou similar |

### 4.8. Limitações da metodologia

Cinco limitações são explicitadas e discutidas no TCC:

1. **Co-retweet ≠ fluxo de influência.** O grafo mede similaridade de consumo, não cadeia causal.
2. **Viés de seleção do dataset.** A análise reconstrói apenas a bolha de quem participou da conversa filtrada por keywords de Silva et al. (2024).
3. **Retweet ≠ endosso (Guerra et al., 2017).** Possibilidade de retweets antagônicos não tratada explicitamente; será discutida em uma seção dedicada do TCC.
4. **Twitter ≠ ecossistema digital completo.** A literatura indica que parte significativa da organização do 8 de janeiro ocorreu em WhatsApp e Telegram, fora do escopo deste trabalho.
5. **Hidratação parcial.** Contas suspensas ou tweets deletados após janeiro de 2023 não poderão ser recuperados, e a taxa de perda pode ser assimétrica entre comunidades.

---

## 5. Resultados Esperados

Ao final do trabalho, espera-se ter produzido:

- **Quatro grafos** correspondentes aos eventos selecionados, com clusters detectados, métricas estruturais (modularidade, tamanho relativo, fluxo inter-cluster) e listas dos usuários mais centrais em cada cluster.

- **Uma tabela comparativa** das métricas entre os quatro eventos, permitindo observar se a polarização medida varia significativamente ao longo do ciclo eleitoral. A hipótese de trabalho é que a polarização cresce do 7 de setembro até o 8 de janeiro, mas o resultado pode contrariar essa expectativa, o que seria igualmente interessante.

- **Caracterização narrativa** de cada cluster em cada evento, com 3 a 5 categorias de enquadramento identificadas e exemplos de tweets representativos.

- **Pipeline computacional documentada** em Python, parametrizada, capaz de ser aplicada a outros arquivos do dataset (ou potencialmente a outros datasets em formato similar).

- **Aplicação web pública** que permita a qualquer leitor explorar os grafos, comparar bolhas e visualizar a evolução temporal do 8 de janeiro.

- **Documento do TCC** descrevendo o método, os resultados, as limitações e as discussões pertinentes.

Não se pretende afirmar que este trabalho descobre fenômenos inéditos sobre o 8 de janeiro — a literatura recente (Bastos & Recuero, 2023; Ozawa et al., 2024) já abordou o evento por outros ângulos. A contribuição esperada é instrumental: oferecer uma visualização clara e navegável de algo que tende a ser discutido em termos abstratos, e demonstrar a aplicação de técnicas computacionais consolidadas a um problema social concreto.

---

## 6. Etapas e Cronograma

Cronograma assumindo entrega da proposta no fim de maio de 2026 e defesa final em novembro de 2026 (24 semanas):

| Semanas | Período | Atividade |
|---|---|---|
| 1–2 | Jun/2026 | Validação metodológica preliminar (um arquivo do 8 de janeiro); ajuste de parâmetros default |
| 3–6 | Jun–Jul/2026 | Implementação da pipeline (parsing, projeção bipartida, backbone, detecção de comunidades, métricas) |
| 7–10 | Jul–Ago/2026 | Aplicação da pipeline aos 4 eventos; geração dos grafos e métricas; análise de sensibilidade ao threshold |
| 11–12 | Ago/2026 | Hidratação dos top-200 por evento; cache de autores |
| 13–14 | Set/2026 | Classificação manual e via LLM das fontes; cálculo dos scores ideológicos; rotulagem dos clusters |
| 15–16 | Set/2026 | Análise narrativa por cluster (top-50 internos, enquadramentos) |
| 17–20 | Out/2026 | Desenvolvimento da aplicação web (mapa, "habite a bolha", filtro temporal) |
| 21–22 | Out–Nov/2026 | Redação do documento final do TCC |
| 23 | Nov/2026 | Revisão, ajustes finais, preparação de apresentação |
| 24 | Nov/2026 | Defesa |

Há folga de aproximadamente 2 semanas distribuídas ao longo do cronograma para imprevistos, em particular durante a hidratação (caso a API apresente limitações inesperadas) e durante o desenvolvimento web.

---

## 7. Referências Bibliográficas (lista parcial)

- Bail, C. A. et al. (2018). Exposure to Opposing Views on Social Media Can Increase Political Polarization. *PNAS*, 115(37), 9216–9221.
- Bastos, M. T. & Recuero, R. (2023). The Insurrectionist Playbook: Jair Bolsonaro and the National Congress of Brazil. *Social Media + Society*, 9(4).
- Bruns, A. (2019). *Are Filter Bubbles Real?* Polity Press.
- Conover, M. D. et al. (2011). Political Polarization on Twitter. *Proceedings of ICWSM*.
- Garimella, K. et al. (2018). Quantifying Controversy on Social Media. *ACM Transactions on Social Computing*, 1(1).
- Guerra, P. C. et al. (2017). Antagonism also Flows through Retweets: The Impact of Out-of-Context Quotes in Opinion Polarization Analysis. *Proceedings of ICWSM*.
- Neal, Z. P. et al. (2021). Comparing alternatives to the fixed degree sequence model for extracting the backbone of bipartite projections. *Scientific Reports*.
- Ozawa, J. V. S., Lukito, J., Bailez, F. & Fakhouri, L. G. P. (2024). Brazilian Capitol attack: The interaction between Bolsonaro's supporters' content, WhatsApp, Twitter, and news media. *HKS Misinformation Review*.
- Pariser, E. (2011). *The Filter Bubble*. Penguin Press.
- Pena, C. B., MacCarron, P. & O'Sullivan, D. J. P. (2025). Finding polarized communities and tracking information diffusion on Twitter: the Irish Abortion Referendum. *Royal Society Open Science*.
- Rao, A., Morstatter, F. & Lerman, K. (2022). Retweets Amplify the Echo Chamber Effect. *arXiv:2211.16480*.
- Recuero, R., Zago, G. & Soares, F. (2019). Using Social Network Analysis and Social Capital to Identify User Roles on Polarized Political Conversations on Twitter. *Social Media + Society*, 5(2).
- Silva, L. J. et al. (2024). Tweet_Eleições_2022. *Zenodo*. DOI: 10.5281/zenodo.11206577.
- Sunstein, C. R. (2017). *#Republic*. Princeton University Press.
- Tien, J. H. et al. (2020). Online reactions to the 2017 'Unite the Right' rally in Charlottesville. *Applied Network Science*, 5(1).

---
