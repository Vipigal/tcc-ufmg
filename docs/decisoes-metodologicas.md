# Decisões Metodológicas — Registro de Trade-offs

Este arquivo registra **por que** cada escolha metodológica foi feita e quais alternativas foram consideradas e rejeitadas. O objetivo é evitar que decisões fechadas sejam reabertas sem motivo, e ao mesmo tempo permitir revisão consciente caso surja um problema novo.

Cada decisão é apresentada no formato:

> **Decisão:** o que foi escolhido.
> **Por quê:** o raciocínio.
> **Alternativas rejeitadas:** o que foi considerado e descartado, e por quê.

---

## D1. Foco no 8 de janeiro como evento central, com eventos precursores como contexto

**Decisão:** o trabalho analisa quatro eventos (7 de setembro 2022, Roberto Jefferson, debate "democracia" do 2º turno, 8 de janeiro 2023), tratando o 8 de janeiro como o ápice de um arco narrativo de tensionamento progressivo.

**Por quê:**
- O 8 de janeiro é um evento dramático, claramente delimitado e de alta relevância pública. Faz a defesa do tema ser direta.
- Tratá-lo isolado seria redundante com a literatura recente (Bastos & Recuero 2023; Ozawa et al. 2024).
- A escolha de quatro eventos ligados narrativamente permite contar uma história de construção da polarização, não apenas medi-la em um ponto.
- Quatro é factível em prazo de TCC; cinco ou mais começaria a apertar.

**Alternativas rejeitadas:**
- Analisar todos os 110 eventos do dataset (proposta original) — inviável em prazo de TCC e tornaria a análise dispersa.
- Analisar só o 8 de janeiro — sem contexto comparativo, a análise perde força.
- Análise temporal pré/durante/pós em escala de semanas — o dataset é estruturado por eventos, não por cobertura contínua, então não suporta esse recorte.

---

## D2. Co-retweet network em vez de retweet network direto

**Decisão:** construir uma rede de co-retweet (projeção unipartida de uma rede bipartida usuário-tweet), em que dois usuários são ligados se compartilham retweets a tweets em comum.

**Por quê:**
- O dataset preserva apenas o ID do tweet referenciado, não o autor original. Construir o grafo direto "A retuita B" exigiria hidratar a maioria dos tweets, com custo proibitivo.
- A co-retweet network é metodologicamente válida e tem precedentes na literatura recente (Tien et al. 2020; Pena et al. 2025; estudos sobre eleição EUA 2020).
- Para a pergunta central do trabalho — "como dois grupos enxergam o mesmo fato?" — a co-retweet network é até melhor: a unidade de análise vira o **ambiente informacional** do usuário (o que ele consome), não o fluxo de quem retuita quem.

**Alternativas rejeitadas:**
- Hidratar massivamente para construir grafo direto — custo estimado em centenas de dólares, fora de orçamento.
- Recuperar autores via join interno no dataset — taxa de recuperação ~19%, muito baixa para análise representativa.

**Limitação assumida:** o grafo mede similaridade de consumo, não fluxo causal de influência. Isso é registrado no documento final.

---

## D3. Peso Jaccard nas arestas

**Decisão:** o peso da aresta entre dois usuários é o coeficiente de Jaccard sobre os conjuntos de tweets que cada um retuitou:

```
J(u, v) = |T_u ∩ T_v| / |T_u ∪ T_v|
```

**Por quê:**
- Normaliza pela atividade total dos usuários, evitando que usuários hiperativos apareçam como "próximos" só por causa do volume.
- É a métrica padrão para projeções bipartidas em literatura comparável.
- Implementação simples e barata computacionalmente.

**Alternativas rejeitadas:**
- Contagem absoluta de tweets em comum — inflada por usuários hiperativos, distorce a estrutura.
- Cosseno binário — equivalente em interpretação ao Jaccard para vetores binários, sem ganho prático.
- TF-IDF antes da projeção — mais sofisticado, mas adiciona complexidade que pode não ser necessária. Pode ser revisitado se a projeção mostrar que tweets de altíssimo alcance dominam indevidamente a estrutura (note que o peso Jaccard já normaliza pela atividade total de cada usuário).

---

## D4. Universal threshold como técnica de backbone extraction

**Decisão:** após calcular o peso Jaccard, manter apenas as arestas com peso ≥ τ, com τ inicial = 0,1. Documentar análise de sensibilidade em τ = 0,05 e τ = 0,15.

**Por quê:**
- Simples, defensável, fácil de explicar na defesa.
- Adequado ao nível de um TCC; metodologias mais sofisticadas (disparity filter, SDSM) acrescentam complexidade sem retorno proporcional para o objetivo de visualização.
- A análise de sensibilidade documenta a robustez dos achados ao parâmetro escolhido.

**Alternativas rejeitadas:**
- Disparity filter (Serrano et al. 2009) — mais sofisticado, considerado para versão futura mas fora do escopo inicial.
- Stochastic Degree Sequence Model — mais rigoroso, mas computacionalmente caro e complexo demais para a justificativa do trabalho.
- Nenhum backbone — geraria hairball ilegível.

---

## D5. Filtragem de ruído antes da projeção

**Decisão:** aplicar um único filtro antes da projeção bipartida — descartar usuários que retuitaram menos de N vezes no evento (N inicial = 3).

**Por quê:**
- Usuários com 1-2 retweets não têm sinal suficiente para serem classificados em uma bolha.
- O parâmetro N é ajustável empiricamente durante a validação preliminar.

**Reversão (2026-06-17): remoção do filtro de tweets virais.**

A versão inicial desta decisão previa um segundo filtro, que descartava tweets retuitados por mais de X% dos usuários do evento (X inicial = 30%), sob a hipótese de que tweets "consumidos por todos os lados" eram ruído. Esse filtro foi **removido** por duas razões:

1. **Metodológica (decisiva).** Os tweets de maior alcance são justamente o material central da análise narrativa — o que cada comunidade amplificou sobre o evento. Tratá-los como ruído contradiz a pergunta de pesquisa. Passam a ser preservados.
2. **Empírica.** Na validação preliminar (evento 8 de janeiro), o limiar de 30% não removeu nenhum tweet: o mais retuitado alcançou ~11% dos usuários remanescentes. O filtro era, na prática, inócuo no regime de parâmetros considerado.

A explosão combinatória de arestas causada por tweets muito retuitados — que motivava o filtro do ponto de vista computacional — é tratada **na projeção** (corte do peso Jaccard durante a geração das arestas, ver D4), não por descarte de dados.

**Alternativas rejeitadas:**
- Não filtrar nada — usuários sem sinal (1-2 retweets) inflam o grafo sem contribuir para a estrutura de comunidades.
- Filtro de usuários fixo sem possibilidade de ajuste — não conhecemos o valor certo de N até olhar os dados.

**Risco assumido:** N passa a ser o único parâmetro de filtragem e, portanto, o mais frágil dessa etapa. A validação preliminar é desenhada para calibrá-lo.

---

## D6. Estratégia de hidratação seletiva — hidratar antes de rotular, não depois

**Decisão:** hidratar os top-200 tweets mais retuitados de cada evento (medido sobre o dataset bruto, antes de qualquer detecção de comunidade). Usar essa hidratação para tanto rotular clusters quanto analisar narrativas.

**Por quê:**
- Resolve um problema circular: para rotular clusters precisamos saber quem é esquerda/direita, mas para usar seed accounts as próprias contas-âncora (Lula, Bolsonaro) provavelmente não estão no grafo como nós (são autores retuitados, não retweetadores).
- Hidratar uma vez por evento gera o material para ambas as etapas (rotulagem e análise narrativa), evitando hidratação duplicada.
- Custo controlado: ~US$ 24 no total para os quatro eventos. Cache evita pagar duas vezes pelo mesmo tweet.

**Alternativas rejeitadas:**
- Usar lista de seed accounts (estratégia inicial discutida) — falha porque as seed accounts mais óbvias (políticos com perfis ideológicos claros) tendem a aparecer como autores retuitados, não como retweetadores nos clusters.
- Hidratar top-50 *por cluster* — exigiria conhecer os clusters antes, o que é o que queríamos descobrir.
- Hidratação massiva — custo proibitivo.

---

## D7. Score ideológico contínuo em vez de classificação binária por usuário

**Decisão:** atribuir a cada usuário um score contínuo em [-1, +1] baseado na proporção de retweets a fontes-direita vs. fontes-esquerda dentro dos top-200 hidratados:

```
score(u) = (R_right(u) - R_left(u)) / (R_right(u) + R_left(u))
```

**Por quê:**
- Captura nuances: usuários moderados ou ambíguos têm score próximo de zero, não são forçados a um lado.
- Permite análises mais ricas (distribuição dos scores em cada cluster, identificação de pontes via scores intermediários).
- A rotulagem do *cluster* (não do usuário) ainda é categórica, baseada na mediana dos scores.

**Alternativas rejeitadas:**
- Classificação binária por usuário (esquerda/direita) — perde informação, especialmente sobre usuários moderados ou indefinidos.
- Score baseado em outras métricas além do retweet — fora do escopo (não temos texto dos tweets do usuário, só dos retuitados).

---

## D8. Uso de LLM como assistente, com revisão manual obrigatória

**Decisão:** usar LLM (Claude ou equivalente) em duas etapas — classificação ideológica dos autores hidratados, e sumarização das narrativas por cluster. Em ambos os casos, a saída do LLM é revisada manualmente antes de ser usada na análise final.

**Por quê:**
- LLM acelera muito as duas tarefas (cada uma seria inviável manualmente em ~800 autores hidratados).
- Revisão manual evita erros sistemáticos do modelo e mantém o trabalho defensável academicamente.
- Documentar o uso é transparente e está em linha com boas práticas atuais em pesquisa assistida por IA.

**Alternativas rejeitadas:**
- Classificação 100% manual — inviável em prazo de TCC.
- LLM sem revisão — frágil para defesa, e arrisca erros sistemáticos.
- Treinar classificador supervisionado próprio — overkill para o escopo.

**Compromisso:** documentar explicitamente no TCC os prompts usados, os critérios de revisão e exemplos de casos em que a revisão alterou a classificação do LLM.

---

## D9. Visualização como produto central, não como complemento

**Decisão:** a aplicação web interativa pública é tratada como entregável central, não como anexo do trabalho escrito.

**Por quê:**
- O TCC é em Sistemas de Informação; um produto computacional concreto fortalece a defesa.
- A pergunta central do trabalho é explicitamente sobre **tornar visível** a divergência — sem produto visual, a pergunta fica respondida apenas em métricas abstratas.
- A visualização permite que o trabalho atinja audiência além da banca.

**Alternativas rejeitadas:**
- Apenas grafos estáticos no documento do TCC — não cumpre o objetivo de tornar a estrutura "navegável".
- Notebook Jupyter interativo — adequado para análise técnica, inadequado para leitor não-técnico.

---

## D10. Grafo estrutural fixo + filtro temporal de visualização (não grafos por janela)

**Decisão:** para o 8 de janeiro, computar **um único grafo** sobre todos os retweets do dia, com cada nó e cada aresta carregando o atributo de "primeiro instante de atividade". No frontend, o slider de hora apenas controla a opacidade/visibilidade dos elementos.

**Por quê:**
- Simples de implementar e de explicar.
- Estruturalmente correto: um nó que aparece às 18h já é membro daquele cluster; ele estava lá esperando o evento, só não tinha agido ainda.
- Permite visualizar o efeito "a rede se preenche" sem custo computacional alto.

**Alternativas rejeitadas:**
- Recomputar o grafo a cada janela horária — pesado, e produziria mudanças estruturais espúrias só por causa do volume diferente de cada janela.
- Animação pré-renderizada como vídeo — perde a interatividade.

**Complemento:** calcular modularidade Q por janela de 3h (sobre subgrafos induzidos pelos nós ativos em cada janela) e exibir como gráfico de linha ao lado. Isso mostra a evolução estrutural sem comprometer a coerência do grafo principal.

---

## D11. Não incluir análise da influência de Elon Musk no Twitter

**Decisão:** apesar de Musk ter comprado o Twitter em outubro/2022 (~3 meses antes do 8 de janeiro), o trabalho **não** investiga o impacto dessa mudança de governança na plataforma.

**Por quê:**
- Já estamos abrindo várias frentes novas; adicionar mais uma dispersa o escopo.
- Atribuir mudanças estruturais especificamente a decisões de Musk seria difícil de provar com este dataset.
- Pode virar uma seção de "discussão" no TCC, não uma hipótese central.

**Alternativas rejeitadas:**
- Manter Musk como variável de análise (parte da proposta original) — sai do escopo enxuto do pivô atual.

---

## D12. Tipo de pesquisa: mista (científica + tecnológica)

**Decisão:** classificar o trabalho como pesquisa mista na capa.

**Por quê:**
- Tem componente científico claro: análise quantitativa de redes, métricas estruturais, comparação entre eventos.
- Tem componente tecnológico claro: pipeline reutilizável + aplicação web interativa publicada.
- Caracterizar como puramente científica subestima o produto; como puramente tecnológica subestima a análise.

**Alternativas rejeitadas:**
- "Científica" pura — não captura o entregável tecnológico.
- "Tecnológica" pura — não captura a análise comparativa entre eventos.

---

## D13. Idempotência da pipeline por cache de estágio

**Decisão:** cada módulo da pipeline (M1–M6) implementa uma interface uniforme de estágio (classe base `Stage`) com um método `run(..., force=False)` que carrega os artefatos do disco se já existem, ou recalcula e persiste caso contrário. No notebook, um único parâmetro `FORCE_FROM = N` recalcula o módulo N e todos os posteriores (cascata).

**Por quê:**
- A pipeline é iterada muitas vezes (especialmente o M4, projeção). Re-executar o notebook inteiro a cada mudança reprocessaria etapas caras (carga de ~1,1M linhas, filtragem, bipartida) sem necessidade.
- Centralizar a lógica de cache numa classe base (padrão **Template Method**) mantém a interface pública descritiva dos módulos intacta (`build`, `project`, `apply`, `extract`, `detect`) e a política de persistência num só lugar, testável isoladamente (`tests/test_stage.py`).
- `load()` reconstrói o objeto completo em memória, inclusive `stats` — o caminho `compute → save → load` faz round-trip para um estado equivalente, sem leituras especiais de disco nas células de inspeção.

**Mecânica de invalidação:** por **existência de arquivo**, não por hash de conteúdo ou de código (escola leve, estilo Make). Consequência assumida: se o código de um módulo muda, o cache não percebe sozinho — é preciso forçar o recálculo via `FORCE_FROM`. Essa disciplina está documentada na célula de configuração do notebook.

**Alternativas rejeitadas:**
- Framework de pipeline (DVC, Dagster, Snakemake, Ploomber) — fariam invalidação por hash e gestão de dependências, mas adicionam maquinário desproporcional a um TCC com pandas/igraph/scipy. Registrado como próximo degrau caso o projeto escale.
- Cache por hash de entrada/código — mais robusto, porém mais complexo; YAGNI para o porte atual.
- Função utilitária solta (`materialize`) em vez de método de classe — preferiu-se a interface interna às classes pela ergonomia de chamada no notebook (`Stage(...).run(...)`).

**Trade-off assumido:** acoplar a política de cache à hierarquia de classes reduz um pouco a separação de responsabilidades, mas a lógica fica inteira na base `Stage` (DRY e coberta por testes).

---

## D14. Projeção em blocos com backbone embutido + formato final em Parquet

**Decisão:** o módulo de projeção (M4) passa a (a) calcular o Jaccard **em blocos** de usuários, (b) cortar o peso em τ **durante** a geração das arestas, e (c) remover nós isolados — produzindo o grafo de backbone diretamente. O módulo separado de backbone (`backbone.py`) foi **removido** e fundido na projeção. O resultado final da pipeline é serializado em dois Parquet autocontidos (`graph_edges.parquet`, `graph_nodes.parquet`); o GraphML foi descontinuado.

**Por quê (projeção em blocos + corte embutido):**
- A projeção ingênua (`C = B·Bᵀ` inteiro) materializava centenas de milhões de arestas antes de qualquer corte, estourando a memória. Processar em blocos de `block_size` usuários limita o pico de memória ao bloco, não ao grafo inteiro.
- O corte por τ é feito na projeção porque `J(u,v)` depende **só** dos conjuntos `T_u` e `T_v` daquele par — não do limiar nem das outras arestas. Logo, cortar em τ durante a projeção dá um grafo **idêntico** a projetar tudo e filtrar depois (não há renormalização do Jaccard). Validado em dados reais: N=10 reproduz exatamente 22.097 nós / 5.661.890 arestas e modularidade Q=0,5034, em ~13s e ~1 GB de pico (vs. 80,5M de arestas materializadas antes).
- **Sem `τ_floor`:** uma versão intermediária cortava num piso (0,05) para permitir a análise de sensibilidade re-filtrando. Como a projeção em blocos ficou rápida, optou-se por cortar direto em τ e **reprojetar** para cada valor da sensibilidade (τ=0,05/0,10/0,15) — mais simples, sem o passo de backbone separado, resultado idêntico.

**Por quê (construção do igraph com numpy):** a versão anterior do M5 montava o grafo via `list(zip(W.row.tolist(), W.col.tolist()))`, criando dezenas de milhões de objetos Python (gargalo de memória/tempo). Passou a usar `np.column_stack` direto.

**Por quê (formato final em 2 Parquet):**
- O `community_graph.graphml` (XML) chegou a **560 MB** para 5,66M de arestas, sendo 100% redundante com os dados já presentes em outros artefatos.
- `graph_edges.parquet` (src, dst, peso) + `graph_nodes.parquet` (user_id, community) somam ~16,8 MB (zstd), são autocontidos e em formato universal.
- `graph_nodes.parquet` é o **acumulador natural** para os atributos por usuário das etapas seguintes (score ideológico — §3.4; coordenadas de layout e grau — §3.6 da proposta). `graph_edges.parquet` alimenta centralidade, fluxo inter-cluster e o render no Sigma.js.

**Limpeza:** `modules/cleanup.py` apaga os artefatos intermediários (M1–M4) e órfãos de versões anteriores (`projection_*`, `community_graph.graphml`), mantendo só o resultado final. Re-rodar a pipeline recomputa do zero (cache por existência de arquivo, ver D13).

**Alternativas rejeitadas:**
- Manter projeção e backbone como módulos separados — gerava e persistia ~80M arestas (236 MB) para descartar >90% no passo seguinte.
- `τ_floor` + re-filtragem — ganho marginal após a projeção ficar rápida; adiciona um limiar a mais para raciocinar.
- Trio `npz` + parquets como formato final — ligeiramente maior (19,3 MB) e menos ergonômico que os 2 Parquet para as etapas seguintes.
- Jaccard aproximado (MinHash/LSH) — complexidade desproporcional; a projeção exata em blocos resolve.

---

## Histórico de decisões revisadas

Este espaço é para registrar mudanças futuras de decisão. Toda vez que uma decisão acima for revisada, registrar aqui:

| Data | Decisão revisada | O que mudou | Por quê |
|---|---|---|---|
| 2026-06-17 | D5 — filtragem de ruído | Removido o filtro de tweets virais; mantido apenas o filtro de usuários inativos | Tweets de alto alcance são o material central da análise narrativa, não ruído; e o limiar de 30% não removia nenhum tweet na validação preliminar |
| 2026-06-18 | D4 / implementação | Backbone (corte τ) fundido na projeção (M4), em blocos; módulo `backbone.py` removido | Cortar τ na projeção evita materializar o grafo inteiro e dá resultado idêntico (Jaccard é por par). Ver D14. |