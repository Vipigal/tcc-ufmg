# Relatório preliminar de leitura narrativa dos clusters

> **Data:** 2026-09-15.
> **Material:** os top-K hidratados por (evento, cluster) do banco `data/database/hydrated.sqlite`,
> tal como exportados em `data/export/<evento>/tweets.json` (M10). Leitura feita sobre 1.080 slots
> (873 IDs únicos), dos quais 875 slots retornaram texto. Rótulos "polo anti-Bolsonaro" e "polo
> bolsonarista" abaixo são **leitura de conteúdo** feita nesta rodada, não a classificação D7/D8,
> que ainda não existe.
> **Natureza:** norte qualitativo, para orientar a análise completa (§4 da especificação). Tudo em
> "Interpretação" é apontamento datado, amarrado ao estado atual (N por evento, τ=0,10,
> resolution=1,0), não verdade estabelecida. As medições estruturais que aparecem aqui foram
> feitas ad hoc nesta sessão (scripts não versionados) e devem ser reproduzidas na pipeline se
> forem usadas no texto final.

---

## 1. Observações brutas — estrutura

### 1.1. Dois super-polos por evento, um fechado e um fatiado

Fluxo de peso entre clusters com ≥1% dos nós (% do peso total do grafo; matriz simétrica, calculada
sobre `graph_edges.parquet` mapeando `src`/`dst` como **índice posicional** em `graph_nodes.parquet`).

| Evento | Cluster | % nós | intra | fluxo p/ outros do mesmo polo | fluxo p/ outro polo | pureza mediana do top-K |
|---|---|---|---|---|---|---|
| 7/9 | c0 | 46 | 26,5 | c3: 0,42 | ≤0,31 | 0,99 |
| 7/9 | c1 | 32 | 20,0 | c2: **18,3** | 0,31 | 0,57 |
| 7/9 | c2 | 19 | 33,0 | c1: **18,3** | 0,09 | 0,44 |
| 7/9 | c3 | 2,7 | 1,3 | c0: 0,42 | ≤0,01 | 0,96 |
| 23/10 | c1 | 59 | 17,5 | — | 0,01 | 1,00 |
| 23/10 | c0 | 24 | 34,6 | c2: **30,6** | 0,00 | 0,75 |
| 23/10 | c2 | 17 | 17,3 | c0: **30,6** | 0,01 | 0,29 |
| 30/10 | c1 | 31 | 18,9 | c0 10,2 · c2 12,4 · c4 13,1 | 0,00 | 0,48 |
| 30/10 | c0 | 29 | 5,6 | c1 10,2 · c2 8,8 · c4 6,1 | 0,00 | 0,30 |
| 30/10 | c2 | 21 | 11,5 | c1 12,4 · c0 8,8 · c4 7,6 | 0,00 | 0,23 |
| 30/10 | c4 | 16 | 5,5 | c1 13,1 · c0 6,1 · c2 7,6 | 0,00 | 0,16 |
| 30/10 | c3 | 3,4 | 0,35 | — | 0,00 | 1,00 |
| 8/1 | c1 | 44 | 35,8 | — | 0,02 | 1,00 |
| 8/1 | c0 | 34 | 20,4 | c2: **16,5** | 0,02 | 0,81 |
| 8/1 | c2 | 21 | 27,3 | c0: **16,5** | 0,02 | 0,56 |

Fluxo normalizado `inter / sqrt(intra_a · intra_b)` entre os clusters do polo fatiado: 7/9 c1–c2
**0,71**; 23/10 c0–c2 **1,25**; 30/10 entre c0/c1/c2/c4 **0,84–1,29**; 8/1 c0–c2 **0,70**. Entre
polos distintos: ≤0,07 (7/9 c0–c3) e ≤0,014 nos demais.

Fração do peso de cada cluster que fica dentro dele: 23/10 c2 **0,36**; 30/10 c0 **0,18**, c4
**0,17**, c2 0,29, c1 0,35; 7/9 c1 0,52; 8/1 c0 0,55. Nos clusters fechados: 0,97–0,999.

Sobreposição dos top-K (IDs em comum): 7/9 c1∩c2 = **92**/100; 23/10 c0∩c2 = **83**; 30/10, entre
os quatro grandes, **62–77** em cada par; 8/1 c0∩c2 = **49**. Entre polos: 0–3.

### 1.2. Qual polo é o fatiado muda de evento para evento

| Evento | Polo fechado (1 cluster) | Polo fatiado |
|---|---|---|
| 7/9 | anti-Bolsonaro (c0, 46%) | bolsonarista (c1 + c2 = 51%) |
| 23/10 | anti-Bolsonaro (c1, 59%) | bolsonarista (c0 + c2 = 41%) |
| 30/10 | bolsonarista (c3, **3,4%**) | anti-Bolsonaro (c1 + c0 + c2 + c4 = 96%) |
| 8/1 | bolsonarista (c1, 44%) | anti-Bolsonaro (c0 + c2 = 56%) |

Além dos dois polos, 7/9 tem um terceiro cluster coerente: c3 (439 nós), 95% dos membros
retuitaram @cirogomes; top-20 quase todo Ciro/PDT.

### 1.3. Quem retuitou o quê — cobertura de autores por cluster

Percentual dos membros do cluster que retuitaram ≥1 tweet hidratado do autor (`retweets.parquet` ×
`graph_nodes` × `tweets`).

| Evento | Autor | c(a) | c(b) | c(c) | c(d) |
|---|---|---|---|---|---|
| 7/9 (c0, c1, c2, c3) | @jairbolsonaro | 0 | **0** | **100** | 0 |
| 7/9 | @rmotta2 | 0 | 23 | 27 | 0 |
| 7/9 | @PMESP | 0 | 20 | 24 | 0 |
| 7/9 | @cirogomes | 2 | 0 | 0 | **95** |
| 23/10 (c0, c2) | @jairbolsonaro | 63 | **86** | | |
| 23/10 | @taoquei1 | 73 | 68 | | |
| 23/10 | @flferronato | **54** | 26 | | |
| 23/10 | @PastorMalafaia | **48** | 23 | | |
| 23/10 | @RafaelFontana | **33** | 10 | | |
| 23/10 | @fabiofaria | 18 | **31** | | |
| 23/10 | @Rconstantino | 16 | **29** | | |
| 30/10 (c0, c1, c2, c4) | @AndreJanonesMG | 1 | 56 | 30 | **99** |
| 30/10 | @poty_oficial | 0 | 4 | **99** | 0 |
| 30/10 | @randolfeap | 20 | **82** | 33 | 22 |
| 30/10 | @simonetebetbr | 6 | **49** | 11 | 11 |
| 30/10 | @MarinaSilva | 28 | 43 | 38 | 31 |
| 8/1 (c0, c2) | @choquei | 50 | **65** | | |
| 8/1 | @tracklist | 4 | **32** | | |
| 8/1 | @LulaOficial | 29 | **41** | | |
| 8/1 | @gleisi | **35** | 14 | | |
| 8/1 | @Ana_Flor | **30** | 12 | | |
| 8/1 | @randolfeap | **24** | 5 | | |
| 8/1 | @reporterenato | **22** | 8 | | |
| 8/1 | @FlavioDino | **14** | 2 | | |
| 8/1 (c1) | @DanVitorPH | — | — | 60 | |
| 8/1 (c1) | @Jakelyneloiola_ | — | — | 44 | |

Conteúdo **exclusivo** de cada metade do par (tweets com ≥30 retweets na união; "enviesado" =
taxa por mil membros ≥2× maior num lado): fração do volume do cluster que cai em tweets enviesados
para ele — 7/9: c1 **0,01**, c2 0,19; 23/10: c0 **0,56**, c2 **0,06**; 30/10: c1 0,52–0,56, c0
0,28, c2 0,37, c4 0,11; 8/1: c0 **0,66**, c2 **0,43**.

### 1.4. Quando cada cluster agiu

| Evento | Cluster | mediana da 1ª ação do membro | pico horário (fração dos RTs) | mediana de RTs/membro |
|---|---|---|---|---|
| 23/10 | c0 | 16:45 | 16h (0,148) | 16 |
| 23/10 | c2 | 17:04 | 22h (0,146) | 11 |
| 23/10 | c1 | 17:19 | 18–19h (0,13) | 15 |
| 8/1 | c1 | **16:01** | 19–20h (0,12) | 13 |
| 8/1 | c0 | 19:15 | 19–21h (0,11) | 13 |
| 8/1 | c2 | 20:00 | **21h (0,215)** | 10 |

No 8/1, fração dos retweets do cluster feitos **antes das 18h**: c1 **0,17**; c0 0,04; c2 0,01.

### 1.5. Os mesmos usuários ao longo dos eventos

Tabulação cruzada de `user_id` entre `graph_nodes` de eventos distintos (só clusters ≥1%):

- 7/9 c0 → 23/10 c1: 100%. 7/9 c1 → 23/10 c0/c2: 65/35. 7/9 c2 → 23/10 c0/c2: 57/43.
- 23/10 c0 e c2 → 8/1 c1: 100% e 99%. 23/10 c1 → 8/1 c0/c2: 82/18.
- 30/10 c1 → 8/1 c0/c2: 88/12. c4: 75/25. c0: 68/32. c2: **52/48**. c3 → 8/1 c1: 99%.
- 7/9 c3 (Ciro) → 8/1 c0: 88%.
- Fração dos membros do 8/1 já vistos em algum evento anterior: c0 **0,51**; c1 0,27; c2 **0,25**.
  Dos que voltaram, 100% vieram do mesmo polo (c0/c2 ← anti; c1 ← bolsonarista).

### 1.6. Perfil dos autores-âncora (ponderado por `rt_cluster` no top-K hidratado)

| Evento | Cluster | seguidores (mediana pond.) | volume em autores <100k seg. | volume em contas criadas ≥2019 | volume em verificados | volume em contas governamentais |
|---|---|---|---|---|---|---|
| 7/9 | c0 | 548k | 0,17 | 0,14 | 0,69 | 0,17 |
| 7/9 | c1 / c2 | 681k / 1,4M | 0,27 / 0,17 | 0,23 / 0,15 | 0,85 / 0,91 | 0,12 / 0,08 |
| 23/10 | c1 | 585k | 0,07 | 0,23 | 0,76 | 0,06 |
| 23/10 | c0 / c2 | 1,4M / 1,9M | 0,12 / 0,08 | 0,12 / 0,11 | 0,90 / 0,93 | 0 / 0 |
| 30/10 | c1 | 1,0M | 0,21 | 0,10 | 0,79 | **0,37** |
| 30/10 | c0 / c2 | 168k / 118k | **0,46 / 0,49** | 0,12 / 0,09 | 0,59 / 0,54 | 0,17 / 0,16 |
| 30/10 | c4 | 700k | 0,30 | 0,10 | 0,72 | 0,16 |
| 8/1 | **c1** | **66k** | **0,71** | **0,62** | 0,47 | 0,03 |
| 8/1 | c0 | 421k | 0,22 | 0,19 | 0,58 | 0,16 |
| 8/1 | c2 | 1,3M | 0,20 | 0,09 | 0,70 | 0,12 |

### 1.7. Atrição (IDs não devolvidos pela API)

| Evento | Cluster | atrição | dos quais `Authorization Error` (conta suspensa/protegida) |
|---|---|---|---|
| 7/9 | c0 / c1 / c2 / c3 | 0,12 / **0,38** / **0,39** / 0,10 | 1 / 7 / 7 / 0 |
| 23/10 | c1 / c0 / c2 | 0,21 / **0,34** / **0,32** | 4 / 1 / 1 |
| 30/10 | c1 / c0 / c2 / c4 / c3 | 0,17 / 0,24 / 0,23 / 0,19 / 0,10 | 3 / 6 / 7 / 5 / 1 |
| 8/1 | c1 / c0 / c2 | **0,28** / 0,16 / 0,11 | **12** / 5 / 3 |

---

## 2. Leitura narrativa por evento (apontamentos, 2026-09-15)

### 2.1. 7 de setembro — o mesmo ato, dois enquadramentos prontos

**Polo anti-Bolsonaro (c0).** Quatro fios dominam: (i) *apropriação* — "sequestro da data",
"comício travestido de parada oficial", "apequenou o 7 de setembro" (Randolfe, Gleisi, Lula,
Sâmia, Ivan Valente); (ii) *ilegalidade* — crime eleitoral, abuso de poder, "acionar o TSE"
(Randolfe, PSOL, PT, Rede, UOL, O Globo, Estadão); (iii) *ridicularização* — "imbrochável",
"insegurança masculina", "Viagra", "flopou" (Boulos, Tabet, Sensacionalista, Cynara Menezes,
Brasil 247); (iv) *alívio* — "não teve golpe nem facada", "ele é fraco, covarde" (Tabet, Boff).
Imprensa e comentaristas de centro (Reinaldo Azevedo, Cantanhêde, Miriam Leitão, Noblat, Alckmin)
estão dentro do cluster, com pureza ~1. Ou seja: o "polo anti-Bolsonaro" já aqui não é "a
esquerda", é uma coalizão anti-Bolsonaro que inclui a imprensa de referência.

**Polo bolsonarista (c1 + c2).** Fios: (i) *grandeza* — "maior 7 de setembro da história",
imagens aéreas, "mar verde e amarelo", PMESP sem ocorrências; (ii) *inversão do sequestro* —
"não foi sequestrar, foi resgatar" a bandeira (Motta, viniciuscfp82); (iii) *coro* — "prende o
Lula" nos desfiles (Piraja, Oeste); (iv) *imprensa em luto* — jornalistas "tensos", "Rivotril
zerado", "furiosos que Bolsonaro usou politicamente"; (v) **plataforma hostil** — "Twitter
derrubando seguidores", "passaram o rodo nas contas da direita", "o alvo é diminuir os robôs do
Bolsonaro, vamos levantar as contas de novo" (SandraMorenah22, Gardenalpequen3, Engler, Davy
Albuquerque, Fernanda Salles). O fio (v) é o embrião da narrativa de perseguição que reaparece
nos eventos seguintes. A frase do próprio Bolsonaro sobre "trazer para dentro das quatro linhas
os que ousam ficar fora delas" (via Jovem Pan) está no top-100.

**Terceiro polo (c3, Ciro/PDT).** Pequeno, mas coeso e distinto: quase só Ciro, com a pauta
"comício eleitoral, cobramos a justiça" — o mesmo diagnóstico do polo anti, sem ser parte dele.
88% desses usuários reaparecem no c0 do 8/1.

### 2.2. Roberto Jefferson — a violência como teste, e o anti-STF já formado

**Polo anti-Bolsonaro (c1, fechado).** O eixo é uma operação de *vinculação*: "ROBERTO JEFFERSON
É BOLSONARO" (desmentindobozo, Laura Carvalho, Zélia Duncan, Lázaro Rosa), "não é louco, é
bolsonarista" (Ronchi), "coordenador da campanha". Secundários: *violência contra policiais/mulher
+ granada* (Haddad, Freixo, Rita Lisauskas), *hipocrisia racial* ("se fosse preto e pobre" —
Tabet, Thiago Resiste), *cumplicidade governamental* (ministro da Justiça enviado ao Rio — Natuza,
Ronchi, Erika Hilton), *vazamento da operação* (Reinaldo, Tabet), *cortina de fumaça* (salário
mínimo de Guedes — Xico Sá, Marcelo Lins, Sherazade), e a *comemoração do recuo* de Bolsonaro
("dominamos a narrativa... XEQUE MATE" — Janones, 22:26). Imprensa (UOL, Folha, Metrópoles,
Mônica Bergamo, Natuza) e Choquei estão dentro do polo.

**Polo bolsonarista (c0 + c2).** Duas camadas no mesmo dia:

- *Reação imediata (mais forte em c0, 16h)*: "Gestapo te prende num domingo por xingamento"
  (TeAtualizei), "Alexandre de Moraes instituiu a pena de morte" (Fontana), "ditadura da toga",
  "maldita ditadura, que Deus proteja o Roberto Jefferson" (Fernanda Salles), "dois pesos: Bárbara
  Gancia xingou a filha do presidente e nada" (Sonaira, Mocellin, Carvalho), "quem pediu a prisão
  foi Randolfe, coordenador do Lula" (Fontana, Saul, Gazeta do Povo), "derrubaram a conta da
  filha". Aqui a moldura **STF/Moraes como inimigo** está completa, dois meses e meio antes do
  8/1.
- *Linha oficial (mais forte em c2, 22h)*: "Repudio as falas... bem como inquéritos sem respaldo
  na Constituição" e "Prisão do criminoso Roberto Jefferson" (Bolsonaro), "NÃO é coordenador,
  fake news do PT" (Fábio Faria, TeAtualizei), "nada justifica a violência" (Tarcísio, Mourão,
  Carvalho), "turma do mensalão" (Constantino), "Bolsonaro chega ao debate que o Lula fugiu"
  (PATRIOTAS). A construção recorrente é "lamento e repudio, **mas**…".

A leitura que fica: no 23/10 o polo bolsonarista *ensaia* separar-se de um aliado violento sem
abandonar a tese de perseguição judicial. A tese sobrevive; o aliado é descartado.

### 2.3. 30 de outubro — "democracia" é vocabulário de um lado só

O evento é definido pela palavra-chave "democracia". Nos dados, 96,6% dos nós estão no polo
anti-Bolsonaro. Isso é em parte **efeito do filtro do dataset**: o termo era o léxico da campanha
de Lula/Tebet/Alckmin e da imprensa naquele dia; o polo bolsonarista estava no Twitter, mas não
falava nesses termos. O evento mede, portanto, *como um polo mobilizou a palavra*, não a disputa
entre polos.

**Polo anti-Bolsonaro (c1, c0, c2, c4).** Um único acontecimento organiza tudo: as blitze da PRF
como *supressão de voto* — "BANDIDOS! CRIMINOSOS!" (Randolfe), "Deixem o Nordeste votar",
"golpe em curso", "estamos em 1964", "estender o horário de votação", "GloboNews abra o sinal".
Janones opera como central de denúncias ("continuem me enviando"); há dezenas de respostas a
@AndreJanonesAdv no top-K de c4. O tom vai de institucional-sereno (Tebet, Alckmin, Gilmar
Mendes, senadores: "que seja um domingo de paz") a fandom-indignado (BTSxBRAZIL, seokjiiminie,
"a festa da democracia virando um enterro").

**Polo bolsonarista (c3, 332 nós).** Inverte o mesmo fato: PRF parando ônibus é "fiscalizar
compra de votos / ônibus fretado — a democracia agradece" (fabifbbr, Gagliasso), "em Cuba deu
empate 0x0" (Joaquin Teixeira), "arruaceiros querem cagar democracia praticando crime eleitoral"
(ricardors_of), "o Xandinho não quer que Bolsonaro vença", e — antes do resultado — "se não vier
do povo a democracia, virá das FFAA! Não vai ter golpe" (Índio Pistola, 17:04). Mara Maravilha,
Milton Neves, Mourão, Tereza Cristina ancoram. É um cluster pequeno, mas coeso e legível; não é
ruído.

### 2.4. 8 de janeiro — dois dias diferentes no mesmo calendário

**Polo bolsonarista (c1, fechado).** O que mais chama atenção não é só o conteúdo, é *quem* e
*quando*.

- *Quem*: as âncoras são contas pequenas e recentes — DanVitorPH (66k seguidores, criada em
  2022, 15 itens no top-100), Jakelyne Loiola (172k, 10 itens), A Trombeta, 7minutos_news
  (Miami, 4k), stenyolaisson (24k), Júlio Rocha (Polônia, 22k), OnePaul (Miami), FredRC,
  Capitão Telhada. 71% do volume vai a autores com <100k seguidores e 62% a contas de 2019+.
  As âncoras institucionais do polo nos eventos anteriores (Bolsonaro, TeAtualizei, Malafaia,
  Mourão, Nikolas, Carlos, Tarcísio, Motta) quase somem: Motta aparece em #65 negando movimentação
  de tropas, Malafaia em #89 com uma pergunta, Magno Malta em #90 negando ter convocado. **Os
  usuários são os mesmos** (23/10 c0/c2 → 8/1 c1 em 99–100%), **as vozes que amplificam são
  outras.** Continuidade de público com substituição de liderança — coerente com o silêncio de
  Bolsonaro (em Orlando) e o afastamento dos políticos.
- *Quando*: 17% dos retweets do cluster são anteriores às 18h (c0: 4%; c2: 1%); mediana da
  primeira ação às 16:01 contra 19:15 e 20:00. O dia do c1 começa de madrugada ("Não para de
  chegar patriotas, 01:50", "Brasília está tomada por brasileiros raiz, incansáveis há quase 70
  dias", "300 ônibus chegam", "Tomada do poder Brasília" às 10:36 — este último com 3.232
  retweets **antes** da invasão).
- *O quê*, em três atos: (1) **celebração/épica** — "marcha patriótica de 5km #BrazilianSpring",
  "Subindo a rampa! haha", "Supremo é o Povo", "Brasília tomada, esperando o ministro da Defesa e
  Moraes pras negociações", "já é notícia na France2"; (2) **cerco/martírio** — "polícia
  atirando bala de verdade", "povo patriota atacado por bombas", "manifestantes pacíficos",
  "policial aplaudido pelos manifestantes"; (3) a partir das ~20h, **"infiltrados" e
  transferência de culpa** — "FOI TUDO PLANEJADO! Ajudem a divulgar os infiltrados! Senão nós
  vamos perder a batalha! São eles em Brasília e nós nas redes sociais!" (22:37; o mesmo texto
  aparece em **quatro** contas no top-100, somando ~7,8 mil retweets do cluster), "jornalista
  canhoto descoberto", "viatura indo para a água sem ser empurrada, tudo arrumado", "não houve
  revista, tudo suspeito", "Flávio Dino acionou o gatilho", "Lula decreta intervenção e a
  esquerda dizia que Bolsonaro era golpista", "em 2017 esquerdistas incendiaram ministérios e
  Dino celebrou", "Maduro apoia Lula". Fecha com esperança militar: "Forças do carniça tentam
  invadir área militar e o Exército não permite", "movimentos fortes na caserna", "FFAA, agora é
  a hora". Cerca de um quinto dos itens hidratados fala de infiltrados. A frase "nós nas redes
  sociais" nomeia a divisão de trabalho.

**Polo anti-Bolsonaro (c0 + c2).** Um acontecimento (invasão às ~15h, na TV às 18h) e duas
dietas:

- *c0 — esfera político-jornalística*: responsabilização e identificação. Ibaneis/Anderson
  Torres/Múcio "prevaricaram"; "PM tira foto e bate papo com vândalos" (Ana Flor, Choquei,
  Central da Política); nomeação de participantes (coronel da FAB, capitão da Marinha, deputado
  de MG, Pamela Bório, presidente da Galoucura, tenista dopado, "deixando o friburguense
  famoso"); "documentem tudo antes que apaguem"; Anonymous e Lupa pedindo material; áudio de
  Magno Malta; Jovem Pan "lado a lado com os invasores". Resposta institucional (nota do STF,
  Lula, Dino, Randolfe/Gleisi pedindo intervenção, Chile, Casa Branca, UE). 51% dos membros já
  estavam em eventos anteriores.
- *c2 — esfera pop/entretenimento*: os mesmos fatos vistos por Choquei (65% dos membros),
  Tracklist, UpdateCharts, BCharts, mais a conta do próprio Lula (41%) e humor. "Cavalo socorrido
  após ser atacado", "trompetista toca jingle do Lula enquanto terroristas são presos", "mulher
  coloca bandeira do Lula e eles começam a mugir", "terroristas com a cara no chão"; Lula citado
  literalmente por Tracklist ("a esquerda já teve gente morta e nunca invadiu o Congresso");
  deboche ("Bolsonaro na Disney e os corno quebrando tudo", "metade de Brasília desempregada
  amanhã", "o tanto de vaga pro concurso da polícia"); vozes de fandom/cultura (Cleo, AOC via
  BCharts, "queria ver a série da betinha"). 75% dos membros **não** estavam em nenhum evento
  anterior. Pico concentrado às 21h (discurso de Lula às 20:57 + cobertura do Choquei). 43% do
  volume de c2 é conteúdo enviesado para c2 — não é um subconjunto de c0.

**O "mesmo fato".** Os dois polos não discordam só na avaliação; assistem a *eventos* diferentes.
Para c1, o fato é uma vigília patriótica de 70 dias que culmina em marcha, é sabotada por
infiltrados e reprimida à bala; para c0/c2, o fato é uma tentativa de golpe facilitada por uma
polícia conivente. A mesma cena (policiais junto a manifestantes) é "policial aplaudido pelo
povo" num lado e "PM batendo papo com golpistas" no outro. Fluxo entre os polos: 0,02% do peso.

### 2.5. O arco até o 8/1, como se lê nestes dados

1. **Âncoras.** O polo anti-Bolsonaro tem o mesmo elenco nos quatro eventos (Janones, Randolfe,
   Gleisi, Reinaldo Azevedo, desmentindobozo, Ronchi, Thiago Resiste, Lázaro Rosa, Noblat,
   GloboNews/UOL/Folha/Metrópoles, Choquei). O polo bolsonarista troca de elenco a cada evento e,
   no 8/1, perde as vozes institucionais. A bolha que invade é *sem liderança* no Twitter.
2. **Molduras que amadurecem.** "Plataforma nos persegue" (7/9) → "STF/Moraes/Gestapo" e "nada
   justifica, mas…" (23/10) → "FFAA como árbitro" e "PRF faz seu trabalho" (30/10, minoritário)
   → "infiltrados", "Dino provocou", "Exército protege o povo" (8/1). Do outro lado: "crime
   eleitoral / TSE" (7/9) → "RJ é Bolsonaro / bolsonarismo mata" (23/10) → "golpe em curso /
   PRF" (30/10) → "terrorismo / identificar e punir / polícia conivente" (8/1). As duas
   sequências são internamente consistentes e mutuamente impermeáveis.
3. **Assimetria de atrição.** O material do polo bolsonarista é o mais perdido (28–39% nos
   clusters fechados/fatiados dele, 12 suspensões só no c1 do 8/1). O que se lê é o que
   *sobreviveu*; a leitura tende ao lado mais brando da bolha.
4. **"Esquerda" e "direita" são rótulos imprecisos aqui.** O polo anti inclui Tebet, Alckmin,
   Gilmar Mendes, Reinaldo Azevedo, Miriam Leitão e a imprensa de referência; o polo oposto é
   especificamente bolsonarista. Registrar isso antes do D7/D8, porque afeta como o score de
   §3.4 deve ser lido.
5. **Terceiros polos existem e são legíveis.** Ciro (7/9) e o bolsonarismo em "democracia"
   (30/10). Caracterizados acima; não descartar.

---

## 3. Os clusters entrelaçados: hipóteses sobre o que os separa

Pergunta: por que o Leiden fatia um polo em 2–4 clusters cujos top-K são quase iguais?

### 3.1. O que as medições sustentam

**(a) Estruturalmente, cada par é uma comunidade só.** Fluxo normalizado 0,70–1,29 entre as
metades (valor ≥1 significa que a aresta entre as metades pesa mais que a média geométrica das
internas). Em 23/10 c2 e em 30/10 c0/c4, a maior parte do peso do cluster sai dele. O E6 de
`analises-sensibilidade.md` já mostrava que `resolution=0,7` funde c0+c2 no 8/1, e o relatório de N
mostrou que N≥15 também funde. O corte está no limite do parâmetro.

**(b) O mecanismo mais forte é um item megaviral + Jaccard + poucos retweets por usuário.**
- 7/9 c2: **100%** dos membros retuitaram o tweet de Bolsonaro das 22:42 (3.144 retweets =
  o tamanho do cluster); **0%** do c1. Com N=3, a mediana é 4 retweets por usuário; dois usuários
  que compartilham esse único item já têm Jaccard ≥1/7 > τ. Resultado: um quase-clique (densidade
  interna 0,60 contra 0,14 no c1). O c2 é "a audiência de um tweet".
- 30/10: c2 = **99%** retuitaram @poty_oficial (cantor com 1.135 seguidores, 2.046 retweets); c4 =
  **99%** retuitaram o "metrô de BH" de Janones; c1 = 82% o "BANDIDOS!" de Randolfe; c0 = o
  resíduo sem item dominante (nenhum autor acima de 28%) e o menos denso (0,22 contra 0,55–0,69).
- 23/10: c2 = 86% retuitaram Bolsonaro (dois tweets, 16:40 e 22:12) contra 63% em c0.

**(c) O fatiamento não persiste entre eventos quando é artefato.** 7/9 c1 e c2 distribuem-se
quase igual entre 23/10 c0 e c2 (65/35 vs 57/43). Já 30/10 c2 (poty) manda 48% para 8/1 c2,
enquanto 30/10 c1 (Randolfe/Tebet) manda 12% — aqui a divisão carrega algo.

**(d) Onde há sinal social por baixo do artefato:**
- *23/10 c0 vs c2*: c0 = militância (16 retweets/membro, mais Fontana/Salles/Malafaia/Ferronato,
  pico às 16h, 56% do volume em conteúdo próprio); c2 = audiência da linha oficial (11
  retweets/membro, mais Bolsonaro/Faria/Constantino/Tarcísio, pico às 22h, **6%** do volume em
  conteúdo próprio). c2 é quase um subconjunto de consumo de c0, concentrado nos itens oficiais.
- *30/10*: gradiente institucional ↔ base/fandom. c1 tem 37% do volume em contas governamentais
  (senadores, Tebet, Alckmin, Gilmar); c0 e c2 têm ~47% em autores <100k e vozes de fandom
  (BTSxBRAZIL, seokjiiminie, Vai Desmaiar, Caldeirão Furado, Jovem Nerd, BCharts). c4 é a
  audiência de Janones. Os de fandom são os que mais vão para 8/1 c2.
- *8/1 c0 vs c2*: a diferença mais sólida dos quatro eventos. Dieta (político-jornalística vs
  agregadores de entretenimento), público (51% recorrentes vs 25%), horário (espalhado vs pico
  às 21h) e conteúdo próprio (66% vs 43% — c2 tem material seu, não é subconjunto). Fluxo
  normalizado 0,70, o mais baixo entre pares do mesmo polo.

### 3.2. Hipóteses, por ordem de suporte

| Hipótese | Onde domina | Evidência a favor | Contra |
|---|---|---|---|
| H1 — artefato: item megaviral + Jaccard com poucos RTs por usuário | 7/9 (c1×c2); 30/10 (c2, c4, c1) | cobertura 99–100% de um autor; densidade de clique; não persiste entre eventos; funde com resolution/N | não explica 8/1 |
| H2 — camadas de consumo dentro do polo: militância/institucional × audiência/pop | 8/1 (c0×c2); 30/10 (c1 × c0/c2); 23/10 (fraco) | dietas de autores distintas; recorrência de público; conteúdo próprio em c2 do 8/1; mapeamento 30/10→8/1 | em 23/10 c2 quase não tem conteúdo próprio |
| H3 — horário de engajamento (quem age às 16h e quem age às 22h co-retuíta coisas diferentes) | 23/10; 8/1 c2 | picos distintos; itens megavirais têm hora (Bolsonaro 22:12; Lula 20:57) | é mecanismo de H1/H2, não causa independente |

Leitura por ora: **em 7/9 e 30/10 o fatiamento é majoritariamente capricho metodológico** (o
Jaccard reage a um único item quando a atividade por usuário é baixa — exatamente o cenário que D3
previa para "revisitar TF-IDF"); **em 23/10 é misto**; **em 8/1 é uma distinção real** entre a
esfera política e a esfera pop do mesmo polo. Em nenhum caso a divisão é ideológica: as metades
estão sempre do mesmo lado.

### 3.3. O que isso implica (trade-offs, não recomendação)

- *Para o leitor/produto*: apresentar c0 e c2 do 8/1 como "duas bolhas" ao lado de c1 induz o
  leitor a ver três lados onde há dois. Uma alternativa é mostrar dois polos (colapso por fluxo,
  como o L2 do relatório de N) e, dentro do polo, as camadas — com a legenda honesta de que no
  7/9 e 30/10 as camadas são a audiência de um tweet. Outra é manter o Leiden como está e
  rotular explicitamente "mesmo polo, camada X". A primeira é mais fiel à estrutura; a segunda,
  mais fiel ao algoritmo. Escolha a registrar em D-novo, se for feita.
- *Para a metodologia*: N mais alto ou TF-IDF na bipartida reduziriam H1 (o relatório de N já viu
  a fusão em N≥15), mas apagariam também a camada real do 8/1. Testar não custa; adotar é escolha
  com viés e deve ser explicitada.
- *Para o D7/D8*: o score de §3.4 por usuário dentro de um polo será ~constante; a rotulagem por
  cluster vai dar o mesmo rótulo a c0 e c2. Isso é esperado e confirma H1/H2, não é falha.

---

## 4. Pendências abertas por esta leitura

- Reproduzir na pipeline (módulo ou notebook) as medições de §1 (fluxo posicional, cobertura por
  autor, viés por par, recorrência entre eventos, perfil de âncoras). Foram feitas ad hoc.
- Ler os IDs **não hidratados** mais enviesados para cada metade (listados nesta sessão por
  contagem; ex.: 23/10 c0 tem seis itens com 2–4 mil retweets e sem texto). A atrição pode
  esconder o que diferencia as metades.
- Verificar o efeito do filtro de palavra-chave em 30/10 (é o único evento onde um polo tem 3%).
- Decidir se c3 do 7/9 (Ciro) e c3 do 30/10 entram na narrativa como terceiros polos.
