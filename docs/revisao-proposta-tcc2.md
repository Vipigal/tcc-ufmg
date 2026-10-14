# Revisão da proposta do TCC2 (`docs/proposta-tcc2.md`)

> **Data:** 2026-10-06.
> **Escopo:** cruzamento da proposta com (a) os artefatos da pipeline em `data/processed/` e os docs de
> análise (`relatorio-narrativa-preliminar.md`, `analises-sensibilidade.md`, `relatorio-sensibilidade-N.md`),
> (b) a auditoria e o guia de citações (`auditoria-referencias.md`, `guia-citacoes-tcc2.md`) mais uma
> conferência de DOIs no Crossref feita nesta rodada, e (c) o tom e a postura dos docs vivos
> (`visao-projeto.md`, `CLAUDE.md`), do relatório congelado do TCC1 e da proposta do TCC1 (`proposta.md`),
> levando em conta a mudança de rumo registrada em `docs/proposta-tcc2-rascunho.md`.
> **Como foi feito:** leitura integral dos documentos acima; hermeticidade por comunidade e por super-polo
> recalculada com pandas direto de `graph_nodes.parquet` e `graph_edges.parquet` (script de sessão, não
> versionado, descrito em §1.1); DOIs consultados em `api.crossref.org` e `doi.org`.
> **O que foi alterado na proposta:** só correções factuais, listadas em §5. Tudo que é escolha de redação,
> escopo ou postura ficou aqui como sugestão (§3 e §6).

---

## 1. Resultados: o que a proposta afirma e o que os artefatos mostram

### 1.1 Observações brutas — hermeticidade por comunidade e por super-polo

Medida: `h = I / (I + E)`, com `I` = peso das arestas internas e `E` = peso das arestas que saem do conjunto,
sobre os grafos em disco (N e τ do `run_config` de cada evento; `src`/`dst` são índices posicionais em
`graph_nodes.parquet`). Comunidades com ≥ 1% dos nós.

| Evento | Com. | % nós | h_c (relatório TCC1) | h_c (recalculada) |
|---|---|---|---|---|
| 7/9 | c0 | 45,6 | 0,969 | 0,9685 |
| 7/9 | c1 | 31,8 | — | 0,517 |
| 7/9 | c2 | 19,1 | — | 0,642 |
| 7/9 | c3 | 2,7 | — | 0,748 |
| 23/10 | c1 | 59,1 | 0,999 | 0,9993 |
| 23/10 | c0 | 23,6 | — | 0,530 |
| 23/10 | c2 | 17,2 | — | 0,361 |
| 30/10 | c3 | 3,4 | 0,979 | 0,9792 |
| 30/10 | c1 | 31,0 | — | 0,347 |
| 30/10 | c0 | 28,6 | — | 0,184 |
| 30/10 | c2 | 21,2 | — | 0,287 |
| 30/10 | c4 | 15,8 | — | 0,170 |
| 8/1 | c1 | 44,2 | 0,999 | 0,9989 |
| 8/1 | c0 | 34,3 | 0,55 | 0,554 |
| 8/1 | c2 | 21,4 | 0,62 | 0,623 |

Os valores do relatório são reproduzidos. Agregando por super-polo (regra L2 do relatório de N:
fluxo mútuo ≥ 0,10 · min(peso interno dos dois)):

| Evento | Polo monolítico | h_polo | Polo subdividido | h_polo | Fluxo entre polos (% do peso total) |
|---|---|---|---|---|---|
| 7/9 | {c0, c3} | **0,984** (c0 sozinho: 0,969) | {c1, c2} | **0,994** | 0,41 |
| 23/10 | {c1} | 0,9993 | {c0, c2} | 0,9998 | 0,012 |
| 30/10 | {c3} (3,4% dos nós) | 0,979 | {c0, c1, c2, c4} (96,6%) | 0,9999 | 0,007 |
| 8/1 | {c1} | 0,9989 | {c0, c2} | 0,9994 | 0,039 |

Regra de super-polo: a prosa do relatório congelado define super-polo por "fluxo mútuo acima de 1% do peso
total"; com essa regra o 7/9 tem **três** super-polos (c3, o cluster Ciro/PDT, troca 0,42% com c0 e fica
separado), e a tabela do relatório diz 2. Com a regra L2 (θ = 0,10) são 2, {c0, c3} e {c1, c2}. O relatório
não é editado; registro só para que a proposta não herde a ambiguidade (ver §1.2, item 4).

### 1.2 O que isso muda no texto (apontamentos, 2026-10-06)

1. **"Os dois super-polos são igualmente herméticos (acima de 0,99)"** não se sustenta no 7/9: o polo
   anti-Bolsonaro fica em 0,984 ({c0, c3}) ou 0,969 (c0 sozinho). O que vale nos três eventos de confronto é
   "0,98 a 0,9999" e "o polo subdividido é tão ou mais fechado que o monolítico". **Corrigido na proposta**
   (§5, item 2). A memória de sessão que originou o número também estava errada e foi corrigida.
2. **"Consistente com [4]"** estava preso à frase do dia do segundo turno. Interian e Rodrigues não dizem
   nada sobre o 30/10; a consistência (a auditoria pede "é consistente com", não "converge") é com o
   isolamento de uma comunidade. **Corrigido** (§5, item 1).
3. **"O dia do segundo turno apresenta a menor segregação"** é verdade pelas métricas de partição
   (Q = 0,149; r = 0,168), que a própria E1 propõe abandonar. No nível do polo o 30/10 também tem dois
   polos selados (0,9999 e 0,979), um deles com 3,4% dos nós. A proposta agora qualifica a frase
   ("pelas métricas de partição"), mas **não** diz que a leitura do 30/10 como controle enfraquece. Isso é
   interpretação e fica como sugestão: uma frase em P1 ou na E1 do tipo "no dia do segundo turno, o mesmo
   cálculo mostra dois polos fechados de tamanhos muito desiguais (96,6% e 3,4% dos nós), o que a E1 deve
   reler junto com o efeito do filtro por palavra-chave".
4. **"Dois super-polos"** no 7/9 depende da regra (ver §1.1). O cluster Ciro/PDT é um terceiro grupo legível
   (relatório de narrativa, §2.1 e §2.5). Sugestão de redação em P1 ou E1: "dois super-polos dominantes,
   mais um pequeno terceiro grupo no 7/9", para não forçar estrutura.

### 1.3 Demais números e fatos conferidos

| Afirmação na proposta | Fonte interna | Status |
|---|---|---|
| Hermeticidade do polo lacrado 0,97 a 0,999 nos três eventos de confronto | relatório TCC1, Tab. I; recalculado | confere |
| Interian e Rodrigues: >15 M de tweets; 44,1% vs 13,4% da modularidade | auditoria | confere |
| Um polo monolítico e outro subdividido; o lado subdividido muda por evento | narrativa preliminar §1.2 | confere (anti fechado em 7/9 e 23/10; bolsonarista em 30/10 e 8/1) |
| Hidratação seletiva dos mais retuitados por comunidade e leitor web beta | memória da fase 2; `web/`, `data/export/` | existem, mas são **posteriores ao relatório do TCC1** (set./2026); a proposta os listava como resultado do MSI I e, na frase seguinte, dizia que as comunidades estavam "sem conteúdo". Corrigido (§5, item 1) |
| "Comparação com a leitura manual já realizada" (E3) | `relatorio-narrativa-preliminar.md` (875 slots lidos) | existe; agora a introdução a menciona |
| Leitor web "se mostrou confuso para quem não vem da computação" | memória da sessão de 2026-10-05 (avaliação informal da orientadora) | sustentado por uma avaliação informal; ver §3.6 |
| Grupo focal com 3 a 5 pesquisadores; critério de robustez pré-registrado; 5º evento com o saldo da API | memória 2026-10-05 | confere |
| Evidência preliminar de que as subdivisões são sensíveis a `resolution` e a N | `analises-sensibilidade.md` E6 (resolution 0,7 funde c0+c2 no 8/1); `relatorio-sensibilidade-N.md` (N ≥ 15 funde) | existe e não é citada na proposta; vale uma frase na E1 como motivação do teste |

---

## 2. Referências: cruzamento com a auditoria, o guia e o Crossref

Numeração da versão de **32 referências** (antes do corte descrito em §8); serve como auditoria de cada fonte, inclusive das que saíram. "Crossref ✓ (hoje)" = metadados
conferidos nesta rodada em `api.crossref.org`.

| Ref. | Obra | Status | Observação |
|---|---|---|---|
| [1] | Bastos e Recuero 2023 | Crossref ✓ (hoje) | uso (narrativa de fraude pela liderança) conforme guia |
| [2] | Pariser, ed. Zahar 2012 | pendente leve | edição brasileira: conferir editora/ano/cidade na ficha catalográfica (guia) |
| [3] | Sunstein, #Republic 2017 | pendente leve | o guia só verificou o cap. 1; a "polarização de grupo" atribuída a [3] vem de Sunstein 2002 (*The law of group polarization*). Ou citar o artigo, ou conferir o capítulo de #Republic |
| [4] | Interian e Rodrigues 2023 | auditado ✓ | verificar se há versão publicada |
| [5] | Nota do STF 24/10/2022 | não acessível daqui (HTTP 403) | sustenta a ordem de prisão; "aliado de Bolsonaro" e "tiros e granadas" vêm de [6] e [7] (guia) |
| [6] | AP via Global News | auditado no guia ([47]) | **nova na proposta** |
| [7] | Poder360 | auditado no guia ([48]) | **nova na proposta** |
| [8] | Alabarse dos Santos et al. 2024 | Zenodo ✓ | autoria corrigida conforme auditoria |
| [9] | Sunstein 2002, *The law of group polarization* | Crossref ✓ (hoje) | **nova na proposta** (decisão do autor, 2026-10-06): sustenta a "polarização de grupo" que antes estava só em [3] |
| [10] | Recuero, Soares e Zago 2021 | Crossref ✓ (hoje) | os três usos (dieta pró/anti-HCQ; crítica à falta de definição; leitura manual de atores) conferem com o guia |
| [11] | Recuero, Soares e Gruzd 2020 | Crossref ✓ (hoje) | rede de interação, não só retweet; o texto da proposta não afirma o contrário |
| [12] | Hoffmann da Silva e Recuero 2025 | DOI resolve (doi.org → OJS) | Crossref sem metadados; conferir grafia do sobrenome na página do artigo |
| [13] | Conover et al. ICWSM 2011 | auditado ✓ | uso (dois grupos segregados) conforme guia |
| [14] | Conover et al. PASSAT 2011 | auditado ✓ | uso (95%) conforme guia |
| [15] | Kessler 1963 | **não consultado** | citar só a ideia (como está); guia sugere "conforme descrito em [16]" se não for lido |
| [16] | Perianes-Rodriguez et al. 2016 | Crossref ✓ (hoje) | orientação da matriz (C = M·Mᵀ) a conferir visualmente (guia) |
| [17] | van Eck e Waltman 2009 | Crossref ✓ (hoje) | DOI 10.1002/asi.21075 confere (não constava no guia) |
| [18] | Becatti et al. 2019 | auditado ✓ | uso restrito à projeção bipartida, como pede a auditoria |
| [19] | Pacheco et al. 2021 | auditado ✓ | — |
| [20] | Mattei et al. 2022 | Crossref ✓ (hoje) | fonte do termo "comunidade discursiva", como pede a auditoria |
| [21] | Traag et al. 2019 | auditado ✓ | — |
| [22]–[24], [26] | Good 2010; Fortunato e Barthélemy 2007; Traag et al. 2011; Peixoto 2014 | auditado ✓ | — |
| [25] | Lancichinetti e Fortunato 2012 | Crossref ✓ (hoje) | *Sci. Rep.* 2, 2012, doi 10.1038/srep00336: a pendência do guia ("recuperado de memória") está resolvida |
| [27] | Recuero 2024 (Compós) | pendente | falta URL/páginas nos Anais (guia) |
| [28] | Gatti 2005 | **não auditado** | livro real (Liber Livro, série Pesquisa em Educação); confirmar leitura e dados da edição |
| [29] | Gephi (Bastian et al. 2009) | Crossref ✓ (hoje) | — |
| [30] | NodeXL (Hansen et al. 2011) | não auditado | livro; metadados plausíveis |
| [31] | 4CAT (Peeters e Hagen 2022) | Crossref ✓ (hoje) | — |
| [32] | Hoaxy (Shao et al. 2016) | Crossref ✓ (hoje) | — |

Ordem de citação IEEE (primeira aparição) conferida: 1 a 32, sequencial, sem entrada órfã nem citação sem
entrada. O guia pedia ao menos uma fonte fora da escola de Recuero (ciência política ou ciência de dados
social); a proposta tem 5 itens de Recuero em 32 e nenhuma fonte de ciência política. Fica a critério.

---

## 3. Tom de voz, postura e visão

### 3.1 A pergunta central mudou em relação a `visao-projeto.md`

A proposta diz "a pergunta central se mantém" e a formula como *"o Twitter brasileiro estava polarizado no
ciclo de 2022, e qual é a forma dessa polarização?"*. Isso é a pergunta do **relatório do TCC1**. A pergunta
de `visao-projeto.md` ("o que não muda") é outra: *como apoiadores de **esquerda e de direita** construíram
narrativas distintas sobre o **8 de janeiro** e como torná-las visíveis e navegáveis*. Três mudanças reais:
sai o rótulo esquerda/direita (coerente com a decisão de não rotular a priori e com a leitura de que o polo
anti inclui Tebet, Alckmin e a imprensa de referência), o 8/1 vira um evento do arco em vez do objeto, e a
parte "visível e navegável" passa a tese tecnológica. As três são defensáveis, mas `visao-projeto.md` diz que
mudanças ali exigem discussão explícita. **Decisão do autor:** atualizar a pergunta em `visao-projeto.md`
(com data e motivo) ou reescrever a frase da proposta para "a pergunta central foi reformulada no TCC1 e se
mantém desde então".

### 3.2 O que saiu do plano do MSI I e a proposta não diz

O relatório congelado prometia, como trabalhos futuros: score ideológico contínuo por usuário (D7),
rotulagem esquerda/direita das comunidades, painel longitudinal de radicalização e o controle temporal do
8/1 (D10). A proposta abandona os quatro, e com razão (a memória de 2026-10-05 registra a decisão), mas o
rascunho tinha um parágrafo "Fora do escopo" que a versão final perdeu. As diretrizes pedem que os objetivos
do MSI I sejam "revisitados"; um leitor que compare o relatório com a proposta vai sentir a falta. Sugestão
de parágrafo para o fim da Introdução, antes dos objetivos:

> **O que muda em relação ao plano do MSI I.** O relatório do TCC1 previa rotular as comunidades como
> esquerda e direita por um score ideológico de autores, medir a radicalização de um painel de usuários ao
> longo do arco e animar o 8 de janeiro hora a hora. Esses itens saem do escopo. A leitura preliminar
> mostrou que "esquerda" e "direita" descrevem mal os polos encontrados (um deles reúne candidatos de centro
> e a imprensa de referência), e por isso os rótulos passam a emergir do conteúdo e da leitura dos
> participantes do grupo focal, não de uma classificação prévia. O painel de radicalização e o controle
> temporal ficam como trabalhos futuros.

Se o parágrafo entrar, `docs/decisoes-metodologicas.md` precisa de uma entrada de revisão para D7, D8 e D10
(o `CLAUDE.md` exige), o que ainda não existe.

### 3.3 O título presume a resposta de P4

"Duas realidades sobre o mesmo fato" afirma o que P4 pergunta ("os ambientes são distintos a ponto de
constituírem realidades paralelas?"). A frase vem da proposta do TCC1, onde era a noção a "tornar palpável",
não uma hipótese a testar. Com a postura "descrever, não prescrever", um título que não antecipe o veredito
seria mais coerente, por exemplo *"A forma da polarização: estrutura, conteúdo e visualização interativa do
Twitter brasileiro no ciclo eleitoral de 2022"*. O rascunho marcava o título como ⟦decidir⟧ e a decisão
continua em aberto.

### 3.4 "O grafo é meio, não fim": justificar a E1 pela ferramenta

A E1 é a etapa mais longa da metodologia e é estrutural. Isso está em linha com a insistência do autor em
rever a estrutura antes da ferramenta, mas a postura 2 de `visao-projeto.md` pede que métricas sirvam ao
produto. Falta a frase que liga as duas coisas, e ela já existe no relatório de narrativa (§3.3): apresentar
c0 e c2 do 8/1 como "duas bolhas" ao lado de c1 induz o leitor a ver três lados onde há dois. Sugestão para
abrir a E1: "A revisão estrutural decide o que a ferramenta mostra: se uma subdivisão não é robusta, ela é
exibida como camada de um mesmo polo, não como comunidade à parte."

### 3.5 "Caracterize antes de descartar"

P1 e a E1 opõem "comunidade distinta" a "artefato da detecção". Pelo `CLAUDE.md`, um veredito de artefato
ainda pede caracterização: no 7/9, o c2 é "a audiência de um único tweet de Bolsonaro" (100% dos membros o
retuitaram; 0% do c1), o que é uma descrição, não um descarte. Sugestão: no entregável da E1, "um veredito
por par, com a caracterização do que separa as duas metades em ambos os casos". A frase sobre o SBM
("decide estatisticamente") foi trocada por "oferece um critério independente para avaliar" (§5, item 4),
porque seleção por descrição mínima não é teste de hipótese.

### 3.6 Frases a suavizar ou sustentar

- "o leitor web do TCC1 se mostrou confuso para quem não vem da computação": a base é uma avaliação informal
  com a orientadora. Sugestão: "em uma primeira avaliação informal com a orientadora, o leitor web mostrou-se
  confuso para quem não vem da computação". É mais honesto e justifica melhor o grupo focal.
- "margem estreita" (segundo turno) está sem fonte; o rascunho previa citar o resultado oficial do TSE. Ou
  cita, ou aceita como fato notório.
- A Introdução reaproveita quase literalmente a do relatório congelado (primeiro parágrafo e o parágrafo da
  "forma da divisão"). Para a proposta é aceitável; no artigo final convém reescrever.

### 3.7 Postura mantida (o que está bem)

- Nenhum rótulo ideológico a priori; "esquerda/direita" aparece só ao citar Interian e Rodrigues, nos
  termos deles.
- Câmara de eco como propriedade estrutural mensurável, não como hipótese sobre exposição (coerente com a
  postura 1 da visão e com a reescrita R1 do guia).
- Jaccard declarado como escolha analítica; analogia com acoplamento bibliográfico declarada como do autor;
  "comunidade discursiva" com a fonte certa.
- "Resultados negativos também serão reportados"; critério de robustez registrado antes da execução.
- Fora do escopo da visão respeitado: sem análise de sentimento em larga escala (as sínteses usam só top-K e
  assinaturas), sem bots/desinformação como objeto, sem comparação internacional.
- Declaração de uso de IA em dois planos, como as diretrizes exigem.

---

## 4. Conformidade com as diretrizes (agosto/2026)

| Item exigido | Presente | Observação |
|---|---|---|
| Capa: título, tipo (mista), orientador, coorientador | sim | tipo "mista" coerente com D12 |
| Introdução: problema, importância, objetivos geral e específicos | sim | — |
| MSI II: resumo dos objetivos do MSI I e dos resultados alcançados | sim | agora separa relatório congelado do que veio depois |
| Referencial com soluções/ferramentas existentes e comparação | sim | tabela Gephi/NodeXL/4CAT/Hoaxy |
| Metodologia: passos e abordagem | sim | E1–E6 |
| Resultados esperados | sim | — |
| Cronograma em semanas | sim | semanas relativas; datas do Moodle pendentes (rascunho). `visao-projeto.md` ainda diz "defesa final: novembro de 2026", data do calendário antigo |
| Referências | sim | 13 entradas após o corte de §8 (10 bibliográficas + 3 notícias do caso Roberto Jefferson) |
| Papel da IA declarado | sim | — |
| Máximo de 10 páginas | provável | corpo ≈ 2.520 palavras após o corte (o do TCC1 tinha 2.482) + 13 referências (≈ 370 palavras); com folga para as 10 páginas. O corpo da proposta do TCC1 tinha 2.482 palavras. Confirmar no PDF |

---

## 5. Alterações aplicadas em `docs/proposta-tcc2.md` (todas factuais; reverter é seguro)

1. **Resumo do MSI I.** "Os resultados foram" → "Os resultados relatados foram"; o bullet de hidratação e
   leitor web saiu da lista de resultados do relatório e virou um período próprio ("Entre a entrega do
   relatório e esta proposta..."), com menção à leitura manual preliminar. "Consistente com [4]" mudou da
   frase do 30/10 para a frase do polo lacrado; o 30/10 ficou com "menor segregação pelas métricas de
   partição (modularidade e assortatividade)".
2. **Hermeticidade por super-polo.** "igualmente herméticos (acima de 0,99)" → "herméticos em grau comparável
   (0,98 a 0,9999 nos três eventos de confronto) e ... o polo subdividido é tão ou mais fechado que o
   monolítico", com a ressalva de que a medição é preliminar e será incorporada à pipeline na E1.
3. **Caso Roberto Jefferson.** Citação [5] → [5]–[7]; inseridas as referências AP/Global News e Poder360 (as
   que a auditoria indica para "aliado de Bolsonaro" e "tiros e granadas"); todas as referências de [6] em
   diante renumeradas (+2) no texto e na lista. Ordem de citação e lista conferidas por script.
4. **SBM aninhado.** "decide estatisticamente" → "com seleção por descrição mínima, oferece um critério
   independente para avaliar".

5. **Segunda rodada, após as decisões do autor (mesmo dia).** Título trocado pelo do relatório final do TCC1
   (*Análise estrutural das comunidades no Twitter brasileiro durante o ciclo eleitoral de 2022*); no parágrafo
   de P1, acrescentadas a frase sobre o terceiro grupo do 7/9 e a do 30/10 no nível do polo (96,6% e 3,4% dos
   nós); inserido o parágrafo "O que muda em relação ao plano do MSI I" antes do objetivo geral; Sunstein 2002
   citado na "polarização de grupo" e inserido como [9] (metadados conferidos no Crossref), com renumeração de
   [9] em diante (+1). Total: 32 referências, ordem de citação reconferida.

Nada mais foi alterado. O arquivo ainda não está versionado (`git status` o lista como novo), então não há `git diff`; a lista acima é o registro completo das mudanças.

---

## 6. Decisões tomadas pelo autor (2026-10-06)

| Ponto | Decisão | Onde foi aplicado |
|---|---|---|
| Título (§3.3) | Manter o do relatório final do TCC1 | `proposta-tcc2.md`, capa |
| Pergunta central (§3.1) | Atualizar `visao-projeto.md` com data e motivo | `visao-projeto.md`: nova pergunta + nota "Reformulação registrada em 2026-10-06" (três motivos); entregável 3 com nota de revisão; seção Identificação com datas rotuladas TCC1/TCC2 |
| Escopo do MSI I (§3.2) | Inserir o parágrafo e registrar D7/D8/D10 | `proposta-tcc2.md` (parágrafo antes do objetivo geral); `decisoes-metodologicas.md`: blocos "Revisão (2026-10-06)" em D7, D8 e D10 + três linhas no histórico |
| 30/10 e terceiro grupo (§1.2, itens 3 e 4) | Acrescentar as duas frases | `proposta-tcc2.md`, parágrafo de P1 |
| Sunstein | Acrescentar Sunstein 2002 para a polarização de grupo | `proposta-tcc2.md`, §2 e referência [9] |
| Kessler | Manter como está (ideia atribuída a Kessler, formulação matricial a [16]) | — |
| Ajustes de tom (§3.5 e §3.6: "se mostrou confuso", frase E1→ferramenta, veredito com caracterização, TSE) | Nenhum agora; o autor corrige depois | — |

## 7. Pendências restantes

1. Ajustes de tom listados acima, a cargo do autor.
2. Referências: Pariser (ficha catalográfica), Kessler (obter pelo Portal CAPES antes do artigo final), Recuero
   2024 (URL/páginas), Gatti e NodeXL (confirmar edição), Hoffmann da Silva (grafia), Interian (versão publicada).
3. Datas do cronograma e da seção Identificação da visão pelo Moodle; conferir o número de páginas no PDF.
4. Reproduzir na pipeline (E1) a hermeticidade por super-polo de §1.1, hoje medida por script de sessão.

---

## 8. Corte de referências (2026-10-06, decisão do autor)

**Motivo:** 32 referências é mais do que um estudante consegue ler com profundidade no prazo de uma proposta; a lista
passa a ter as 10 de maior impacto no texto, mais as 3 notícias do caso Roberto Jefferson como adendo (só elas).
Rodapés com URL não entram na contagem.

**Ficam (ordem de citação):** [1] Bastos e Recuero 2023 · [2] Pariser 2012 · [3] Sunstein 2017 · [4] Interian e
Rodrigues 2023 · [5] STF 2022 · [6] AP/Global News 2022 · [7] Poder360 2022 · [8] Alabarse dos Santos et al. 2024 ·
[9] Recuero, Soares e Zago 2021 · [10] Hoffmann da Silva e Recuero 2025 · [11] Conover et al. 2011 (ICWSM) ·
[12] Kessler 1963 · [13] Traag et al. 2019.

**Saem (19), para reaproveitar no artigo final:** Sunstein 2002; Recuero, Soares e Gruzd 2020; Conover et al. 2011
(PASSAT, 95%); Perianes-Rodriguez et al. 2016; van Eck e Waltman 2009; Becatti et al. 2019; Pacheco et al. 2021;
Mattei et al. 2022; Good et al. 2010; Fortunato e Barthélemy 2007; Traag, Van Dooren e Nesterov 2011; Lancichinetti e
Fortunato 2012; Peixoto 2014; Recuero 2024; Gatti 2005; Gephi, NodeXL, 4CAT e Hoaxy (viraram rodapés com o site).
Os metadados auditados de todas continuam na tabela de §2 e em `guia-citacoes-tcc2.md`.

**O que mudou no texto:**
- §2 Bolhas: a polarização de grupo fica atribuída a #Republic [3]; conferir o capítulo antes da entrega.
- §2 Polarização no Brasil: sai a frase sobre 2018; a literatura do grupo de Recuero é representada só pelo artigo da
  hidroxicloroquina, e "polarização assimétrica" fica definida por ele.
- §2 Co-retweet: Conover citado uma vez (dois grupos segregados; retweet como endosso); a fórmula *C = M·Mᵀ* fica sem
  citação; saem as frases sobre alternativas ao Jaccard e sobre precedentes de projeção; "comunidades discursivas"
  passa a termo nosso.
- §2 Robustez: os três motivos ficam como conhecimento corrente ("bem estabelecidos na literatura"), sem citação; o
  SBM idem.
- §2 Métodos digitais: parágrafo reescrito sem Recuero 2024; a tendência a métodos mistos fica apoiada em [9], [10];
  grupo focal sem referência de método.
- Tabela de ferramentas mantida, com rodapés para os sites.
- E1 perde a faixa de citações; E4 perde a citação na linha de ética.

**Risco assumido:** a E1 (robustez) e o grupo focal ficam sem âncora bibliográfica na proposta. Se a banca cobrar,
Fortunato e Barthélemy 2007 e Gatti 2005 são as primeiras a voltar.
