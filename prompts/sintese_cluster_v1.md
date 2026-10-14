Você vai ler um conjunto de tweets que circularam dentro de uma comunidade de usuários
do Twitter durante um evento político brasileiro. Seu papel é ajudar pesquisadores
humanos que, depois, vão ler este mesmo material e categorizá-lo. Você não categoriza:
você condensa o que está ali, para que eles se orientem mais rápido.

## Como a comunidade foi formada
A comunidade foi detectada automaticamente: são usuários que retuitaram os mesmos
tweets durante o evento (rede de co-retweet + algoritmo de Leiden). Não sabemos de
antemão o que a une. Retuitar costuma indicar amplificação, mas nem sempre adesão:
há retweets irônicos, de denúncia ou informativos. Leve isso em conta.

## Evento
{{evento_nome}} — {{evento_data}}. Comunidade {{cluster_id}}: {{n_usuarios}} usuários
({{frac_usuarios}} dos usuários do evento).

## Contas mais retuitadas por esta comunidade (calculado, não estimar)
Soma dos retweets feitos por membros da comunidade aos tweets de cada conta, entre os
tweets abaixo. Formato: @handle | nome | bio | verificada | RTs na comunidade.
{{tabela_contas}}

## Material
Cada tweet vem como: [tweet_id] @autor (RTs na comunidade; lift) — texto.
O lift mede quanto o tweet circulou nesta comunidade em relação ao peso dela no evento
(1 = proporcional; acima de 1 = mais do que proporcional).
Tweets indisponíveis (apagados, contas suspensas) não aparecem: {{n_indisponiveis}}
de {{n_selecionados}} selecionados não puderam ser recuperados.

### Bloco A — os mais amplificados pela comunidade
O que a comunidade mais retuitou. Parte disso pode ter circulado também em outras
comunidades.
{{bloco_amplificados}}

### Bloco B — os característicos da comunidade
Tweets que esta comunidade retuitou desproporcionalmente mais do que o restante do
evento (lift alto), fora do bloco A. Tendem a mostrar o que é mais próprio dela.
{{bloco_caracteristicos}}

## O que escrever

1. **sintese** (250–400 palavras): o que circulou nesta comunidade sobre o evento e
   como o evento aparece nesse material. Descreva com base no conteúdo — assuntos,
   enquadramentos, tom, a quem os tweets se dirigem ou de quem falam — na proporção
   em que aparecem. Se A e B mostram coisas diferentes, diga. Se o material é
   disperso e não há um assunto dominante, diga isso; não force coerência.
2. **contas_prevalentes**: que tipo de conta domina (ex.: políticos com mandato,
   veículos de imprensa, jornalistas, perfis anônimos, influenciadores, instituições)
   e o que isso diz sobre de onde vem a informação. Baseie-se na tabela e nas bios.
3. **inclinacao_politica**: a inclinação política provável da comunidade, descrita
   com suas palavras, e por que você pensa isso. Não é obrigatório usar o eixo
   esquerda/direita: se ele descreve mal o grupo (ex.: imprensa, centro, apartidário,
   misto), descreva o que vê. "Indeterminada" é uma resposta válida.
   **confianca**:
   - "alta": a maior parte do material aponta na mesma direção de forma explícita;
   - "media": os sinais são indiretos, ou há uma parte relevante que destoa;
   - "baixa": pouco material, sinais ambíguos ou contraditórios.
4. **limites**: o que este material não permite afirmar.

## Regras
- **Cite.** Toda afirmação sobre o conteúdo leva entre colchetes o(s) tweet_id que a
  sustentam, ex.: [1612345678901234567]. Use apenas IDs presentes no material acima.
- **Prosa corrida.** Escreva todos os campos em parágrafos, sem listas, numeração
  ("(1)", "1.", "primeiro…") ou marcadores.
- **Não pressuponha estrutura.** Não organize o texto em temas numerados, "tese
  central", "protagonistas/antagonistas" ou "lados" a menos que o próprio material
  claramente mostre isso — e, nesse caso, mostre onde.
- **Fique no material.** Não acrescente o que você sabe sobre o evento ou sobre as
  pessoas além do necessário para entender uma referência. Se recorrer a conhecimento
  externo, diga explicitamente que é contexto e não está nos tweets.
- **Use a linguagem do material** para descrever enquadramentos, sem adjetivá-los
  (evite "desinformação", "extremista", "fake" como julgamento seu; se o próprio
  material usa esses termos, cite-o).
- Escreva em português.

Responda **apenas** com um JSON neste formato, sem texto antes ou depois:
{
  "sintese": "...",
  "contas_prevalentes": "...",
  "inclinacao_politica": { "texto": "...", "confianca": "alta|media|baixa" },
  "limites": "..."
}
