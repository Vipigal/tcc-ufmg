# PROPOSTA DE TCC

## Informações Gerais
* [cite_start]**Título:** Arestas, comunidades e narrativas: análise estrutural da polarização no Twitter brasileiro durante o ciclo eleitoral de 2022 [cite: 2]
* [cite_start]**Aluno:** Vinícius Pinho Galvão [cite: 3]
* [cite_start]**Orientadora:** Eliane Cristina de Freitas Rocha [cite: 3]
* [cite_start]**Tipo de pesquisa:** Científica [cite: 4]
* [cite_start]**Local e Data:** Belo Horizonte, Abril 2026 [cite: 5, 6]

---

## [cite_start]1. Introdução [cite: 7, 8]
[cite_start]O ciclo eleitoral brasileiro de 2022 foi um dos períodos mais polarizados da história política recente do país[cite: 9]. [cite_start]O debate público em torno da disputa entre Lula e Jair Bolsonaro migrou de forma substancial para as plataformas digitais, com o Twitter (atualmente X) ocupando posição central como espaço de circulação de notícias, manifestações políticas e mobilização de apoiadores[cite: 10]. [cite_start]A plataforma serviu simultaneamente como canal oficial de comunicação para políticos, veículos de imprensa e influenciadores, e como ambiente em que narrativas concorrentes sobre os mesmos fatos eram construídas, amplificadas e contestadas[cite: 11].

[cite_start]O desfecho mais visível dessa polarização ocorreu em 8 de janeiro de 2023, quando apoiadores do então ex-presidente Bolsonaro invadiram as sedes dos três poderes em Brasília, num ato de contestação ao resultado eleitoral e às instituições democráticas[cite: 12]. [cite_start]O evento marcou o ápice de um processo de tensão que vinha se acumulando há meses, e tornou explícito o quanto duas parcelas da sociedade brasileira haviam passado a operar a partir de leituras radicalmente distintas da mesma realidade política[cite: 13].

[cite_start]Esse descompasso entre leituras de um mesmo fato é o problema central que este trabalho busca caracterizar[cite: 14]. [cite_start]Para uma parcela significativa dos brasileiros, o Twitter funciona como fonte primária de informação sobre política nacional, e a linha do tempo de cada usuário é moldada por suas próprias escolhas de quem seguir e o que retweetar, em interação com o que o algoritmo da plataforma decide promover[cite: 15]. [cite_start]O resultado prático é que dois usuários expostos ao mesmo evento podem ter experiências de leitura completamente diferentes da realidade[cite: 16].

[cite_start]A hipótese que orienta este trabalho é que essa divergência não surgiu pronta no 8 de janeiro: ela foi construída ao longo do ciclo eleitoral, em uma sequência de eventos em que o descontentamento foi sendo intensificado em uma comunidade enquanto era enquadrado de forma muito distinta na comunidade oposta[cite: 17]. [cite_start]Para investigar essa hipótese, propõe-se analisar não apenas o 8 de janeiro isoladamente, mas também eventos anteriores que compõem o arco narrativo que culmina nele, observando como as comunidades políticas no Twitter se organizaram em torno de cada um deles e como suas leituras divergiram[cite: 18].

Para isso, será utilizado como base o dataset Tweet_Eleições_2022, desenvolvido por Silva et al. (2024)[cite_start], que contém aproximadamente 9,5 milhões de tweets coletados entre abril de 2022 e janeiro de 2023[cite: 20, 21]. [cite_start]O dataset foi desenvolvido com o objetivo de evidenciar a dinâmica de comportamento das redes sociais de acordo com a ocorrência de eventos politicamente relevantes no cenário nacional e noticiados na imprensa, e está organizado em 110 arquivos correspondentes a eventos políticos específicos do período, abrangendo desde discussões pré-eleitorais até a cobertura direta dos ataques de 8 de janeiro em janelas de três horas[cite: 21]. [cite_start]Essa segmentação por evento permite tanto a análise focada de momentos políticos individuais quanto a comparação entre eles, oferecendo cobertura temporal e temática adequada à investigação proposta neste trabalho[cite: 22].

### [cite_start]Objetivos Gerais [cite: 23]
Caracterizar a estrutura das comunidades políticas no Twitter brasileiro em torno do 8 de janeiro de 2023, e desenvolver uma visualização interativa que torne essa estrutura compreensível para um público não-técnico, usando como dataset os tweets coletados por Silva et al. (2024) [cite_start][cite: 23, 24].

### [cite_start]Objetivos Específicos [cite: 25]
1. Desenvolver uma pipeline computacional reutilizável que receba como entrada um arquivo do dataset Silva et al. (2024) [cite_start]e produza como saída um grafo de co-retweet com comunidades detectadas e métricas estruturais associadas[cite: 26, 27].
2. [cite_start]Aplicar essa pipeline a quatro eventos políticos do dataset, escolhidos por compor um arco narrativo que culmina no 8 de janeiro: a mobilização de 7 de setembro de 2022, o caso Roberto Jefferson (outubro de 2022), o debate sobre democracia no dia do segundo turno (30 de outubro de 2022) e os ataques de 8 de janeiro de 2023[cite: 28].
3. [cite_start]Hidratar seletivamente um conjunto reduzido de tweets originais mais retuitados em cada evento para permitir a classificação manual de fontes ideológicas e a caracterização das narrativas predominantes em cada comunidade[cite: 29].
4. [cite_start]Construir uma aplicação web interativa que permita a um leitor explorar os grafos resultantes, comparar lado a lado os tweets dominantes em cada comunidade, e observar a evolução temporal do grafo do 8 de janeiro ao longo do dia[cite: 30].

---

## [cite_start]2. Referencial Teórico [cite: 32, 33]

### 2.1. [cite_start]Bolhas de eco e câmaras de eco [cite: 34]
[cite_start]O conceito de bolhas de eco, popularizado por Pariser (2011) como filter bubble, descreve o fenômeno em que um usuário de redes sociais passa a consumir predominantemente conteúdo que reforça suas próprias opiniões e visões de mundo[cite: 35]. [cite_start]Isso acontece por uma combinação de dois fatores: as escolhas do próprio usuário, que tende a seguir contas e amplificar conteúdos com os quais já concorda; e a ação dos algoritmos de recomendação das plataformas, que aprendem essas preferências e passam a entregar mais conteúdo do mesmo tipo[cite: 36, 37]. [cite_start]Com o tempo, o resultado é um ambiente informacional cada vez mais homogêneo, em que o usuário tem pouco contato com perspectivas divergentes[cite: 38]. 

[cite_start]No contexto político, isso tem efeitos concretos[cite: 39]. [cite_start]Comunidades opostas passam a habitar realidades informacionais paralelas, em que os mesmos fatos são descritos com vocabulário, ênfase e enquadramento radicalmente diferentes[cite: 39]. [cite_start]Esse fenômeno é o que torna possível que um mesmo evento, como os ataques de 8 de janeiro, seja interpretado por um lado como um atentado à democracia e pelo outro como uma manifestação patriótica, sem que haja um espaço comum em que essas leituras se confrontam de forma produtiva[cite: 40].

### 2.2. [cite_start]Análise de polarização em redes sociais brasileiras [cite: 41]
[cite_start]A análise de polarização política no Twitter brasileiro tem na pesquisadora Raquel Recuero uma de suas principais referências[cite: 42]. [cite_start]Os trabalhos do grupo de Recuero têm mostrado, em diferentes eventos do contexto político nacional como na eleição presidencial de 2018 (Recuero, Soares e Gruzd, 2020; Soares e Recuero, 2021) à circulação de desinformação sobre a pandemia de Covid-19 (Recuero, Soares e Zago, 2021), que as comunidades de esquerda e de direita no Twitter formam estruturas claramente segmentadas, com pouca interação entre si, e que essas estruturas são detectáveis a partir do padrão de retweets entre os usuários[cite: 43]. [cite_start]A premissa metodológica é que o retweet funciona como uma forma de endosso: ao retuitar uma mensagem, o usuário sinaliza concordância ou pelo menos disposição a amplificar aquele conteúdo dentro de sua própria rede[cite: 44]. [cite_start]Essa noção é a base da maior parte dos estudos quantitativos sobre polarização em redes sociais, incluindo este trabalho[cite: 45].

### 2.3. [cite_start]Rede de co-retweet como ferramenta de análise [cite: 47]
[cite_start]A maneira mais direta de estudar polarização em uma rede de retweets é construir um grafo em que os usuários são os nós e existe uma aresta dirigida de A para B quando A retuita B[cite: 48]. Conover et al. (2011)[cite_start], em um dos trabalhos seminais sobre o tema, aplicaram essa abordagem ao Twitter político americano e demonstraram que ela revela duas comunidades claramente segregadas, com pouquíssima interação entre si[cite: 48, 49]. [cite_start]Essa construção, no entanto, exige conhecer o autor de cada tweet retuitado, informação que não está disponível diretamente no dataset utilizado neste trabalho, e cuja recuperação completa via API teria custo proibitivo[cite: 50].

[cite_start]A alternativa adotada é a construção de uma rede de co-retweet (co-retweet network), em que dois usuários são ligados por uma aresta sempre que compartilham o retweet de um mesmo tweet[cite: 51]. [cite_start]A intuição é simples: usuários que amplificam consistentemente o mesmo material habitam o mesmo ambiente informacional, ainda que não interajam diretamente entre si[cite: 52]. [cite_start]Trabalhos recentes têm aplicado variantes dessa abordagem em diferentes contextos eleitorais[cite: 53]. [cite_start]Pena, Maccarron e O'Sullivan (2025) utilizam co-retweet networks para investigar a polarização no Twitter irlandês em torno do referendo do aborto, demonstrando a capacidade da técnica de revelar comunidades ideologicamente coerentes mesmo sem acesso à cadeia direta de retweets[cite: 54]. Flamino et al. (2023) [cite_start]evidenciaram o aumento da segregação informacional em redes de similaridade derivadas do padrão de retweets no contexto eleitoral americano[cite: 55].

---

## [cite_start]3. Metodologia [cite: 56, 57]

### 3.1. [cite_start]Dataset [cite: 58]
[cite_start]O trabalho utiliza o dataset Tweet_Eleições_2022 (Silva et al., 2024), disponível publicamente no Zenodo sob licença CC-BY 4.0[cite: 59]. [cite_start]O dataset contém aproximadamente 9,47 milhões de tweets coletados entre abril de 2022 e janeiro de 2023, organizados em 110 arquivos por evento político[cite: 60]. [cite_start]O dataset está desidratado por razões éticas; cada registro contém apenas: data de criação, ID do autor da ação, ID da conversa, e campo referenciando tweets com o ID e o tipo de tweet referenciado (retweeted, replied_to, quoted)[cite: 61, 63]. [cite_start]O campo referenced_tweets é central para a construção do grafo[cite: 64]. [cite_start]Quando vazio, indica que o tweet é original[cite: 64]. [cite_start]Quando preenchido, contém o ID do tweet referenciado e o tipo da referência[cite: 65].

[cite_start]Quatro eventos do dataset foram selecionados para análise, escolhidos por compor um arco narrativo de tensionamento institucional progressivo: [cite: 66]
1. [cite_start]Mobilização do 7 de setembro de 2022 com aproximadamente 242 mil tweets; [cite: 67]
2. [cite_start]Caso Roberto Jefferson (out/2022) com aproximadamente 966 mil tweets; [cite: 68]
3. [cite_start]Debate sobre a "democracia" no $2^{\circ}$ turno (30/10/2022): ~299 mil tweets; [cite: 69]
4. [cite_start]Ataques de 8 de janeiro de 2023: ~1,23 milhão de tweets. [cite: 70]

### 3.2. [cite_start]Construção do grafo de co-retweet [cite: 71]
[cite_start]O processamento parte do arquivo CSV de cada evento[cite: 72]. [cite_start]O primeiro passo é filtrar apenas registros com type=retweeted no campo referenced_tweets, descartando respostas, citações e tweets originais[cite: 72]. [cite_start]Dessa filtragem resulta um conjunto de pares (usuário, tweet retweetado)[cite: 73].

A partir desses pares, constrói-se uma representação bipartida do evento na forma de uma matriz bipartida usuário tweet B de dimensões $|U| [cite_start]\times |T|$ onde U é o conjunto de usuários ativos no evento e T é o conjunto de tweets que foram retuitados pelo menos uma vez[cite: 74]. [cite_start]Nesse caso $B_{u,t}=1$ caso o usuário u tenha retweetado o tweet t e 0 caso contrário[cite: 75].

[cite_start]A matriz bipartida é então projetada em um grafo unipartido de usuários: dois usuários são ligados por uma aresta se compartilharam o retweet de pelo menos um tweet em comum[cite: 76]. [cite_start]O peso atribuído à aresta entre os usuários u e v é dado pelo coeficiente de Jaccard sobre os conjuntos de tweets retuitados por cada um: [cite: 77]

$$J(u,v)=\frac{|T_{u}\cap T_{v}|}{|T_{u}\cup T_{v}|}$$

[cite_start]Onde $T_{u}$ denota o conjunto de tweets retuitados pelo usuário u[cite: 77]. [cite_start]O coeficiente varia entre 0 (nenhum tweet em comum) e 1 (os dois usuários retuitaram exatamente o mesmo conjunto de tweets)[cite: 77, 78, 80]. [cite_start]A escolha do Jaccard normaliza a similaridade pela atividade total de cada usuário, evitando que usuários hiperativos apareçam como artificialmente próximos[cite: 80].

### 3.3. [cite_start]Limpeza e detecção de comunidades [cite: 81]
[cite_start]Grafos construídos por projeção bipartida tendem a ser densos e ruidosos[cite: 82]. [cite_start]Para que a análise produza resultados interpretáveis, é necessário aplicar etapas de limpeza[cite: 83]. [cite_start]Usuários que retuitaram poucas vezes no evento (limiar inicial: menos de três retweets) são descartados antes da projeção, o que reduz o número de nós do grafo sem perda informativa relevante[cite: 84, 85].

[cite_start]Após a projeção, retém-se apenas as arestas com peso de Jaccard $\ge \tau$, com $\tau$ inicial $=0,1$[cite: 86]. [cite_start]Esse corte elimina ligações fracas, que conectam usuários com apenas um ou dois tweets em comum entre dezenas de retweets cada um[cite: 87]. [cite_start]A escolha de $\tau$ será acompanhada de análise de sensibilidade em $\tau=0.05$ е $\tau=0.15$, documentada após análise exploratória[cite: 88].

[cite_start]Sobre o grafo resultante é aplicado o algoritmo de Leiden (Traag, Waltman e van Eck, 2019) para detecção de comunidades[cite: 89]. [cite_start]Esse algoritmo busca uma partição dos nós que maximize a modularidade Q, produzindo uma partição dos usuários em comunidades e métricas de separação[cite: 90, 91].

### 3.4. [cite_start]Rotulagem ideológica dos clusters [cite: 92]
[cite_start]Para cada evento, são identificados os tweets que foram mais retuitados dentro do dataset e é feita a hidratação de uma amostra desses tweets via API do X para recuperar o texto e o autor original[cite: 96]. [cite_start]Com essa amostra em mãos, classifica-se os autores em categorias ideológicas amplas (esquerda, direita, mídia jornalística, neutro), e infere-se a posição predominante de cada comunidade detectada no grafo, com base em quem seus membros amplificam com mais frequência[cite: 97]. [cite_start]A classificação dos autores será feita com auxílio de um modelo de linguagem (LLM) em uma primeira passada automática, seguida de revisão manual[cite: 98]. [cite_start]Esse processo será documentado de forma transparente no trabalho final[cite: 99].

### 3.5. [cite_start]Análise narrativa das comunidades [cite: 100]
[cite_start]Uma vez que cada comunidade esteja rotulada, são selecionados os tweets mais retuitados internamente a cada comunidade, e o conteúdo desses tweets é analisado qualitativamente novamente com apoio de um modelo de linguagem para sugerir categorias narrativas predominantes, seguido de revisão manual[cite: 101, 102]. [cite_start]O objetivo é produzir, para cada par (evento, comunidade), uma descrição curta de "o que essa comunidade amplificou neste evento", que possa ser apresentada de forma legível ao leitor final na aplicação web[cite: 103].

### 3.6. [cite_start]Visualização interativa [cite: 104]
[cite_start]O produto final do trabalho inclui uma aplicação web pública, desenvolvida em React, que permite ao leitor explorar os resultados da análise de forma interativa[cite: 105]. [cite_start]A aplicação deve: [cite: 106]
* [cite_start]Oferecer uma representação visual dos grafos de cada evento, com as comunidades coloridas e identificáveis; [cite: 106]
* [cite_start]Permitir que o leitor compare lado a lado o conteúdo amplificado por cada comunidade, tornando palpável a noção de "duas realidades sobre o mesmo fato"; [cite: 107]
* [cite_start]E, no caso do 8 de janeiro, oferecer um controle temporal que permita observar como a rede se preenche ao longo do dia do evento[cite: 108].

---

## [cite_start]4. Resultados Esperados [cite: 111, 112]
[cite_start]Ao final do trabalho, espera-se ter produzido um conjunto integrado de resultados em três frentes: [cite: 113]

* [cite_start]**Na frente analítica:** Espera-se ter caracterizado a estrutura das comunidades políticas no Twitter em torno dos quatro eventos selecionados, com métricas que permitam comparar o grau de polarização entre eles[cite: 114]. [cite_start]A expectativa preliminar é que a polarização se intensifique ao longo do ciclo eleitoral[cite: 115]. [cite_start]Para cada evento, espera-se ter identificado quais foram as narrativas predominantes em cada comunidade[cite: 116].
* [cite_start]**Na frente técnica:** Espera-se ter desenvolvido uma pipeline computacional documentada, capaz de processar arquivos do dataset de ponta a ponta, permitindo reaplicação a outros eventos[cite: 117, 118, 119].
* [cite_start]**Na frente de comunicação:** Espera-se ter disponibilizado publicamente uma aplicação web interativa que torne os resultados acessíveis a um leitor não-especialista, demonstrando como duas comunidades políticas viram e amplificaram leituras diferentes do mesmo conjunto de eventos[cite: 120, 121]. 

[cite_start]A contribuição esperada é instrumental: aplicar técnicas computacionais consolidadas a um problema social concreto, e produzir um artefato visual que torne o problema mais legível para quem não está familiarizado com a literatura técnica[cite: 123].

---

## [cite_start]5. Etapas e Cronograma [cite: 124]
* [cite_start]**Semana 1:** Estudo aprofundado da literatura relevante e experimentação inicial com um arquivo do dataset para validar as escolhas metodológicas[cite: 126].
* [cite_start]**Semana 2:** Implementação da pipeline de construção do grafo: leitura dos arquivos, projeção bipartida, limpeza, detecção de comunidades[cite: 127].
* [cite_start]**Semana 3:** Aplicação da pipeline aos quatro eventos selecionados; geração dos grafos e das métricas estruturais[cite: 128].
* [cite_start]**Semana 4:** Hidratação seletiva dos tweets mais retuitados, classificação dos autores, rotulagem ideológica das comunidades e análise narrativa[cite: 129].
* [cite_start]**Semana 5:** Desenvolvimento da aplicação web interativa e integração com os resultados da análise[cite: 130].
* [cite_start]**Semana 6:** Redação final do documento, revisão, ajustes finais e defesa[cite: 131].

---

## [cite_start]6. Referências Bibliográficas [cite: 132]
1. CONOVER, M. D. et al. Political Polarization on Twitter. [cite_start]In: Proceedings of the Fifth International AAAI Conference on Weblogs and Social Media (ICWSM), 2011[cite: 133, 134].
2. PARISER, E. The Filter Bubble: How the New Personalized Web Is Changing What We Read and How We Think. [cite_start]Nova York: Penguin Press, 2011[cite: 135, 136].
3. PENA, C. B.; MACCARRON, P.; O'SULLIVAN, D. J. P. Finding polarized communities and tracking information diffusion on Twitter: the Irish Abortion Referendum. [cite_start]Royal Society Open Science, 2025[cite: 137, 138].
4. SILVA, L. J. et al. [cite_start]Tweet_Eleições_2022: Um dataset de tweets durante as eleições presidenciais brasileiras de 2022. Zenodo, 2024. DOI: 10.5281/zenodo.11206577[cite: 139].
5. FLAMINO, J. et al. Political polarization of news media and influencers on Twitter in the 2016 and 2020 US presidential elections. Nature Human Behaviour, v. 7, n. 6, p. [cite_start]904-916, 2023[cite: 140, 141].
6. RECUERO, R.; SOARES, F. B.; ZAGO, G. Polarização, hiperpartidarismo e câmaras de eco: como circula a desinformação sobre Covid-19 no Twitter. Contracampo, v. 40, n. [cite_start]1, 2021[cite: 142, 143].
7. SOARES, F. B.; RECUERO, R. Hashtag Wars: Political Disinformation and Discursive Struggles on Twitter Conversations During the 2018 Brazilian Presidential Campaign. Social Media + Society, v. 7, n. [cite_start]2, 2021[cite: 144, 145].
8. RECUERO, R.; SOARES, F. B.; GRUZD, A. Hyperpartisanship, Disinformation and Political Conversations on Twitter: The Brazilian Presidential Election of 2018. Proceedings of the International AAAI Conference on Web and Social Media, v. 14, n. 1, p. [cite_start]569-578, 2020[cite: 146, 147].
9. TRAAG, V. A.; WALTMAN, L.; VAN ECK, N. J. From Louvain to Leiden: guaranteeing well-connected communities. Scientific Reports, v. 9, n. [cite_start]1, 5233, 2019[cite: 148, 149].