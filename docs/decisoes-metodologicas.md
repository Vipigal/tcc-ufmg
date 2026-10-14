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

**Decisão:** hidratar os top-100 tweets mais retuitados **por cluster** (clusters com ≥1% dos nós do evento), ranqueados pelo número de retweets feitos por membros do cluster; K = 20 para clusters com ≤5% do peso interno de arestas. Usar essa hidratação para tanto rotular clusters quanto analisar narrativas.

**Por quê:**
- Resolve um problema circular: para rotular clusters precisamos saber quem é esquerda/direita, mas para usar seed accounts as próprias contas-âncora (Lula, Bolsonaro) provavelmente não estão no grafo como nós (são autores retuitados, não retweetadores).
- Hidratar uma vez por evento gera o material para ambas as etapas (rotulagem e análise narrativa), evitando hidratação duplicada.
- Custo controlado: ~US$ 4 em tweets para os quatro eventos (pay-per-use, US$ 0,005/post; ver revisão abaixo). Cache evita pagar duas vezes pelo mesmo tweet.

**Revisão (2026-09-10): seleção por cluster, não por evento.**

A versão inicial selecionava os top-200 tweets **por evento**, medidos sobre o dataset bruto antes de qualquer detecção de comunidade, e rejeitava "top-50 por cluster" porque os clusters ainda não eram conhecidos. Essa premissa caiu: a pipeline (M1–M6) produz partições estáveis para os quatro eventos (`docs/relatorio-sensibilidade-N.md`). A seleção passa a ser feita por **(evento, cluster)**:

- **Unidade de seleção:** cada cluster Leiden com ≥1% dos nós do evento (o mesmo `min_frac` do `run_config.json`).
- **Critério de ranking:** número de retweets ao tweet feitos por **membros do cluster** (nós do grafo), contados em `retweets.parquet`. Não é a contagem global do evento nem a métrica pública da API.
- **K = 100** por cluster. Para clusters com **≤5% do peso interno de arestas** do grafo, **K = 20** — o suficiente para caracterizar do que se tratam, sem investir profundidade de leitura neles. "Peso interno" = soma das arestas internas ao cluster dividida pelo peso **total** de arestas do grafo (intra + inter), o mesmo denominador da matriz de fluxo (M6). Hoje são dois: c3 de mobilizacao-0709 (1,3% do peso; 2,7% dos nós) e c3 de eleicoes (0,35%; 3,4%). O critério por fração de nós dá o mesmo conjunto. Atenção: em eleicoes, c0 e c4 ficam em 5,6% e 5,5% do peso interno (29% e 16% dos nós), logo acima do corte; o corte é por peso, e essa proximidade deve ser lembrada se o critério for reaplicado com outros N/τ.
- **Deduplicação e cache:** IDs repetidos entre clusters do mesmo evento (e entre eventos) são hidratados uma vez; `data/database/hydrated.sqlite` é o cache (ver `data/database/README.md`).
- **Hidratação:** `/2/tweets` sem expansions (US$ 0,005/post retornado). Autores (US$ 0,010/user) em passo separado, quando D7/D8 exigirem.

**Por quê a revisão:**
- A razão para rejeitar seleção por cluster deixou de existir.
- O top-200 global mistura os clusters e sub-representa os menores: no plano K=100, por evento, 165–193 dos 217–276 IDs selecionados por cluster coincidem com o top-200 global; o restante é justamente o material dos clusters menores, que o critério global não alcança.
- O custo caiu uma ordem de grandeza: a API do X passou a pay-per-use em 2026 (US$ 0,005/post, em vez dos ~US$ 0,03 estimados originalmente; sem assinatura). Medido em 2026-09-10: 1.340 slots brutos → 874 IDs únicos (sobreposição entre clusters do mesmo evento: 83 em roberto-jefferson, 240 em eleicoes, 124 em mobilizacao-0709, 49 em invasao-3-poderes; nenhuma entre eventos), 76 já em cache → **798 a hidratar ≈ US$ 4,00** em tweets; autores ≈ US$ 6–8 (razão observada de 0,80 autor/tweet na hidratação anterior).

**Observações que fundamentaram a revisão** (2026-09-10; medidas sobre `retweets.parquet` × `graph_nodes.parquet`, apenas nós do grafo; interpretação como apontamento, não como verdade):
- No nível de conteúdo, os clusters de cada evento se organizam em **dois blocos** que quase não compartilham tweets: cosseno entre vetores de contagem de clusters de blocos distintos 0,00–0,02; dentro do mesmo bloco 0,53–0,80. A fração dos retweets de cada bloco que vai a tweets com ≥90% dos retweets vindos dele é de 93% a 99% em todos os eventos (nulo por permutação de rótulos: 2–4%). Dos 1.005 IDs do plano K=100 sem a regra dos 5%, 95% são exclusivos de um bloco.
- A assimetria observada é de **fragmentação**, não de fechamento: um bloco é um único cluster Leiden; o outro se subdivide em 2–4 clusters que compartilham conteúdo entre si. Qual bloco corresponde a qual campo político só a hidratação dirá — não assumir.
- Eleicoes é regime distinto: os quatro clusters grandes compartilham amplamente (73% dos tweets com ≥5 retweets têm ≤60% de pureza); só o c3 é fechado. Ali, a cobertura dos tweets exclusivos por nós do grafo é baixa (mediana 12%): o conteúdo exclusivo é amplificado sobretudo pela periferia não classificada.
- A camada de conteúdo *próprio* dentro do bloco subdividido existe com volume em um único cluster: c0 de invasao-3-poderes (28% do seu volume; 1.390 tweets exclusivos com ≥5 retweets; o top-100 por contagem lê 21 deles). Nos demais clusters abertos ela é ≤5% do volume, com 0–86 tweets, quase todos no piso de 5 retweets.

**Alternativas rejeitadas ou adiadas:**
- Usar lista de seed accounts (estratégia inicial discutida) — falha porque as seed accounts mais óbvias (políticos com perfis ideológicos claros) tendem a aparecer como autores retuitados, não como retweetadores nos clusters.
- Hidratação massiva — custo proibitivo mesmo a US$ 0,005/post (~29 mil tweets distintos só no 8 de janeiro).
- Manter top-200 por evento (a decisão original) — mistura clusters e perde os menores (acima).
- Amostra estratificada 50 por contagem + 50 exclusivos (pureza ≥0,9, ≥5 retweets) por cluster — **adiada**. Nos clusters fechados o estrato exclusivo coincide com o top-50 por contagem e só reduz a cobertura (ex.: 44% → 29% do volume em roberto-jefferson c1); em 9 dos 15 clusters não há 50 tweets exclusivos com ≥5 retweets. Só faz diferença no c0 de invasao-3-poderes (cobertura da camada própria 23% → 37%). A caracterização do bloco meso do 8 de janeiro será tratada à parte.
- Perfil por tweet (contagens por cluster, pureza, bloco dominante) como artefato Parquet + módulo novo da pipeline — **adiado** até se verificar que a hidratação precisa dele.
- Todos os clusters, sem corte de 1% — acrescentaria ~575 IDs de clusters com 2–38 nós, que não são caracterizáveis por leitura de top-K.

**Implementação (2026-09-15):** `modules/select_tweets.py` (M8, `TopTweetSelector`) grava `top_tweets.parquet` por evento e a tabela `event_top_tweets` por (evento, cluster) em `hydrated.sqlite`; orquestração em `notebooks/pipeline_tcc2.ipynb`. A hidratação é o M9 (`modules/hydrate.py`; cliente HTTP em `modules/fetch_x_data.py`): pede só o que falta no banco, sem expansions, e registra em `lookup_errors` os IDs que a API não devolve, com o motivo — base da atrição por cluster. Retweet repetido do mesmo usuário conta 1 (mesma binarização de M3); desempate por `rt_graph` e depois `tweet_id`. **Recontagem com o código versionado (2026-09-15):** 1.340 slots → **873** IDs únicos (sobreposição entre clusters do mesmo evento: 83 em roberto-jefferson, 239 em eleicoes, 96 em mobilizacao-0709, 49 em invasao-3-poderes; nenhuma entre eventos), 76 já em cache → **797 a hidratar ≈ US$ 3,98**. Os valores de 2026-09-10 acima (874/798; sobreposições 240 e 124) vieram de código de rascunho perdido — o de mobilizacao corresponde ao plano com K=100 em todos os clusters, antes da regra dos 5%. Sem a regra dos 5%, o código versionado dá 999 IDs únicos (registrado como 1.005 acima).

**Risco assumido:** na hidratação anterior (invasao-3-poderes, 100 IDs), 17% não retornaram (tweets removidos, contas suspensas ou protegidas). A atrição não é aleatória — tende a atingir mais o conteúdo de quem foi suspenso após o 8 de janeiro — e deve ser reportada por cluster junto do material lido.

---

## D7. Score ideológico contínuo em vez de classificação binária por usuário

**Decisão:** atribuir a cada usuário um score contínuo em [-1, +1] baseado na proporção de retweets a fontes-direita vs. fontes-esquerda dentro dos tweets hidratados (seleção por cluster, D6):

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

**Revisão (2026-10-06): fora do escopo do TCC2.** O score ideológico por usuário não será calculado. Motivos: (a) a leitura preliminar do conteúdo (`docs/relatorio-narrativa-preliminar.md`, §2.5) mostrou que "esquerda" e "direita" descrevem mal os polos encontrados — um deles reúne candidatos de centro, Gilmar Mendes e a imprensa de referência —, de modo que a régua do score forçaria uma estrutura que o dado não tem; (b) dentro de um polo o score seria quase constante (as metades de um polo subdividido estão sempre do mesmo lado), e a pergunta do TCC2 sobre as subdivisões é de organização interna, não ideológica; (c) a rotulagem dos polos passa a ser feita a posteriori, pelo conteúdo (sínteses por LLM, ver D8) e pela leitura manual dos participantes do grupo focal. Consequência: o painel longitudinal de radicalização previsto no relatório do TCC1, que dependia do score, também sai do escopo (trabalho futuro). Registrado na proposta do TCC2 (`docs/proposta-tcc2.md`, "O que muda em relação ao plano do MSI I").

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

**Revisão (2026-10-06): o LLM deixa de classificar autores e passa a sintetizar conteúdo com ancoragem.** Com a revisão de D7, a primeira tarefa (classificação ideológica dos autores) deixa de existir. O LLM fica com uma função: gerar, por evento e comunidade, sínteses narrativas (temas, protagonistas, antagonistas, tese central) a partir do top-K e dos tweets-assinatura hidratados, sem rótulo ideológico prévio e com cada afirmação citando os identificadores dos tweets que a sustentam. A revisão manual obrigatória se mantém e ganha duas camadas antes dela: checagem automática de que os tweets citados existem e pertencem à comunidade, e comparação item a item com a leitura manual preliminar (o que o modelo capturou, omitiu ou inventou). Modelo, versão e prompt ficam registrados. A rotulagem manual dos polos migra para o grupo focal (proposta do TCC2, etapas E3 e E5).

**Revisão (2026-10-13): síntese em texto livre, como ajuda de leitura, com inclinação política provável.** Em conversa com a orientadora, o papel do LLM foi estreitado: ele **condensa** o material de cada (evento, cluster) para os rotuladores humanos, que categorizam depois. Por isso a síntese deixa de ter campos estruturados (temas, protagonistas, antagonistas, tese central), que pressupunham uma estrutura que não queremos afirmar de antemão. A saída passa a ser: `sintese` (texto livre, 250–400 palavras), `contas_prevalentes` (comentário sobre o tipo de conta que domina), `inclinacao_politica` (texto livre + confiança alta/média/baixa; o eixo esquerda/direita não é obrigatório e "indeterminada" é válida) e `limites`. Mantêm-se: citação `[tweet_id]` inline em toda afirmação, checagem automática das citações contra o corpus do cluster, revisão humana, registro de modelo, prompt e resposta bruta. O que é contável (contas mais retuitadas, tamanho, atrição) é **calculado pela pipeline** e entregue ao modelo, nunca estimado por ele. O corpus de cada cluster passa a ter dois blocos: top-K (mais amplificados) e cauda característica (D16). Modelo: Claude Sonnet 5.5 (`claude-sonnet-5-5`), via Claude Code headless (`claude -p`) na assinatura; um único modelo (comparação Sonnet × Haiku considerada e não adotada). Prompt: `prompts/sintese_cluster_v1.md`. Spec: `docs/superpowers/specs/2026-10-13-sintese-clusters-llm-design.md`.

*Adendo (2026-10-14), visão geral do leitor:* a inclinação aparece também como **tag binária colorida** (direita azul, esquerda vermelho, "outro" amarelo), atribuída pelo autor lendo o `inclinacao_politica` do LLM e guardada na curadoria (`data/curation/clusters.json`), junto com um trecho **literal** da síntese (validado no export). É decisão do autor e contraria a revisão de D7 e a proposta ("esquerda e direita descrevem mal os polos"); "outro" existe para o que não cabe no binário (7/9 Grupo 4, Ciro/PDT). Mitigação disponível: `?tags=0` oculta as tags (ex.: nas sessões do grupo focal). Spec: `docs/superpowers/specs/2026-10-14-visao-geral-comparacao-design.md`.

*Trade-offs assumidos:* (a) a **inclinação política reintroduz um rótulo ideológico**, que a revisão de 2026-10-06 tinha tirado ("sem rótulo ideológico prévio"); ele entra como palpite descrito e com confiança, não como categoria; (b) a síntese **e a inclinação ficam visíveis aos rotuladores desde o início** (alternativa considerada: esconder a inclinação atrás de um "revelar"). Isso acelera a rotulagem, mas a ancora no palpite do modelo: a rotulagem humana não é independente da do LLM, e a comparação LLM × humano prevista acima deve ser lida com essa ressalva; (c) `temperature` não é controlável pelo `claude -p`, então reprodutibilidade = prompt + modelo + resposta bruta guardados, não reexecução.

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

**Revisão (2026-10-06): fora do escopo do TCC2.** O controle temporal do 8 de janeiro (slider de hora sobre o grafo fixo e Q por janela de 3h) não entra na ferramenta do TCC2, cujo foco passa a ser a comparação entre polos e comunidades (sínteses, tweets-assinatura, explicação do método), validada em grupo focal. O desenho acima continua válido como trabalho futuro; o atributo de "primeiro instante de atividade" já existe nos dados, e os horários por cluster foram usados na leitura preliminar (`docs/relatorio-narrativa-preliminar.md`, §1.4).

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

## D15. Leitor de clusters: modo analista do app final, só leitura, dados exportados pela pipeline

**Decisão (2026-09-15):** a ferramenta de leitura dos tweets por cluster — necessária para a rotulagem (D8) e a análise narrativa (§4) — é construída **dentro do app web final** (React + Sigma.js + Tailwind, stack fixada em `docs/visao-projeto.md`), como "modo analista", e é **só leitura**. Ela consome **JSON estático** gerado por um estágio da pipeline (M10, `modules/export.py`) a partir do banco, sem backend (spec §5.3). As coordenadas DRL (M7) passam a ser **entregáveis** da fase 2 (não são mais apagadas pela limpeza), porque alimentam o mini-mapa. Autores são hidratados (D6 previa passo separado; o card do X exige nome, @handle e avatar). Spec completa: `docs/superpowers/specs/2026-09-15-leitor-de-clusters-design.md`.

**Objetivo declarado, nesta ordem:** (1) ser o embrião da navegação interativa do produto final (D9; componente B da spec §5.2); (2) ser ferramenta analítica do pesquisador para avaliar a narrativa de cada cluster e a disposição dos tweets — em contexto estrutural (mini-mapa), com pureza, sobreposição entre clusters e atrição visíveis por slot.

**Por quê:**
- Evita trabalho descartável: cada hora no leitor é hora no entregável central.
- A leitura qualitativa precisa do contexto que só a pipeline tem (pureza, `rt_cluster` vs. API, IDs não devolvidos por cluster); um leitor genérico do X não mostra isso.
- Sem backend, a ferramenta é publicável como está e reprodutível a partir do repositório.
- Só leitura porque anotar por tweet exigiria um caminho de escrita no banco; a classificação (D7/D8) é por **autor** e será feita pela pipeline (LLM + revisão), não pela interface.

**Alternativas rejeitadas:**
- Streamlit/Panel — rápido, mas fora da stack fixada, fraco para a fidelidade do card e para 33 mil pontos, e seria descartado.
- SQLite no navegador (sql.js) — liga ao banco literalmente, mas os joins ficariam em JavaScript sem testes; o app público precisa de JSON curado de qualquer forma.
- Datasette sobre o banco — navegação instantânea, sem card nem mini-mapa.
- Ferramenta separada e descartável — duplicaria o esforço do componente B.

---

## D16. Cauda característica por cluster, por sobrerrepresentação (lift)

**Decisão (2026-10-13):** além do top-K (D6), cada (evento, cluster) ganha uma cauda de até `m` tweets (M8b, `TailSelector` em `modules/select_tweets.py`) para a síntese por LLM (D8). Para cada tweet *t* e cluster *c*: `lift(t, c) = (rt_c(t) / rt_graph(t)) / (RT_c / RT_graph)` — a fração dos retweets de *t* vinda de *c*, sobre a fração de *c* em todos os retweets do grafo. Candidatos: `rt_c ≥ min_rt`, `lift > 1` e fora do top-K de *c*; seleção por lift desc → rt_cluster desc → tweet_id asc. Valores iniciais, a ajustar: `m = 50`, `min_rt = 10`. Gravada em `event_tail_tweets`, separada do top-K; hidratada pelo mesmo M9.

**Por quê:**
- O top-K mostra o que o cluster mais amplifica, inclusive o que circula no evento todo; a pergunta sobre a estrutura interna de um polo subdividido precisa do que cada fatia amplifica *mais que as irmãs*.
- Medido em 2026-10-13 (tweets fora do top-K, ≥ 10 RTs no cluster): o critério de exclusividade "≥ 90% dos RTs vêm de c" devolve centenas a milhares de tweets nos polos fechados (invasão c1: 1.776; RJ c1: 2.083) e ~0 nas fatias (eleições: 0–11 por cluster; mobilização c1–c3: 1–3). As fatias diferem em grau, não em exclusividade — o lift ordena os dois casos com uma regra só.
- `lift > 1` é a definição de sobrerrepresentação, não um ajuste: sem ele, clusters com poucos candidatos (eleições c2, c4) completavam o top-50 com tweets sub-representados (lift 0,82–0,88).

**Observação (2026-10-13):** nos polos fechados o lift satura no teto `1 / (RT_c / RT_graph)` (tweets 100% exclusivos) para todos os 50 selecionados; ali a ordem efetiva é por `rt_cluster` — a cauda vira "os exclusivos mais retuitados fora do top-K". Plano: 649 IDs, 625 novos, ≈ US$ 3,12 em tweets + autores novos.

**Alternativas rejeitadas:**
- Exclusividade absoluta ≥ X% — vazia exatamente nas fatias que se quer diferenciar.
- Lift contra os clusters irmãos do mesmo polo — mais nítido para a estrutura interna, mas exige definir formalmente os polos (agrupar clusters), uma escolha analítica a mais.
- Aumentar K do top-K — traz mais do que já é compartilhado, não o que é próprio.

---

## D17. Conteúdo compartilhado entre clusters (barra da visão geral)

**Decisão (2026-10-14):** a visão geral do leitor mostra, por cluster *c*, `shared(c)` = fração dos retweets dados por *c* que vai a conteúdo que também circula em outros clusters, decomposta em `shared_with(c, d) = Σ_t rt_c(t)·rt_d(t)/rt_graph(t) ÷ Σ_t rt_c(t)`. Equivale a 1 − pureza média dos tweets que *c* retuíta, ponderada por `rt_c`. Sobre o log completo do evento (usuário×tweet distinto conta 1). Estágio `ContentOverlap` (`modules/overlap.py`); exportado em `event.json`.

**Por quê:**
- Mostra a forma da polarização (quem está isolado, quem é "irmão" de quem) sem nomear ninguém e **sem exigir definir polos** antes (a E1 ainda não formalizou o agrupamento).
- Reaproveita a noção de pureza que o leitor já exibe por tweet — uma ideia a menos para explicar ao grupo focal.
- Medido em 2026-10-14: polos fechados 1–3% (7/9 c0, RJ c1, eleições c3, 8/1 c1); fatias irmãs 22–77%, sempre apontando a irmã esperada; 7/9 c3 (Ciro) 24% com o polo anti-Bolsonaro e 2% com o bolsonarista.

**Observação:** é assimétrica (8/1: c2→c0 50%, c0→c2 21%) — o grupo menor compartilha mais com o maior; o "Como ler esta tela" do app explica. Não substitui a hermeticidade por super-polo da E1 (grafo de usuários); são medidas complementares.

**Alternativas rejeitadas:**
- Nº de tweets em comum entre as seleções (top-K ∪ cauda) — depende de K e da atrição; fica só como dado secundário na comparação.
- Hermeticidade por super-polo — exige definir os polos primeiro.

---

## Histórico de decisões revisadas

Este espaço é para registrar mudanças futuras de decisão. Toda vez que uma decisão acima for revisada, registrar aqui:

| Data | Decisão revisada | O que mudou | Por quê |
|---|---|---|---|
| 2026-06-17 | D5 — filtragem de ruído | Removido o filtro de tweets virais; mantido apenas o filtro de usuários inativos | Tweets de alto alcance são o material central da análise narrativa, não ruído; e o limiar de 30% não removia nenhum tweet na validação preliminar |
| 2026-06-18 | D4 / implementação | Backbone (corte τ) fundido na projeção (M4), em blocos; módulo `backbone.py` removido | Cortar τ na projeção evita materializar o grafo inteiro e dá resultado idêntico (Jaccard é por par). Ver D14. |
| 2026-09-10 | D6 — hidratação seletiva | Seleção passa de top-200 por evento para top-100 por cluster (≥1% dos nós), ranqueada por retweets internos ao cluster; K=20 para clusters com ≤5% do peso interno de arestas | Clusters agora são conhecidos (premissa da rejeição original caiu); top-200 global sub-representa clusters menores; custo caiu para ~US$ 4 com o pay-per-use da API |
| 2026-10-06 | D7 — score ideológico | Sai do escopo do TCC2: sem score por usuário nem painel de radicalização | "Esquerda/direita" descreve mal os polos (um reúne centro e imprensa de referência); as subdivisões internas não são ideológicas; rótulos passam a emergir do conteúdo e do grupo focal |
| 2026-10-06 | D8 — uso de LLM | Deixa de classificar autores; gera sínteses narrativas ancoradas em tweets citados, com checagem automática das citações, comparação com a leitura manual e revisão humana | Decorre da revisão de D7; a ancoragem torna a síntese verificável |
| 2026-10-06 | D10 — controle temporal do 8/1 | Sai do escopo do TCC2 (trabalho futuro) | O foco da ferramenta passa à comparação entre polos e comunidades, validada em grupo focal |
| 2026-10-13 | D8 — uso de LLM | Síntese em texto livre como ajuda aos rotuladores (sem temas/protagonistas/tese impostos), com inclinação política provável + confiança, visível desde o início; corpus = top-K + cauda (D16); Sonnet 5.5 via `claude -p` | Decisão com a orientadora: a categorização é humana e posterior; o LLM só condensa. Rótulo ideológico volta como palpite descrito, com o trade-off de ancoragem assumido |
| 2026-10-14 | D8 — uso de LLM | Tag binária colorida de inclinação (+ "outro") na visão geral, atribuída pelo autor a partir do texto do LLM; trecho curado literal | Decisão do autor para legibilidade; trade-off com D7 registrado; `?tags=0` como mitigação |
