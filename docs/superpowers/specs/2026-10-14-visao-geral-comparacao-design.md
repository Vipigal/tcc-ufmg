# Visão geral, comparação e mídias no leitor — design (2026-10-14)

Evolução do leitor web (`web/`, D15) para a etapa E4 da proposta do TCC2 (`docs/proposta-tcc2.md`):
comparação lado a lado de grupos, sínteses com links para os tweets, explicação acessível do método.
Consome as sínteses do M11 (`docs/superpowers/specs/2026-10-13-sintese-clusters-llm-design.md`).
Design aprovado pelo autor em 2026-10-14 sobre mockups (`.superpowers/brainstorm/…/dark-v2.html`).

## 1. Objetivo e público

Pesquisadores de comunicação e ciência política (grupo focal, E5), que não vêm da computação. A
ferramenta deve deixar a **forma** da polarização legível de relance (quem está isolado, quem é
"irmão" de quem) e levar do resumo ao tweet em poucos cliques. Tudo continua estático (JSON gerado
pela pipeline, sem backend).

## 2. Telas e navegação

Três telas por evento, com as abas dos eventos e um seletor fixo **Visão geral · Ler grupo · Comparar**.
Trocar de evento mantém a tela atual.

| Rota | Tela |
|---|---|
| `/:evento` | **Visão geral** (nova; entrada padrão; `/` → primeiro evento) |
| `/:evento/:community` | **Leitor do grupo** (o atual: síntese + thread de tweets), mantido |
| `/:evento/comparar/:a/:b` | **Comparação** (nova) |

### 2.1. Visão geral
Mini-mapa DRL (o atual) + um **cartão por grupo**, na ordem `group`:
- cor, "Grupo g", % dos usuários;
- **tag de inclinação** (§3.2);
- **trecho curado** da síntese (§3.1), entre aspas;
- "quem mais é retuitado": 3 primeiras contas de `top_accounts`;
- **barra de conteúdo compartilhado** (§4) + frase: "quase nada em comum com os outros grupos"
  (< 10%) ou "compartilha boa parte com o Grupo X" (irmão de maior participação);
- ações: "ler o grupo →" e "comparar ⇄". Marcar "comparar" em dois cartões habilita
  "comparar Grupo a × Grupo b →".
- Link "saiba mais" abre a explicação do método em linguagem simples (o que é um ponto, um grupo,
  a barra, a síntese por LLM e seus limites, a tag).
Grupo sem curadoria: cartão mostra só os dados calculados e "síntese ainda não curada".

### 2.2. Leitor do grupo (mantido)
Igual ao atual (`SummaryPanel` + `CardList` com filtro de origem), com: a síntese **recolhível**,
a tag de inclinação no painel e na lista de grupos lateral, e mídias nos cards (§5).

### 2.3. Comparação
- Barra superior: seletores dos dois grupos; "em comum": % de compartilhamento de cada lado
  (§4, `shared_with`), nº de tweets presentes nas duas seleções (top-K ∪ cauda), contas em comum
  entre os `top_accounts`.
- Duas colunas, cada uma: tag; síntese recolhível (aberta no trecho curado, "ler tudo ▾"); contas;
  seção **mais amplificados** (top 3 do top-K) e seção **característicos (só deste grupo)** (top 3 da
  cauda), como previews de tweet com mídia. "ver todos →" leva ao leitor do grupo com o filtro de
  origem correspondente.

### 2.4. Tema
**Modo escuro como padrão**, com alternância claro/escuro no cabeçalho, lembrada em `localStorage`
(com try/catch; sem armazenamento → escuro). As cores passam a tokens CSS (`--color-bg`,
`--color-surface`, `--color-ink`, `--color-muted`, `--color-line`) redefinidos por
`[data-theme]`. Paleta escura de referência: fundo `#000`, superfície `#16181c`, linha `#2f3336`,
texto `#e7e9ea`, secundário `#71767b`. As cores dos grupos (PALETTE) ganham variante clareada no
escuro onde o contraste exigir (ex.: Grupo 1 `#5E4FA2` → `#7c6fd0`). Mini-mapa com fundo escuro e
halo dos rótulos escuro.

## 3. Curadoria (estática, humana)

Arquivo versionado `data/curation/clusters.json`, editado à mão, um item por (evento, community):

```json
{ "event": "invasao-3-poderes", "community": 0,
  "summary": { "model": "claude-sonnet-5-5", "prompt_version": "v1" },
  "trecho": "O material trata o 8 de janeiro quase inteiramente como ataque …",
  "eixo": "esquerda", "notas": "" }
```

### 3.1. Trecho
**Recorte literal** da `sintese` referenciada — uma **lista de fragmentos**, cada um substring exata,
exibidos unidos por " … " (ajuste de 2026-10-14: o que distingue um grupo costuma estar em frases
não contíguas; citações `[id]` podem ser omitidas
do recorte, que é comparado com o texto sem elas). O M10 **falha** se o trecho não for substring, e
marca `stale` se a síntese referenciada não for a mais recente `ok` do par. Por quê: o trecho
continua sendo "o que o LLM gerou", e a medida de qualidade das sínteses (proposta, §4) não se
mistura com a curadoria. Rascunho inicial dos 15 trechos proposto pelo agente, revisado pelo autor.

### 3.2. Tag de inclinação
`eixo ∈ {direita, esquerda, outro}`; cores: **direita azul, esquerda vermelho, outro amarelo**.
Atribuída pelo autor, lendo o `inclinacao_politica.texto` do LLM; exibida como "esquerda · LLM"
(a tag traduz a leitura do LLM; a confiança do LLM aparece no leitor e na comparação). Rascunho
inicial proposto pelo agente a partir do texto do LLM.

*Trade-off registrado (revisão de D8):* um binário colorido contraria a revisão de D7 e a proposta
("esquerda e direita descrevem mal os polos") e é a primeira coisa que o grupo focal vê antes de
rotular os polos. Decisão do autor; "outro" existe para os casos fora do binário (7/9 Grupo 4,
Ciro/PDT). Fica previsto parâmetro de URL `?tags=0` que oculta as tags (para as sessões do grupo
focal, se o autor quiser).

## 4. Métrica de conteúdo compartilhado (nova, D17)

Para o cluster *c*, sobre o log completo do evento (usuário×tweet distinto conta 1):

```
shared_with(c, d) = Σ_t rt_c(t) · rt_d(t) / rt_graph(t)  ÷  Σ_t rt_c(t)
shared(c)         = Σ_{d≠c} shared_with(c, d) = 1 − pureza média dos tweets de c, ponderada por rt_c
```

Leitura: "dos retweets que o grupo *c* dá, que fração vai a conteúdo que também circula em *d*".
Mesma noção de **pureza** que o leitor já exibe por tweet. Não depende de definir polos. É
assimétrica (o grupo menor compartilha mais com o maior) — o "saiba mais" explica.

Valores medidos em 2026-10-14: polos fechados 1–3% (7/9 c0, RJ c1, eleições c3, 8/1 c1); fatias
irmãs 22–77% (8/1 c2→c0 50%, c0→c2 21%; RJ c2→c0 59%; 7/9 c2→c1 46%; eleições c4 77%); 7/9 c3
(Ciro) 24% com c0, 2% com c1.

Cálculo: estágio novo da pipeline (`modules/overlap.py`, `ContentOverlap`, `Stage` com
`FILES = ("content_overlap.json",)`), exportado em `event.json` por cluster como
`shared` e `shared_with: {community: frac}`. Relação com a hermeticidade da E1: aquela é medida no
grafo de usuários por super-polo; esta, no conteúdo, por cluster — complementares.

## 5. Mídias

- **Re-hidratação** dos tweets com mídia (495 tweets, 575 mídias: 312 fotos, ~262 vídeos, 1 GIF),
  identificados pelo `media_key` em `entities.urls`. `XClient.lookup_tweets_media(ids)` com
  `expansions=attachments.media_keys` e `media.fields=type,url,preview_image_url,width,height,
  alt_text,variants`. Custo: US$ 0,005 × tweets devolvidos + objetos de mídia (preço a confirmar
  na execução; o relatório registra quantos vieram).
- **Não** reescreve `tweets` (snapshot da 1ª hidratação, README princípio 3). Novas tabelas:
  `media (media_key PK, type, url, preview_image_url, width, height, alt_text, raw_json,
  hydrated_at)` e `tweet_media (tweet_id, media_key, position, PK (tweet_id, media_key))`.
  Estágio `MediaHydrator` (M9c, em `modules/hydrate.py`), mesmo padrão de cache pelo banco:
  pendentes = tweets com `media_key` sem linha em `tweet_media` nem erro registrado.
- **Exibição sem desfoque** (decisão do autor). Fotos/GIF: imagem (`url`) carregada do servidor do
  X, grade de 1–4. Vídeo: `preview_image_url` com ▶; clique abre o tweet no X (sem player).
  Mídia que não voltou: o chip atual "Mídia ↗".
- Export: `tweet.media = [{type, url, preview_image_url, width, height, alt_text}]`.

## 6. Mudanças por componente

Pipeline: `modules/overlap.py` (novo), `MediaHydrator` + `XClient.lookup_tweets_media`,
`Database` (tabelas `media`, `tweet_media`), `WebExporter` (curadoria + overlap + mídia),
notebook `pipeline_tcc2.ipynb` (células M9c e overlap), README do banco, D17 e revisão de D8 em
`decisoes-metodologicas.md`.

Web: rotas novas; `Overview` (cartões + mini-mapa), `Compare`, `TweetPreview` (variante compacta do
`TweetCard`, com mídia), `MediaGrid`, `InclinationTag`, `SharedBar`, `MethodExplainer`;
`ThemeToggle` + tokens; `types.ts` (curadoria, overlap, mídia).

## 7. Testes

- `ContentOverlap`: valores à mão num log de brinquedo (inclusive simetria/assimetria e soma).
- `MediaHydrator`: cliente falso; pendentes, gravação em `media`/`tweet_media`, erros, idempotência.
- `WebExporter`: trecho inválido falha; `stale`; `shared`/`shared_with`; `tweet.media`.
- Web (vitest): seleção de dois grupos para comparar; frase da barra; leitura do tema com
  `localStorage` indisponível; montagem do caminho de comparação.
- Verificação visual no navegador (escuro e claro) das três telas.

## 8. Fora de escopo

Máscara de @ de perfis pessoais (sugerida no mockup, não adotada); player de vídeo embutido;
comparação de mais de dois grupos; resumo curto gerado por LLM (o trecho é curado).
