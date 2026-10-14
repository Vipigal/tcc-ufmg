# PROPOSTA DE TCC — MSI II

## Capa

- **Título:** Análise estrutural das comunidades no Twitter brasileiro durante o ciclo eleitoral de 2022
- **Tipo de pesquisa:** Mista (científica e tecnológica)
- **Aluno:** Vinícius Pinho Galvão
- **Orientadora:** Eliane Cristina de Freitas Rocha
- **Coorientador:** —
- **Local e data:** Belo Horizonte, outubro de 2026

---

## 1. Introdução

O segundo turno da eleição presidencial de 2022 terminou com a vitória de Lula sobre Jair Bolsonaro por margem estreita. Pouco mais de dois meses depois, em 8 de janeiro de 2023, apoiadores de Bolsonaro invadiram e depredaram as sedes dos três poderes em Brasília, contestando o resultado das urnas [1]. Para boa parte do país, esses fatos representavam um ataque à democracia. Para outra parcela, eram um ato legítimo de protesto. Não havia vocabulário comum entre as duas leituras.

Que o Brasil está dividido é quase um consenso intuitivo. O que é menos óbvio, e mais interessante de investigar, é a **forma** dessa divisão. Dois grupos opostos podem trocar informação o tempo todo ou se fechar em ambientes paralelos que quase não se tocam, e esses dois cenários têm consequências diferentes. No Twitter, a experiência de cada usuário é moldada pelo que ele escolhe amplificar e pelo que os algoritmos lhe entregam [2], [3]. Assim, duas pessoas expostas ao mesmo evento podem ter contato com versões quase opostas dele. Interian e Rodrigues [4] observaram um isolamento acentuado da comunidade de direita no Twitter durante a eleição de 2022 e levantaram a hipótese de que ele tenha influenciado o 8 de janeiro. Bastos e Recuero [1] acrescentam que a narrativa de fraude foi também oferecida pela própria liderança, ao longo da campanha. A hipótese deste trabalho é que a divergência foi construída ao longo do ciclo eleitoral, e não de uma vez no 8 de janeiro. Por isso são analisados quatro eventos que formam um arco de tensionamento institucional:

- a mobilização de 7 de setembro de 2022;
- o caso Roberto Jefferson, em 23 de outubro, quando o ex-deputado, aliado de Bolsonaro, reagiu a tiros e granadas a uma ordem de prisão do STF [5]–[7];
- o dia do segundo turno, 30 de outubro;
- a invasão de 8 de janeiro de 2023.

**O que foi feito no MSI I.** O objetivo geral do TCC1 era caracterizar a estrutura das comunidades políticas no Twitter brasileiro em torno do 8 de janeiro e torná-la compreensível por uma visualização interativa. O trabalho partiu do dataset desidratado Tweet_Eleições_2022 [8]. Como esse dataset não registra o autor dos tweets retuitados, construiu-se uma rede de co-retweet: dois usuários se ligam pela coincidência do que retuitaram, com peso dado pelo índice de Jaccard, e as comunidades são detectadas pelo algoritmo de Leiden. Os resultados relatados foram:

- uma pipeline reutilizável aplicada aos quatro eventos, com análise de sensibilidade dos parâmetros;
- a caracterização estrutural: nos três eventos de confronto a rede se organiza em dois super-polos, com uma comunidade quase lacrada (hermeticidade de 0,97 a 0,999), achado consistente com o isolamento de uma das comunidades descrito em [4]; o dia do segundo turno apresentou a menor segregação pelas métricas de partição (modularidade e assortatividade).

O relatório do TCC1 apontou o próprio limite: as comunidades eram objetos estruturais, ainda sem conteúdo. Entre a entrega do relatório e esta proposta, deu-se o primeiro passo dessa camada: os tweets mais retuitados de cada comunidade foram hidratados seletivamente, um leitor web em versão beta foi construído e uma leitura manual preliminar desse material foi registrada. Essa leitura é insumo das perguntas abaixo e da validação prevista na E3.

**Problema e perguntas.** A pergunta central se mantém: *o Twitter brasileiro estava polarizado no ciclo de 2022, e qual é a forma dessa polarização?* Uma revisão inicial dos resultados do TCC1, feita sobre os grafos já gerados, mostrou que, quando se somam as comunidades de cada lado, os dois super-polos são herméticos em grau comparável (0,98 a 0,9999 nos três eventos de confronto) e que o polo subdividido é tão ou mais fechado que o monolítico. A diferença entre eles está na organização interna: um polo aparece monolítico e o outro subdividido, e o lado subdividido muda de evento para evento; no 7 de setembro há ainda um pequeno terceiro grupo, coeso e distinto dos dois polos. No dia do segundo turno, o mesmo cálculo mostra dois polos fechados de tamanhos muito desiguais (96,6% e 3,4% dos nós), a reler junto com o efeito do filtro por palavra-chave do evento. Essa medição é preliminar e será incorporada à pipeline na E1. O TCC2 desdobra a pergunta central em quatro:

- **(P1)** as subdivisões internas dos polos são comunidades distintas ou artefatos da detecção?
- **(P2)** o que cada polo diz sobre cada evento?
- **(P3)** o que um polo vê que o outro não vê?
- **(P4)** os ambientes são distintos a ponto de constituírem realidades paralelas?

Há também um problema de comunicação. Análises desse tipo costumam chegar a pesquisadores de outras áreas como resultados estáticos e difíceis de interrogar, e o leitor web do TCC1 se mostrou confuso para quem não vem da computação. A tese tecnológica do trabalho é que essa análise deve ser **navegável**, para que pesquisadores de comunicação e de ciência política consigam entender o método e explorar os achados por conta própria.

**O que muda em relação ao plano do MSI I.** O relatório do TCC1 previa rotular as comunidades como esquerda e direita por um score ideológico de autores, medir a radicalização de um painel de usuários ao longo do arco e animar o 8 de janeiro hora a hora. Esses itens saem do escopo. A leitura preliminar mostrou que "esquerda" e "direita" descrevem mal os polos encontrados (um deles reúne candidatos de centro e a imprensa de referência), e por isso os rótulos passam a emergir do conteúdo e da leitura dos participantes do grupo focal, não de uma classificação prévia. O painel de radicalização e o controle temporal ficam como trabalhos futuros.

**Objetivo geral.** Caracterizar a forma e o conteúdo da polarização no Twitter brasileiro ao longo do arco eleitoral de 2022–2023 e disponibilizar essa análise numa aplicação interativa compreensível e explorável por pesquisadores de comunicação e ciência política.

**Objetivos específicos (MSI II):**

1. Revisar a caracterização estrutural no nível dos polos e testar a robustez das subdivisões internas.
2. Hidratar seletivamente os tweets que discriminam as subdivisões robustas e, se o orçamento permitir, um quinto evento.
3. Identificar os tweets-assinatura de cada polo e de cada comunidade.
4. Produzir sínteses narrativas por evento e comunidade, com apoio de modelo de linguagem, ancoradas nos tweets que as sustentam e validadas.
5. Evoluir o leitor web para uma ferramenta de comparação entre polos e comunidades.
6. Avaliar a ferramenta num grupo focal com pesquisadores da área e publicá-la.

---

## 2. Referencial Teórico

**Bolhas e câmaras de eco.** Pariser [2] chamou de *filter bubble* o universo informacional individual que os filtros algorítmicos montam para cada usuário, de forma invisível e sem que ele escolha. A noção de câmara de eco, de Sunstein [3], enfatiza outro mecanismo: a homofilia, isto é, a tendência de pessoas semelhantes se agruparem e, deliberando entre iguais, se polarizarem. A rede de co-retweet registra o resultado agregado dos dois mecanismos, ou seja, o que cada usuário amplificou a partir do que lhe chegou. Por isso, a câmara de eco é tratada aqui como propriedade estrutural mensurável, e não como hipótese sobre o que cada usuário viu. Isso responde à crítica de que o termo costuma ser usado sem definição operacional e de que o isolamento completo é raro [9].

**Polarização no Twitter brasileiro.** O grupo de Raquel Recuero documentou, no debate sobre a hidroxicloroquina na pandemia, dois clusters fortemente demarcados e com dietas informativas distintas: num deles a desinformação circulava associada a veículos hiperpartidários; no outro predominavam veículos jornalísticos e institucionais [9]. Nessa literatura, "polarização assimétrica" designa diferenças de dieta informativa entre os polos [9]. O sentido usado aqui é outro: assimetria de organização interna, que esse trabalho não mede. O estudo mais próximo deste é o de Interian e Rodrigues [4], que, numa rede de retweets dirigida com mais de 15 milhões de tweets de 2022, mostraram que a comunidade de direita respondia por 44,1% da modularidade, contra 13,4% da esquerda. Estudos recentes passam da estrutura ao conteúdo. Hoffmann da Silva e Recuero [10] mostraram que os dois polos usaram "democracia" com sentidos opostos em agosto de 2022, o que antecipa a pergunta "o que cada polo diz". Bastos e Recuero [1] documentaram a escalada da narrativa de fraude entre as lideranças.

**Da rede de retweet ao co-retweet.** Conover et al. [11] mostraram que a rede de retweets do Twitter político americano se divide em dois grupos segregados, com base na premissa de que o retweet funciona, em geral, como endosso. A rede dirigida exige conhecer o autor de cada tweet, informação ausente no dataset [8]. A rede de co-retweet liga usuários pelo conjunto de tweets que retuitaram em comum. Ela segue a lógica do acoplamento bibliográfico de Kessler [12], em que dois documentos são próximos quando citam as mesmas referências; formalmente, é a projeção da matriz de incidência usuário × tweet sobre o lado dos usuários, *C = M·Mᵀ*. A analogia é proposta deste trabalho. A normalização por Jaccard é uma escolha analítica, declarada como tal. As comunidades resultantes são chamadas aqui de **comunidades discursivas**: grupos identificados por padrões de amplificação, sem rótulo prévio de orientação.

**Robustez da detecção de comunidades.** Uma partição produzida pelo Leiden [13] não deve ser tomada como verdade, por três motivos bem estabelecidos na literatura de detecção de comunidades:

- a modularidade admite muitas partições quase ótimas e distintas entre si;
- a modularidade tem um limite de resolução, que o Constant Potts Model não tem;
- execuções estocásticas variam, e o *consensus clustering* permite medir a robustez de cada comunidade.

Se esses testes divergirem, o modelo de blocos estocásticos aninhado, com seleção por descrição mínima, oferece um critério independente para avaliar se uma subdivisão é sustentada pelos dados.

**Métodos digitais e ferramentas existentes.** A pesquisa em comunicação sobre plataformas tende a métodos mistos, que combinam mapeamento quantitativo e leitura qualitativa, e a literatura brasileira caracteriza clusters pela leitura manual de seus conteúdos e atores centrais [9], [10]. O TCC2 mantém a leitura humana como validação, feita no grupo focal. As ferramentas mais usadas na área resolvem problemas vizinhos:

| Ferramenta | O que faz | Diferença em relação a este trabalho |
|---|---|---|
| Gephi[^gephi] | Visualização e análise exploratória de grafos | Genérica; não liga comunidades ao conteúdo amplificado |
| NodeXL[^nodexl] | Coleta e análise de redes de mídias sociais | Parte de coleta própria e de redes de interação; não trabalha com dados desidratados |
| 4CAT[^4cat] | Captura e análise de dados de plataformas | Infraestrutura para quem analisa; não publica uma análise para terceiros explorarem |
| Hoaxy[^hoaxy] | Visualização pública da difusão de conteúdo | Foco na difusão de itens, não em comunidades nem na comparação entre polos |

[^gephi]: https://gephi.org
[^nodexl]: https://www.smrfoundation.org/nodexl/
[^4cat]: https://4cat.nl
[^hoaxy]: https://hoaxy.osome.iu.edu

A aplicação proposta não compete com essas ferramentas como software de análise. Ela é a **publicação interativa de uma análise**, que leva o leitor do grafo ao conteúdo.

---

## 3. Metodologia

São seis etapas, em ordem de dependência. Cada uma é implementada como estágio testado da pipeline existente.

**E1. Revisão estrutural.**
- Calcular a hermeticidade por super-polo, ao lado da hermeticidade por comunidade.
- Abandonar a modularidade e a assortatividade como métricas de comparação entre eventos, porque misturam abertura entre polos com subdivisão interna.
- Para cada par de comunidades entrelaçadas, testar a robustez: várias seeds do Leiden (com coassignação e ARI/NMI), varredura de resolução com o CPM como contraprova, variação do limiar de backbone e, se necessário, o SBM aninhado.
- Registrar o critério de "subdivisão robusta" antes da execução.
- *Entregável:* tabela estrutural revisada e um veredito por par.

**E2. Hidratação seletiva.**
- Com o saldo da API do X, hidratar primeiro os tweets discriminantes dos pares robustos, isto é, os mais concentrados em um dos lados.
- Com o saldo restante, hidratar um quinto evento do mesmo dataset, o que também demonstra que a pipeline pode ser reaplicada.

**E3. Camada de conteúdo.**
- *Tweets-assinatura:* para cada tweet, calcular a fração dos retweets vinda de cada polo e de cada comunidade, sobre o log completo, acima de um piso de volume.
- *Sínteses narrativas por modelo de linguagem:* temas, protagonistas, antagonistas e tese central de cada comunidade em cada evento. Cada afirmação cita os tweets que a sustentam, e nenhuma síntese recebe rótulo ideológico prévio.
- *Validação:* checagem automática das citações, comparação com a leitura manual já realizada (o que foi capturado, omitido ou inventado) e revisão humana.

**E4. Ferramenta.** Evolução do leitor web, com dados estáticos:
- comparação lado a lado de polos e comunidades;
- tweets-assinatura;
- sínteses com links para os tweets;
- explicação acessível do método;
- cuidado ético na exibição de tweets.

**E5. Grupo focal.**
- Três a cinco pesquisadores de comunicação e ciência política realizam tarefas abertas na ferramenta, falando em voz alta enquanto a usam, seguidas de discussão.
- *Saídas:* dificuldades de interpretação, rotulagem manual dos polos e funcionalidades sugeridas.
- Participação com termo de consentimento. A necessidade de apreciação por comitê de ética será verificada.

**E6. Iteração e publicação.** Incorporar as sugestões viáveis, publicar a ferramenta e redigir o artigo no formato IEEE.

**Uso de IA.** O modelo de linguagem é componente do método (E3) e é validado como descrito. Assistentes de IA também apoiam o desenvolvimento de código, a pesquisa bibliográfica e a revisão do texto, sob supervisão do autor, com todas as referências conferidas nas fontes.

---

## 4. Resultados Esperados

- **Analíticos:**
  - a forma da polarização nos quatro eventos, revisada no nível dos polos e das subdivisões;
  - para cada evento e comunidade, a narrativa amplificada e os tweets-assinatura, que respondem às perguntas P1 a P4;
  - resultados negativos, como subdivisões que se revelem artefatos, também serão reportados.
- **Tecnológicos:**
  - a pipeline estendida, documentada e testada;
  - a aplicação web publicada;
  - uma medida da qualidade das sínteses (ancoragem e concordância com a leitura manual).
- **De validação:**
  - o relato do grupo focal, com o que os pesquisadores conseguiram interpretar, os rótulos atribuídos aos polos e as melhorias sugeridas;
  - o artigo final.

---

## 5. Etapas e Cronograma

| Semana | Atividade |
|---|---|
| 1 | Entrega da proposta; registro do critério de robustez |
| 2–3 | E1: revisão estrutural e testes de robustez |
| 3–4 | E2: hidratação seletiva e quinto evento |
| 4–6 | E3: tweets-assinatura, sínteses e validação |
| 4–5 | Protocolo do grupo focal, consentimento e recrutamento |
| 5–7 | E4: ferramenta para o grupo focal |
| 7 | Apresentação parcial (pitch) |
| 8–9 | E5: sessões do grupo focal e análise |
| 9–10 | E6: iteração e publicação da ferramenta |
| 10–12 | Redação do artigo, pôster e apresentação final |

---

## 6. Referências Bibliográficas

[1] M. Bastos and R. Recuero, "The insurrectionist playbook: Jair Bolsonaro and the National Congress of Brazil," *Social Media + Society*, vol. 9, no. 4, Art. no. 20563051231211881, 2023, doi: 10.1177/20563051231211881.

[2] E. Pariser, *O Filtro Invisível: O que a Internet Está Escondendo de Você*. Rio de Janeiro: Zahar, 2012.

[3] C. R. Sunstein, *#Republic: Divided Democracy in the Age of Social Media*. Princeton, NJ, USA: Princeton Univ. Press, 2017.

[4] R. Interian and F. A. Rodrigues, "Group polarization, influence, and domination in online interaction networks: A case study of the 2022 Brazilian elections," arXiv:2303.16859, 2023.

[5] Supremo Tribunal Federal, "Ministro Alexandre de Moraes revoga domiciliar e determina nova prisão de Roberto Jefferson," *Notícias STF*, 24 out. 2022. [Online]. Disponível em: https://noticias.stf.jus.br/postsnoticias/ministro-alexandre-de-moraes-revoga-domiciliar-e-determina-nova-prisao-de-roberto-jefferson/

[6] B. Prado and M. Savarese, "Brazil politician, Bolsonaro ally refuses arrest, injures police after firing rifle," The Associated Press, via *Global News*, Oct. 23, 2022. [Online]. Disponível em: https://globalnews.ca/news/9220995/brazil-politician-bolsonaro-ally-refuses-arrest

[7] L. Mendes and T. Angelo, "Jefferson deu 50 tiros de fuzil e jogou 3 granadas, diz PF," *Poder360*, 24 out. 2022. [Online]. Disponível em: https://www.poder360.com.br/justica/jefferson-deu-50-tiros-de-fuzil-e-jogou-3-granadas-diz-pf/

[8] L. Alabarse dos Santos, R. Mendes de Araujo, L. J. da Silva, A. G. D. Correa, O. B. Coelho, and I. C. A. de Oliveira, *Tweet_Eleições_2022: Um dataset de tweets durante as eleições presidenciais brasileiras de 2022* [Dataset], Zenodo, 2024, doi: 10.5281/zenodo.11206577.

[9] R. Recuero, F. B. Soares, and G. Zago, "Polarização, hiperpartidarismo e câmaras de eco: como circula a desinformação sobre COVID-19 no Twitter," *Contracampo*, vol. 40, no. 1, 2021, doi: 10.22409/contracampo.v40i1.45611.

[10] M. L. Hoffmann da Silva and R. Recuero, "Polarized democracies: unveiling distinct perspectives on the concept of Democracy in Brazilian social media political conversations," *Estudos em Comunicação*, no. 41, pp. 3–22, 2025, doi: 10.25768/1646-4974n41v1a01.

[11] M. D. Conover, J. Ratkiewicz, M. Francisco, B. Gonçalves, F. Menczer, and A. Flammini, "Political polarization on Twitter," in *Proc. 5th Int. AAAI Conf. Weblogs and Social Media (ICWSM)*, 2011, pp. 89–96, doi: 10.1609/icwsm.v5i1.14126.

[12] M. M. Kessler, "Bibliographic coupling between scientific papers," *American Documentation*, vol. 14, no. 1, pp. 10–25, 1963, doi: 10.1002/asi.5090140103.

[13] V. A. Traag, L. Waltman, and N. J. van Eck, "From Louvain to Leiden: guaranteeing well-connected communities," *Sci. Rep.*, vol. 9, Art. no. 5233, 2019, doi: 10.1038/s41598-019-41695-z.
