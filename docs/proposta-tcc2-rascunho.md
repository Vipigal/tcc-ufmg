# Proposta do TCC2 — rascunho

> **Status:** rascunho completo de trabalho (2026-10-06). Todas as seções exigidas pelas diretrizes (capa, introdução, referencial, metodologia, resultados esperados, cronograma e referências) estão redigidas.
> **Citações:** os números entre colchetes seguem a bibliografia de `docs/guia-citacoes-tcc2.md` (§4). As referências [T*] são novas, ainda não auditadas, e precisam ser conferidas antes de entrar no texto final. Na versão final, renumerar pela ordem de citação (IEEE).
> **Marcação editorial** (apagar na versão final): ⟦mantido⟧ = vem do TCC1/proposta original e continua firme; ⟦corrigido⟧ = vem do TCC1 com outra fonte ou redação; ⟦novo⟧ = só no TCC2; ⟦decidir⟧ = escolha de redação pendente com o autor ou a orientadora.
> **Limite:** a proposta tem no máximo 10 páginas (diretrizes). Este rascunho está acima disso e precisará de corte, sobretudo no Referencial.

---

## Capa

- **Título:** Duas realidades sobre o mesmo fato: estrutura, conteúdo e visualização interativa da polarização no Twitter brasileiro no ciclo eleitoral de 2022 ⟦decidir⟧
- **Tipo de pesquisa:** Mista (científica e tecnológica)
- **Aluno:** Vinícius Pinho Galvão
- **Orientadora:** Eliane Cristina de Freitas Rocha
- **Coorientador:** —
- **Local e data:** Belo Horizonte, outubro de 2026

---

## 1. Introdução

### 1.1 Contexto e motivação ⟦mantido + corrigido⟧

O segundo turno da eleição presidencial de 2022 terminou com a vitória de Lula sobre Jair Bolsonaro por uma margem estreita ⟦citar resultado oficial do TSE⟧. Pouco mais de dois meses depois, em 8 de janeiro de 2023, apoiadores de Bolsonaro invadiram e depredaram as sedes dos três poderes em Brasília, contestando o resultado das urnas [19]. Para boa parte do país, esses fatos representavam um ataque à democracia. Para outra parcela, eram um ato legítimo de protesto. Não havia vocabulário comum entre as duas leituras nem um espaço em que elas se confrontassem.

Que o Brasil está dividido é quase um consenso intuitivo. Menos óbvia, e mais interessante de investigar, é a **forma** dessa divisão. Dizer que existem dois grupos opostos é diferente de dizer que eles estão isolados entre si, e diferente ainda de dizer que se comportam da mesma maneira. Duas comunidades podem coexistir trocando ataques e informação o tempo todo, ou podem se fechar em ambientes paralelos que quase não se tocam.

As redes sociais são onde boa parte dessas leituras se forma e circula, e o Twitter ocupa uma posição particular por ser centrado em opinião e em reação ao noticiário. A experiência de cada usuário é moldada tanto pelo que ele escolhe seguir e amplificar quanto pelo que os algoritmos de curadoria lhe entregam [2], [3]. Duas pessoas expostas ao mesmo evento podem, assim, ter contato com versões quase opostas dele.

O fechamento de um ambiente informacional tem consequências concretas. No debate sobre a hidroxicloroquina durante a pandemia, os grupos favorável e contrário ao medicamento circularam dietas informativas distintas: no primeiro, a desinformação estava associada a veículos hiperpartidários [12], e o conteúdo amplificado contrariava a evidência clínica [42], [43]. ⟦decidir: manter este parágrafo da Covid, encurtado, ou abrir direto pela forma da polarização⟧

O mesmo mecanismo pode ajudar a entender o caminho até o 8 de janeiro. Para quem acompanhava a eleição num ambiente em que quase todos apoiavam o mesmo candidato, a derrota era difícil de conciliar com o que via todos os dias. Interian e Rodrigues [17] observaram um isolamento acentuado da comunidade de direita no Twitter durante a eleição de 2022 e levantaram a hipótese de que ele tenha influenciado os atos de 8 de janeiro. Bastos e Recuero [19] acrescentam que a narrativa de fraude foi também oferecida pela própria liderança, numa escalada de declarações ao longo da campanha. Os dois mecanismos, fechamento do ambiente e oferta de narrativa, são complementares.

Este trabalho parte da hipótese de que a divergência não nasceu pronta no 8 de janeiro. Ela foi construída ao longo do ciclo eleitoral. Por isso analisa quatro eventos que compõem um arco de tensionamento institucional:

- a **mobilização de 7 de setembro de 2022**, com forte contestação ao STF e ao sistema eleitoral;
- o **caso Roberto Jefferson**, em 23 de outubro: o ex-deputado, aliado de Bolsonaro e em prisão domiciliar, reagiu a uma ordem de prisão do STF com tiros de fuzil e granadas contra agentes da Polícia Federal [45]–[47];
- o **dia do segundo turno**, 30 de outubro;
- a **invasão de 8 de janeiro de 2023**.

### 1.2 O que foi feito no TCC1 (MSI I) ⟦novo⟧

O objetivo geral do TCC1 era caracterizar a estrutura das comunidades políticas no Twitter brasileiro em torno do 8 de janeiro e tornar essa estrutura compreensível por meio de uma visualização interativa. O trabalho usou o dataset desidratado Tweet_Eleições_2022 [1].

Como o dataset não traz o autor dos tweets retuitados, o TCC1 construiu uma **rede de co-retweet**: dois usuários se ligam pela coincidência do que retuitaram, em analogia ao acoplamento bibliográfico. As arestas são ponderadas pelo índice de Jaccard, e as comunidades são detectadas pelo algoritmo de Leiden. O TCC1 entregou:

- **Uma pipeline reutilizável**, com cache por estágio e testes, aplicada aos quatro eventos e acompanhada de análise de sensibilidade dos parâmetros (filtro de atividade *N* e limiar de backbone τ).
- **Uma caracterização estrutural.** Nos três eventos de confronto, a rede se organiza em dois super-polos, com uma comunidade quase lacrada (hermeticidade de 0,97 a 0,999). O dia do segundo turno é a exceção, com a menor segregação. O resultado é consistente com a literatura sobre o Twitter brasileiro [17].
- **O início da camada de conteúdo e da ferramenta.** Os tweets mais retuitados de cada comunidade foram hidratados seletivamente (cerca de 680 tweets e 385 autores, com cache em banco local), e um leitor web de beta exibe, por evento e comunidade, o mapa do grafo e os tweets dominantes.

O próprio TCC1 apontou seu limite: as comunidades eram objetos apenas estruturais. A pergunta que motivou o trabalho, sobre como dois grupos constroem leituras divergentes de um mesmo fato, dependia de uma camada de conteúdo ainda não realizada.

### 1.3 Problema e perguntas do TCC2 ⟦novo⟧

A pergunta central continua a mesma: **o Twitter brasileiro estava polarizado no ciclo eleitoral de 2022, e qual é a forma dessa polarização?** O TCC2 a desdobra em quatro perguntas:

1. **Como os polos se organizam por dentro?** A revisão dos resultados do TCC1 (Seção 3, E1) mostrou que, somadas as comunidades de cada lado, os dois super-polos são igualmente herméticos (acima de 0,99 nos três eventos de confronto). A diferença está na organização interna: um polo aparece monolítico e o outro subdividido, e o lado subdividido muda de evento para evento. Resta saber se essas subdivisões são comunidades discursivas distintas ou artefatos da detecção.
2. **O que cada polo diz?** Qual é a narrativa de cada comunidade em cada evento?
3. **O que um polo vê que o outro não vê?** Quais mensagens um lado amplificou intensamente e o outro praticamente ignorou (os "tweets-assinatura")?
4. **Os ambientes informacionais são diferentes a ponto de constituírem realidades paralelas?** Por exemplo, o polo que se fechou viu algo que antecipasse a vitória do outro candidato?

Há também um problema de comunicação da pesquisa. Pesquisas sobre polarização em redes sociais costumam chegar ao público, e mesmo a pesquisadores de áreas vizinhas, como resultados estáticos e difíceis de interrogar. A experiência com o leitor web do TCC1 indicou que, sem mediação, a leitura dos grafos e dos clusters é confusa para quem não vem da computação. A tese tecnológica do trabalho é que **uma análise dessa natureza deve ser navegável**: pessoas de comunicação e de ciência política devem conseguir entender como a análise funciona e explorar seus achados por conta própria.

### 1.4 Objetivos

**Objetivo geral:** caracterizar a forma e o conteúdo da polarização no Twitter brasileiro ao longo do arco eleitoral de 2022–2023 e disponibilizar essa análise numa aplicação interativa que a torne compreensível e explorável por pesquisadores de comunicação e ciência política.

**Objetivos específicos do TCC2:**

1. Revisar a caracterização estrutural do TCC1 no nível dos polos e testar a robustez das subdivisões internas a seeds, resolução, modelo de detecção e limiar de backbone.
2. Hidratar seletivamente, com o saldo disponível da API, os tweets que discriminam as subdivisões robustas e, se o orçamento permitir, um quinto evento relevante para o arco.
3. Identificar os tweets-assinatura de cada polo e comunidade.
4. Produzir, com apoio de modelo de linguagem, sínteses narrativas por evento e comunidade, ancoradas nos tweets que as sustentam e validadas.
5. Evoluir o leitor web para uma ferramenta de comparação entre polos e comunidades, com sínteses, assinaturas e uma explicação acessível do método.
6. Avaliar a ferramenta com pesquisadores da área num grupo focal, que também servirá à rotulagem manual dos polos, e publicá-la ao final.

**Fora do escopo** (trabalhos futuros): pontuação ideológica de usuários, análise longitudinal de radicalização, acompanhamento de usuários entre eventos e exportação de dados pela ferramenta.

---

## 2. Referencial Teórico

Este capítulo retoma e estende o referencial do TCC1 em cinco frentes. As três primeiras vêm do TCC1: os conceitos que enquadram o problema, a literatura sobre polarização no Twitter brasileiro e a fundamentação da rede de co-retweet. As duas últimas são novas e sustentam as extensões do TCC2: a robustez da detecção de comunidades e os métodos digitais e ferramentas para pesquisa em comunicação.

### 2.1 Bolhas de filtro e câmaras de eco ⟦corrigido⟧

Duas formulações próximas, e muitas vezes confundidas, descrevem a homogeneização dos ambientes informacionais digitais. Pariser [2] cunhou a expressão *filter bubble* (bolha dos filtros) para o universo informacional individual que filtros algorítmicos montam para cada usuário com base em seu comportamento anterior. Para Pariser, essa bolha tem três propriedades novas: cada pessoa está sozinha nela, ela é invisível e não é escolhida por quem está dentro ([2], p. 8–9). A noção de câmara de eco, desenvolvida por Sunstein [3], [4], enfatiza outro mecanismo: a tendência de pessoas com visões semelhantes se agruparem e, deliberando entre iguais, se deslocarem para posições mais extremas (polarização de grupo).

Este trabalho não separa os dois mecanismos. A rede de co-retweet registra um resultado agregado, ou seja, o que cada usuário escolheu amplificar a partir do que lhe chegou. Por isso a câmara de eco é tratada aqui como **propriedade estrutural mensurável da rede**, e não como hipótese sobre o que cada usuário viu ou pensou. Essa postura acompanha a crítica de que o termo costuma ser usado sem definição operacional e de que o isolamento completo é empiricamente raro ([12], p. 4–5). A hermeticidade é, assim, declarada como medida de estrutura, não de exposição.

### 2.2 Polarização no Twitter político brasileiro ⟦mantido + corrigido + novo⟧

A polarização política no Twitter brasileiro está bem documentada, com contribuição central do grupo de Raquel Recuero. Na eleição de 2018, redes de interação (retweets, menções e respostas) mostraram dois grupos fracamente conectados entre si, com veículos hiperpartidários circulando quase só em um deles [10], [11]. No debate sobre a hidroxicloroquina, uma rede de compartilhamento de links revelou dois clusters fortemente demarcados, com dietas informativas distintas [12].

Essa literatura caracteriza a polarização brasileira como **assimétrica**, e convém fixar o sentido do termo, porque ele será usado aqui de outra forma. Nos trabalhos citados, a assimetria se refere à diferença de dieta informativa e de radicalização entre os polos [9], [12], de centralização [10] ou de composição dos atores influentes [13]. Nenhum deles mede a organização interna dos polos, que é o sentido em que o TCC2 usa a palavra. ⟦A afirmação sobre [9] depende de leitura do texto integral, pendente.⟧

O trabalho mais próximo é o de Interian e Rodrigues [17]. Numa rede de retweets dirigida com mais de quinze milhões de tweets do período eleitoral de 2022, eles mostraram que a comunidade de direita, embora menor, respondia em média por 44,1% da modularidade, contra 13,4% da esquerda. Por outro método, a homologia persistente aplicada a outra base da mesma eleição também encontra uma topologia bipolar recorrente [18].

Três trabalhos recentes deslocam o foco da estrutura para o **conteúdo**, como pretende o TCC2:

- Hoffmann da Silva e Recuero [13] mostraram que, na conversa sobre a "Carta pela Democracia" (agosto de 2022), os dois polos mobilizaram a palavra "democracia" com sentidos opostos.
- Recuero e Soares [14] mostraram que as contas oficiais dos candidatos construíram o "outro" de formas assimétricas no segundo turno.
- Bastos e Recuero [19] documentaram a escalada de declarações questionando o processo eleitoral. Os próprios autores ressalvam que seus resultados são descritivos.

A configuração revelada pela revisão estrutural do TCC2 (dois polos igualmente herméticos, que diferem na organização interna) não é antecipada por nenhum dos trabalhos revisados. Ela é tratada como extensão sem precedente direto.

### 2.3 Da rede de retweet à rede de co-retweet ⟦mantido + corrigido⟧

A identificação de comunidades políticas pelo retweet parte da premissa de que o retweet funciona, em geral, como endosso ([7], p. 2). Conover et al. mostraram que a rede de retweets do Twitter político americano se divide em dois grupos segregados [6]. Em trabalho subsequente, mostraram que o rótulo de comunidade nessa rede prevê o alinhamento político dos usuários com cerca de 95% de acurácia [7].

A rede dirigida exige conhecer o autor de cada tweet amplificado, informação ausente no dataset [1]. A rede de co-retweet contorna isso ligando dois usuários pelo conjunto de tweets que ambos retuitaram. A operação tem precedente no acoplamento bibliográfico, introduzido por Kessler [22]: dois documentos estão relacionados quando citam referências em comum. Formalizada pela literatura posterior, essa operação equivale à projeção de uma matriz de incidência [23], [24]. Sendo *M* a matriz usuário × tweet, a contagem de tweets em comum é *C = M·Mᵀ*. A analogia com o acoplamento é proposta deste trabalho.

A contagem bruta precisa ser normalizada. O TCC1 adotou o índice de Jaccard, de uso estabelecido em análise de co-citação [26]. Van Eck e Waltman [25] argumentam, porém, que medidas como Jaccard e cosseno não normalizam dados de coocorrência de forma ideal. A escolha é analítica e será declarada como tal. Projeções bipartidas ponderadas por similaridade têm precedente na projeção de redes de retweet sobre usuários [29], no co-compartilhamento de notícias [30] e na detecção de redes coordenadas, inclusive por co-retweet [27].

As comunidades resultantes são chamadas de **comunidades discursivas**: grupos de contas ligados por padrões de amplificação, identificados sem rótulo prévio de identidade ou orientação [33], [34]. Isso combina com a decisão de não rotular os polos *a priori*.

### 2.4 Robustez da detecção de comunidades ⟦novo⟧

As comunidades são detectadas pelo algoritmo de Leiden [35]. Há três razões conhecidas para não tratar uma partição específica como verdade:

- **Degenerescência:** a modularidade tem muitas partições quase ótimas e estruturalmente distintas [37].
- **Limite de resolução:** a modularidade tem uma escala intrínseca [38]. O Constant Potts Model não tem esse limite e serve de contraprova [39].
- **Variabilidade entre execuções:** algoritmos estocásticos produzem partições diferentes a cada execução. O *consensus clustering* agrega várias execuções e permite medir a robustez de cada comunidade [41].

Se esses testes divergirem, o modelo de blocos estocásticos aninhado com seleção por descrição mínima permite decidir estatisticamente se uma subdivisão é sustentada pelos dados [40].

### 2.5 Métodos digitais e a pesquisa em comunicação ⟦novo⟧

Recuero [21] sistematiza os métodos digitais para o estudo do discurso em plataformas e destaca três pontos que orientam o TCC2:

- a plataforma é agente na produção do discurso, não só fonte de dados;
- o campo tende a métodos mistos, que combinam mapeamento quantitativo e leitura qualitativa, com papel central da visualização;
- há limites práticos e éticos, como o fim do acesso gratuito à API do Twitter e a exposição de sujeitos em dados buscáveis.

A literatura brasileira já caracteriza clusters pela leitura manual de seus conteúdos e atores centrais [12], [13]. O TCC2 mantém a leitura humana como validação, mas inverte a ordem: as sínteses de conteúdo são geradas com apoio de modelo de linguagem, ancoradas nas fontes, e o rótulo dos polos é atribuído depois, pelo grupo focal. ⟦Falta referência metodológica sobre grupo focal, por exemplo Gatti (2005) ou Krueger e Casey.⟧

### 2.6 Ferramentas existentes e posicionamento ⟦novo — [T*] a auditar⟧

| Ferramenta | O que faz | O que não faz, em relação ao TCC2 |
|---|---|---|
| **Gephi** [T1] | Visualização e análise exploratória de grafos. | É genérica e voltada a quem constrói o grafo. Não liga comunidades ao conteúdo amplificado. |
| **NodeXL** [T2] | Coleta e análise de redes de mídias sociais, com relatórios de grupos, hashtags e URLs. | Parte de redes de interação e de coleta própria. Não trabalha com dataset desidratado nem com co-retweet. |
| **4CAT** [T3] | Captura e análise de dados de plataformas para pesquisa em humanidades e comunicação. | É uma infraestrutura de análise. Não publica uma análise feita para exploração por terceiros. |
| **Hoaxy / OSoMe** [T4] | Visualização pública da difusão de conteúdo no Twitter. | O foco é a difusão de itens, não a estrutura de comunidades nem a comparação entre polos ao longo de eventos. |

A aplicação do TCC2 não compete com essas ferramentas como software de análise. Ela é a **publicação interativa de uma análise específica**, que permite a pessoas de fora da computação percorrer o caminho do grafo ao conteúdo: comparar o que cada comunidade amplificou, encontrar os tweets-assinatura e ler sínteses que remetem às fontes.

---

## 3. Metodologia

O trabalho segue seis etapas em ordem de dependência. Cada etapa tem um entregável verificável e é implementada como estágio da pipeline existente, com testes, orquestrada por um notebook da fase.

### E1. Revisão estrutural (sem custo de API)

- **Métricas no nível do polo.** Calcular a hermeticidade de cada super-polo ao lado da hermeticidade por comunidade. A modularidade e a assortatividade deixam de ser usadas para comparar eventos, porque medem a partição em comunidades e misturam abertura entre polos com subdivisão interna.
- **Robustez das subdivisões.** Para cada par de comunidades entrelaçadas no mesmo polo:
  - várias execuções do Leiden com seeds distintas, medindo coassignação e similaridade entre partições (ARI/NMI);
  - varredura do parâmetro de resolução, com o CPM como contraprova [38], [39];
  - repetição em alguns valores de τ;
  - SBM aninhado [40], apenas se os testes anteriores divergirem.
- **Sinais já disponíveis:** horário de atividade, histórico dos membros em eventos anteriores e nível de atividade.
- O critério de "subdivisão robusta" é **registrado antes da execução**, em `docs/decisoes-metodologicas.md`, para não ser ajustado ao resultado.
- *Entregável:* tabela estrutural revisada e um veredito por par (subcomunidade robusta ou artefato).

### E2. Hidratação seletiva (saldo da API do X)

- Primeiro, para os pares considerados robustos na E1, hidratar os tweets **discriminantes**: os mais concentrados em um dos lados do par, acima de um piso de volume. O critério atual de seleção, por volume, captura sobretudo o conteúdo compartilhado pelos dois lados.
- Depois, com o saldo restante, hidratar o top-K de um quinto evento (e talvez um sexto) do mesmo dataset, escolhido pela relevância para o arco e processado do zero pela pipeline. Isso também demonstra que a pipeline pode ser reaplicada.
- *Entregável:* banco de hidratação ampliado, com a atrição (tweets indisponíveis) registrada.

### E3. Camada de conteúdo

- **Tweets-assinatura.** Para cada tweet, calcular a fração de seus retweets vinda de cada polo e de cada comunidade, sobre o log completo de retweets do evento (sem custo de API). As assinaturas são os tweets concentrados em um lado, acima de um piso de volume.
- **Sínteses narrativas** por evento e comunidade, geradas por modelo de linguagem a partir do top-K e das assinaturas hidratadas:
  - descrevem temas, protagonistas e antagonistas, a tese central e a linha do tempo;
  - cada afirmação cita os identificadores dos tweets que a sustentam;
  - não usam rótulo ideológico prévio.
- **Validação das sínteses:**
  - checagem automática de que os tweets citados existem e pertencem à comunidade;
  - comparação item a item com a leitura manual já realizada (relatório de leitura narrativa preliminar): o que o modelo capturou, omitiu ou inventou;
  - revisão manual.
- Modelo, versão e prompt ficam registrados.
- *Entregável:* sínteses validadas e assinaturas exportadas para a aplicação.

### E4. Ferramenta (versão para o grupo focal)

Evolução do leitor web existente, mantendo dados estáticos e nenhum backend:

- visão por polo e por comunidade;
- comparação lado a lado (similaridade, conteúdo exclusivo, assinaturas);
- sínteses com citações que levam ao tweet;
- uma página que explica o método em linguagem acessível (o que é co-retweet, o que é um polo, o que a hermeticidade mede);
- cuidado ético na exibição de tweets [21].

### E5. Grupo focal

- **Participantes:** 3 a 5 pessoas de comunicação e ciência política.
- **Protocolo:** tarefas abertas sobre a ferramenta, com fala em voz alta (*think-aloud*) seguida de discussão. Exemplos: "o que este polo disse no 8 de janeiro?", "o que ele não viu?", "estas duas comunidades são diferentes?".
- **Saídas:**
  - dificuldades de interpretação;
  - **rotulagem manual dos polos** pelos participantes;
  - funcionalidades sugeridas.
- **Ética:** termo de consentimento livre e esclarecido. A necessidade de apreciação por comitê de ética será confirmada com a orientadora ⟦decidir⟧.

### E6. Iteração, publicação e redação

- Implementar as sugestões viáveis do grupo focal e publicar a ferramenta.
- Redigir o artigo final no formato IEEE.

### Uso de inteligência artificial ⟦novo⟧

Em atendimento às diretrizes, o uso de IA é declarado em dois planos:

- **Como componente do método:** o modelo de linguagem gera as sínteses da E3, que são validadas como descrito acima.
- **Como apoio ao trabalho:** assistentes de IA são usados no desenvolvimento de código, na pesquisa bibliográfica e na revisão do texto, sob supervisão do autor. As referências são conferidas nas fontes primárias.

---

## 4. Resultados Esperados

Ao final do TCC2, espera-se ter produzido resultados em três frentes.

**Analítica:**

- uma caracterização revisada da forma da polarização nos quatro eventos, no nível dos polos e das subdivisões internas, com veredito sobre a robustez de cada subdivisão;
- para cada evento e comunidade, a narrativa amplificada e os tweets-assinatura, que respondem empiricamente a "o que um polo vê que o outro não vê";
- uma discussão sobre a hipótese de realidades paralelas no caminho até o 8 de janeiro.

Resultados negativos são considerados resultados. Por exemplo, subdivisões que se revelem artefatos, ou polos que compartilhem mais conteúdo do que o esperado.

**Tecnológica:**

- a pipeline estendida (revisão estrutural, assinaturas e sínteses ancoradas), documentada e testada;
- a aplicação web publicada, com comparação entre polos e explicação do método;
- uma medida de qualidade das sínteses (taxa de ancoragem e concordância com a leitura manual).

**Comunicação e validação:**

- o relato do grupo focal: o que pesquisadores da área conseguiram ou não interpretar com a ferramenta, os rótulos atribuídos aos polos e as funcionalidades sugeridas;
- o artigo final, com a ferramenta como meio de disseminação da análise.

---

## 5. Etapas e Cronograma

Semanas relativas ao início do TCC2 ⟦ajustar às datas do Moodle: entrega da proposta, pitch parcial e pôster/entrega final⟧.

| Semana | Atividade |
|---|---|
| S1 | Redação e entrega da proposta. Registro do critério de robustez (E1). |
| S2–S3 | E1: métricas por polo e testes de robustez; veredito por par. |
| S3–S4 | E2: hidratação seletiva dos pares robustos; seleção e processamento do 5º evento. |
| S4–S6 | E3: tweets-assinatura, sínteses por modelo de linguagem e validação. |
| S4–S5 | Protocolo do grupo focal, consentimento, verificação da necessidade de comitê de ética e recrutamento. |
| S5–S7 | E4: ferramenta, versão para o grupo focal. |
| S7 | Apresentação parcial (pitch em vídeo). |
| S8 | E5: sessões do grupo focal. |
| S9 | E5: análise do grupo focal e consolidação dos rótulos. |
| S9–S10 | E6: iteração e publicação da ferramenta. |
| S10–S12 | Redação do artigo IEEE, pôster e apresentação final. |

---

## 6. Referências Bibliográficas

Lista consolidada e corrigida em `docs/guia-citacoes-tcc2.md` (§4), numerada provisoriamente. Na versão final, renumerar pela ordem de citação e acrescentar [T1]–[T4] e a referência de grupo focal após auditoria.

---

## Pendências do rascunho

- **Margem do 2º turno:** citar o resultado oficial do TSE (§1.1).
- **Soares, Recuero e Zago 2019 [9]:** obter o texto integral (§2.2).
- **Kessler [22]:** obter pelo Portal CAPES (§2.3).
- **Sunstein, *Republic.com*:** ainda não lido. A §2.1 usa #Republic e o artigo de 2002.
- **Ferramentas [T1]–[T4]:** auditar as referências candidatas (Bastian et al. 2009; Hansen, Shneiderman e Smith 2011; Peeters e Hagen 2022; Shao et al. 2016).
- **Grupo focal:** escolher a referência metodológica e confirmar a questão do comitê de ética.
- **Decisões ⟦decidir⟧:** título; manter ou não o parágrafo da Covid; datas do cronograma.
- **Tamanho:** cortar para caber em 10 páginas. Candidatos: §2.2 (lista de trabalhos recentes), §2.4 (condensar em um parágrafo) e §1.1.
- **Total de linhas do dataset:** recontar localmente (≈9,39 M) se o número for citado.
