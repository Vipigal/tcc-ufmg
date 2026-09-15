# Leitor de clusters — design e spec de implementação (fase 2)

**Data:** 2026-09-15 · **Status:** aprovado pelo autor do TCC; implementação prevista para a
sessão seguinte, em uma sessão · **Decisão associada:** D15 em `docs/decisoes-metodologicas.md`.

Este documento é autocontido: quem implementar o app precisa dele, do repositório e de
`data/export/` já gerado pela pipeline da fase 2 (`notebooks/pipeline_tcc2.ipynb`). Não é
necessário rodar a pipeline para desenvolver o front.

---

## 1. Objetivo

A ferramenta tem **dois objetivos, nesta ordem**:

1. **Ser o embrião da navegação interativa do produto final.** O entregável central do TCC é a
   aplicação web pública (D9; `docs/visao-projeto.md`, entregável 3). O que se constrói aqui é o
   primeiro módulo dessa aplicação — o componente B da spec técnica (§5.2, "Habite a bolha")
   nasce deste leitor. Nada aqui é descartável: mesma stack, mesmo repositório, mesmos dados.
2. **Ser ferramenta analítica para o pesquisador.** Antes de existir rótulo ou síntese narrativa
   (D7, D8, §4), o autor precisa **ler** os tweets mais amplificados por cada cluster em contexto:
   onde o cluster está na estrutura (mini-mapa), quão exclusivo de cada cluster cada tweet é
   (pureza), onde mais ele aparece (sobreposição), como a métrica pública se compara ao alcance
   dentro do evento, e o que a API não devolveu (atrição). É com essa leitura que se avalia a
   narrativa de cada cluster e a disposição dos tweets dentro dele.

O leitor **não rotula nem ranqueia ideologicamente** nada (postura do `CLAUDE.md`): ele mostra
comunidades numeradas por tamanho, com cores neutras, e deixa a interpretação para quem lê.

## 2. Decisões aprovadas (2026-09-15)

| # | Decisão | Consequência |
|---|---|---|
| 1 | **Autores hidratados** (`/2/users`) antes do app | O card mostra nome, @handle, avatar, verificado, seguidores. Contas suspensas/removidas ficam em `lookup_errors` e o card mostra o motivo. |
| 2 | **Só leitura** | Sem anotações, sem edição, sem backend. Anotar por tweet exigiria caminho de escrita no banco — fica para outra decisão. |
| 3 | **Mídia como placeholder** | Não temos objetos de mídia (sem `expansions`). Links `t.co` com `media_key` viram um chip "Mídia" que abre o tweet original em x.com. |
| 4 | **Mini-mapa em Sigma.js** | Nós apenas, sem arestas; é a biblioteca do grafo do produto final (§5.1). |
| 5 | **Dentro do app final**, em `web/` | Rota "modo analista"; publicável na Vercel sem mudança de código. |
| 6 | **Imitar o X sem marca registrada** | Layout e tipografia do card do X como base; ícones genéricos; sem logotipo nem assets da marca. |

Stack **fixada** pela visão do projeto (`docs/visao-projeto.md`, "Stack técnica"): React +
Sigma.js + Tailwind. Dados estáticos, sem backend (spec §5.3).

## 3. Escopo da v1 e fora de escopo

**Dentro (v1, uma sessão):** escolher evento e cluster; mini-mapa DRL com o cluster em destaque;
lista dos top-K do cluster em cards estilo X com métricas públicas e metadados da pesquisa; cards
fantasma para slots não devolvidos; ordenar, filtrar e buscar; URL que aponta para
evento + cluster; tudo em português.

**Fora (explicitamente):** anotações ou rótulos manuais; grafo com arestas; filtro temporal
(componente C); painel de síntese narrativa (vem depois de §4); comparação lado a lado de dois
clusters (componente B completo — o leitor é a metade dele); hidratação de mídia; tweets citados
com texto (só o link); autenticação; deploy (mas nada pode impedir um `vite build` + Vercel).

## 4. Requisitos

### 4.1 Funcionais

- **RF1 Evento.** Abas com os quatro eventos (nome e data). Trocar de evento carrega
  `tweets.json` e `layout.json` do evento e seleciona o Grupo 1.
- **RF2 Cluster.** Painel com os clusters selecionados do evento (os ≥ 1% dos nós), na ordem
  "Grupo 1..n" por tamanho, cada um com: cor, `Grupo g (c<community>)`, % dos nós, peso interno %,
  K, `hidratados/selecionados`, atrição %. Clicar seleciona. O cluster selecionado fica evidente.
- **RF3 Mini-mapa.** Scatter das coordenadas DRL do evento (nós da componente gigante), cluster
  selecionado na sua cor, demais em cinza, comunidades < 1% em cinza sempre. Rótulo
  `Grupo g · XX%` no centróide de cada cluster selecionável. Clicar num nó seleciona sua
  comunidade. Mesmas cores e numeração da figura da fase 1 (`assets/grafo-comunidades-drl-anotado.png`).
- **RF4 Lista de cards.** Os K slots do cluster, um card por slot, na ordem do ranking por
  padrão. Cabeçalho da lista: `Grupo g · K slots · h hidratados · a não devolvidos`.
- **RF5 Card estilo X** (tweet hidratado): avatar, nome, @handle, selo se verificado, data e hora
  (pt-BR, fuso de Brasília), texto com hashtags, menções e links clicáveis, chip "Mídia" quando
  houver, "citando / respondendo" quando `referenced_tweets` não for vazio, métricas públicas
  (respostas, reposts, citações, curtidas, salvos, impressões) abreviadas, idioma, e link "abrir
  no X" para `tweet.url`. Marca "possivelmente sensível" quando `possibly_sensitive`.
- **RF6 Faixa de metadados da pesquisa** (sempre, mesmo em card fantasma): `#rank de K`,
  `rt_cluster` ("RTs de membros"), `rt_graph`, `rt_event`, pureza (0–1, duas casas), "também em
  Grupo x (#r)" para cada `also_in`, e a razão entre `metrics.retweet_count` (API, global) e
  `rt_event` (dataset). Cada item com tooltip explicando o que é (glossário em §7.6).
- **RF7 Card fantasma.** Slot com `status != "hydrated"`: mesmo lugar na lista, borda tracejada,
  motivo legível (`not_found` → "Tweet removido ou indisponível"; `not_authorized` → "Conta
  suspensa ou protegida"; `error` → `error.title`; `pending` → "Ainda não hidratado"), o
  `tweet_id` e um link para `https://x.com/i/web/status/<id>`. A faixa de metadados aparece normal.
- **RF8 Autor indisponível.** Tweet hidratado com `author == null`: avatar genérico e texto
  "Autor não disponível" + motivo por `author_status` (`not_found` → "conta removida";
  `not_authorized` → "conta suspensa ou protegida"; `pending` → "não hidratado") + `author_id`.
- **RF9 Ordenar, filtrar, buscar.** Ordenação: rank (padrão), pureza ↓, `rt_graph` ↓,
  reposts na API ↓, data ↑. Filtros: status (todos / só hidratados / só não devolvidos);
  exclusividade (todos / exclusivos, pureza ≥ 0,90 / compartilhados, pureza < 0,50). Busca
  textual no texto do tweet, nome e @handle, sem distinção de caixa e acentos. Contador
  "mostrando n de K".
- **RF10 URL.** `/:evento/:community` reflete o estado; abrir a URL reproduz evento e cluster.
  `/` redireciona para o primeiro evento do índice e seu Grupo 1.

### 4.2 Não funcionais

- **Sem backend.** Só `fetch` de JSON estático em `data/export/` (servido pelo Vite).
- **Local-first.** `npm run dev` abre a ferramenta; atualizar dados = re-executar a célula M10 do
  notebook (o front só recarrega).
- **Volume.** 4 eventos × ≤ 5 clusters × ≤ 100 slots; `layout.json` até ~33 mil pontos
  (~1 MB). Render do mini-mapa em WebGL (Sigma) e lista virtualizada **não é necessária** (≤ 100
  cards por cluster).
- **Português** em toda a interface; números e datas em pt-BR.
- **Reprodutibilidade.** O app não computa nada da pesquisa: pureza, grupo, atrição etc. vêm
  prontos do export. Se um número aparece na tela, ele existe no JSON.
- **TypeScript** com tipos do contrato de dados (§5) em um único arquivo.

## 5. Dados — contrato de `data/export/`

Gerado por `modules/export.py` (`WebExporter`, M10) a partir de `data/processed/<evento>/`
(M7, M8) e do banco `data/database/hydrated.sqlite` (M9). **Determinístico** para o mesmo banco.
Os arquivos são versionados no git, então o front pode ser desenvolvido sem rodar a pipeline.

```
data/export/
├── index.json                    # ponto de entrada
├── invasao-3-poderes/
│   ├── event.json                # mesmo objeto que aparece em index.events[i]
│   ├── tweets.json               # array de slots (cluster, rank)
│   └── layout.json               # coordenadas DRL
├── eleicoes/ …  mobilizacao-0709/ …  roberto-jefferson/ …
```

Servir `data/export/` na raiz do dev server: em `web/vite.config.ts`, `publicDir: "../data/export"`
(caminho relativo à raiz do app). Então `fetch("/index.json")`, `fetch("/invasao-3-poderes/tweets.json")`.
Alternativa equivalente: symlink `web/public/data -> ../../data/export` e prefixo `/data/`.

### 5.1 `index.json`

```ts
interface Index {
  generated_at: string;          // ISO-8601 UTC — único carimbo de tempo do export
  palette: string[];             // 10 cores hex; cor do Grupo g = palette[(g-1) % palette.length]
  events: EventMeta[];           // na ordem da pipeline (mobilizacao, roberto, eleicoes, invasao)
}
```

### 5.2 `event.json` / `EventMeta`

```ts
interface EventMeta {
  slug: string;                  // = nome da pasta; usado na URL
  name: string;                  // "Ataques de 8 de janeiro de 2023"
  event_date: string | null;     // "2023-01-08"
  n_nodes: number;               // nós do grafo (usuários)
  n_edges: number;               // arestas do backbone
  n_communities: number;         // comunidades Leiden, incluindo as < 1%
  run_config: Record<string, unknown>;   // parâmetros da fase 1 (N, τ, resolução…) — exibir em "sobre"
  selection: { k: number; k_small: number; min_frac: number; small_weight_frac: number };
  clusters: ClusterMeta[];       // só os selecionados (≥ min_frac), ordenados por group
  files: { tweets: string; layout: string };   // caminhos relativos a data/export/
}

interface ClusterMeta {
  community: number;             // id Leiden (estável nos dados; usar na URL)
  group: number;                 // 1..n por tamanho (numeração das figuras da fase 1)
  label: string;                 // "Grupo 1"
  color: string;                 // hex, da paleta
  n_nodes: number; frac_nodes: number;          // 0–1
  intra_weight_frac: number;     // peso interno / peso total do grafo (0–1); ≤ 0.05 ⇒ k = k_small
  k: number;                     // 100 ou 20
  n_selected: number;            // = k, salvo cluster com menos candidatos
  n_hydrated: number; n_not_found: number; n_not_authorized: number; n_other_errors: number; n_pending: number;
  attrition: number;             // (n_selected − n_hydrated) / n_selected
}
```

### 5.3 `tweets.json` — `Slot[]`, ordenado por (community, rank)

```ts
type SlotStatus = "hydrated" | "not_found" | "not_authorized" | "error" | "pending";
type AuthorStatus = "hydrated" | "not_found" | "not_authorized" | "error" | "pending" | null;

interface Slot {
  community: number; group: number; rank: number; k: number;
  tweet_id: string;
  rt_cluster: number;            // membros do cluster que retuitaram (critério do ranking)
  rt_graph: number;              // nós do grafo (qualquer cluster) que retuitaram
  rt_event: number;              // usuários do evento, inclusive periferia filtrada
  purity: number | null;         // rt_cluster / rt_graph, 4 casas
  also_in: { community: number; group: number; rank: number }[];   // outros clusters do MESMO evento
  status: SlotStatus;
  error: { title: string; detail: string } | null;   // só quando status ∉ {hydrated, pending}
  tweet: Tweet | null;           // null se não hidratado
  author_id: string | null;      // null se não hidratado
  author: Author | null;         // null se autor não hidratado/negado
  author_status: AuthorStatus;   // null quando o tweet não foi hidratado
}

interface Tweet {
  id: string; text: string; created_at: string; lang: string | null;
  source: string | null; possibly_sensitive: boolean | null; reply_settings: string | null;
  conversation_id: string | null; in_reply_to_user_id: string | null;
  metrics: { retweet_count: number|null; reply_count: number|null; like_count: number|null;
             quote_count: number|null; bookmark_count: number|null; impression_count: number|null };
  entities: {
    urls: { start: number; end: number; url: string; expanded_url?: string; display_url?: string; media_key?: string }[];
    hashtags: { start: number; end: number; tag: string }[];
    mentions: { start: number; end: number; username: string; id?: string }[];
  };
  referenced_tweets: { type: "quoted" | "replied_to" | "retweeted"; id: string }[];
  url: string;                   // https://x.com/i/web/status/<id>
}

interface Author {
  id: string; username: string | null; name: string | null; description: string | null;
  location: string | null; url: string | null; profile_image_url: string | null;
  protected: boolean | null; verified: boolean | null; verified_type: string | null;  // "blue" | "business" | "government" | "none"
  created_at: string | null;
  metrics: { followers_count: number|null; following_count: number|null; tweet_count: number|null; listed_count: number|null };
}
```

**Invariantes úteis:** `status === "hydrated"` ⇔ `tweet !== null`; `author !== null` ⇒
`author_status === "hydrated"`; `also_in` nunca inclui o próprio `community`; `rank` é 1-based e
contíguo dentro de cada `community`; o mesmo `tweet_id` pode aparecer em vários slots do evento.

**Offsets de entidades são em code points Unicode** (padrão da API do X), não em índices UTF-16.
Em JavaScript, fatiar com `Array.from(text)` (ver §7.5).

### 5.4 `layout.json`

```ts
interface Layout {
  n_nodes: number;               // nós do grafo
  n_plotted: number;             // nós da componente gigante (= x.length)
  top_k: number; seed: number;   // parâmetros do DRL (reprodutibilidade)
  x: number[]; y: number[];      // coordenadas (2 casas), mesma ordem que `community`
  community: number[];           // comunidade de cada nó plotado
  centroids: Record<string, [number, number]>;   // mediana (x, y) por comunidade — onde pôr o rótulo
  groups: Record<string, number>;                // community → group (todas as comunidades, inclusive < 1%)
}
```

### 5.5 Como regenerar

`notebooks/pipeline_tcc2.ipynb`, célula "Módulo 10". Re-executar o notebook inteiro é seguro e
não chama a API se nada mudou. Tamanhos de referência (2026-09-15): `tweets.json` 440–720 KB por
evento (eleicoes é o maior: 420 slots); `layout.json` 140 KB (eleicoes) a 510 KB (invasão);
`index.json` ~9 KB. Estado dos dados nessa data: 1.340 slots, 1.022 hidratados (76%), 318 não
devolvidos; todos os 1.022 tweets hidratados têm autor em `author` (0 autores negados pela API).

## 6. Arquitetura do app

### 6.1 Stack e dependências

- **Vite + React + TypeScript** (`npm create vite@latest web -- --template react-ts`).
- **Tailwind CSS** (v4, plugin `@tailwindcss/vite`; `@import "tailwindcss";` no CSS raiz).
- **Sigma.js** (v3) + **graphology** para o mini-mapa (nós apenas).
- **react-router-dom** para `/:evento/:community`.
- **lucide-react** para ícones genéricos (resposta, repost, curtida, salvo, impressão, link).
- **Vitest** para os dois utilitários testáveis (§10). Nada mais.

Versões: instalar as estáveis correntes e registrar em `package.json`; confirmar a API atual de
Sigma v3 e Tailwind v4 na documentação (context7) antes de escrever o mini-mapa e o config. Não
adicionar UI kit; o card é CSS próprio (Tailwind) para ter a fidelidade pedida.

### 6.2 Estrutura de pastas (proposta)

```
web/
├── index.html
├── vite.config.ts                # publicDir: "../data/export"; plugin tailwind
├── package.json
├── src/
│   ├── main.tsx                  # router
│   ├── App.tsx                   # layout: header (eventos) · coluna esquerda (mapa + clusters) · coluna direita (cards)
│   ├── types.ts                  # §5, literalmente
│   ├── data/
│   │   ├── loadIndex.ts          # fetch + cache em memória de index.json
│   │   └── loadEvent.ts          # fetch tweets.json + layout.json por slug (cache por slug)
│   ├── lib/
│   │   ├── entities.ts           # texto → segmentos (texto | hashtag | mention | url | media) — TESTADO
│   │   ├── format.ts             # formatCompact, formatDate, formatPct, normalize (busca) — TESTADO
│   │   └── glossary.ts           # textos dos tooltips (§7.6)
│   ├── components/
│   │   ├── EventTabs.tsx
│   │   ├── ClusterPanel.tsx      # lista de ClusterMeta
│   │   ├── MiniMap.tsx           # Sigma nodes-only + rótulos
│   │   ├── Toolbar.tsx           # ordenar / filtrar / buscar / contador
│   │   ├── TweetCard.tsx         # card X + faixa de pesquisa
│   │   ├── GhostCard.tsx         # slot não devolvido
│   │   ├── ResearchStrip.tsx     # faixa de metadados (usada pelos dois cards)
│   │   ├── Avatar.tsx            # imagem com fallback de iniciais
│   │   └── TweetText.tsx         # renderiza os segmentos de entities.ts
│   └── styles.css
└── README.md                     # como rodar, de onde vêm os dados, como atualizar
```

### 6.3 Roteamento e estado

- Rotas: `/` → redireciona para `/${index.events[0].slug}/${grupo1.community}`;
  `/:evento/:community`.
- Estado derivado da URL: evento e cluster. Estado local (não na URL): ordenação, filtros, busca.
- Dados em memória por slug (carregar uma vez; trocar de aba não re-baixa).
- Nenhum estado global além disso. Sem Redux/Zustand.

### 6.4 Layout de tela

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ Leitor de clusters   [Mobilização 7/9] [Roberto Jefferson] [Eleições 30/10] [8 de janeiro] │
├──────────────────────────────┬───────────────────────────────────────────────────────┤
│  MINI-MAPA (Sigma)           │  Grupo 2 (c0) · 100 slots · 84 hidratados · 16 não devolvidos │
│  ● cluster selecionado colorido│ [ordenar ▾] [status ▾] [exclusividade ▾] [buscar…]  84/100 │
│  ○ demais em cinza           ├───────────────────────────────────────────────────────┤
│  rótulos "Grupo g · XX%"     │ ┌───────────────────────────────────────────────────┐ │
├──────────────────────────────┤ │ (avatar) Nome ✓ @handle · 8 jan 2023, 15:42       │ │
│  CLUSTERS                    │ │ Texto do tweet com #hashtags @menções e links…    │ │
│  ● Grupo 1 (c1) 44% K=100    │ │ [Mídia ↗]                                         │ │
│    peso 35,8% · 72/100 · 28% │ │ 💬 1,2 mil  🔁 28,3 mil  ❝ 890  ♥ 45 mil  🔖 …  👁 … │ │
│  ● Grupo 2 (c0) 34% K=100 ◀  │ ├───────────────────────────────────────────────────┤ │
│    peso 20,4% · 84/100 · 16% │ │ #1 de 100 · 3.389 RTs de membros · pureza 0,75 ·   │ │
│  ● Grupo 3 (c2) 21% K=100    │ │ 4.496 no grafo · 11.802 no evento · API 28.348 (2,4×) │ │
│    peso 27,3% · 89/100 · 11% │ │ · também em Grupo 3 (#12)                          │ │
│                              │ └───────────────────────────────────────────────────┘ │
│  Evento: 33.305 nós · 12,0 mi│ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐ │
│  arestas · 11 comunidades    │   #3 · Tweet removido ou indisponível · id 1612… ↗   │ │
│  N=7 τ=0,1 · K=100/20        │   2.787 RTs de membros · pureza 0,84                 │ │
│                              │ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘ │
└──────────────────────────────┴───────────────────────────────────────────────────────┘
```

Largura mínima alvo: 1280 px (ferramenta de mesa). Abaixo disso, coluna esquerda vira topo.
Sem dark mode na v1.

## 7. Especificação da interface

### 7.1 Cabeçalho e abas de evento

Título "Leitor de clusters". Uma aba por `index.events[]`: `name` curto (definir em um mapa
local slug → rótulo curto: "Mobilização 7/9", "Roberto Jefferson", "Eleições 30/10",
"8 de janeiro") e `event_date`. Aba ativa sublinhada. Trocar aba → navega para
`/${slug}/${clusterGrupo1.community}`.

### 7.2 Painel de clusters

Um item por `ClusterMeta`, ordem `group`. Linha 1: bolinha na `color`, `label`, `(c${community})`,
`${frac_nodes}%`, `K=${k}`. Linha 2, menor e cinza: `peso interno X,X%` ·
`${n_hydrated}/${n_selected} hidratados` · `atrição XX%`. Selecionado: fundo tingido com a cor
a 10% e borda esquerda na cor. Rodapé do painel: `n_nodes` nós, `n_edges` arestas (abreviado),
`n_communities` comunidades, `N=${run_config.min_user_retweets} τ=${run_config.tau}`,
`K=${selection.k}/${selection.k_small}`.

### 7.3 Mini-mapa (Sigma, nós apenas)

- Um `graphology.Graph` com `n_plotted` nós: `x`, `y` (Sigma inverte y em relação ao
  matplotlib — se a figura sair espelhada em relação à da fase 1, usar `-y`), `size` ≈ 1–1,5,
  `color`, atributo `community`. **Nenhuma aresta.**
- Settings: `renderLabels: false`, `enableEdgeEvents: false`, `allowInvalidContainer: true`.
- Cor: `nodeReducer` devolve `color: palette[(group-1)%10]` se `community === selecionado`,
  senão `#c7ccd6` (cinza da fase 1); comunidades sem `ClusterMeta` (< 1%) sempre cinza.
  Trocar a seleção → `sigma.refresh()`; não reconstruir o grafo.
- Rótulos `Grupo g · XX%` para cada cluster selecionável, em HTML absoluto sobre o canvas, posição
  = `sigma.graphToViewport(centroids[community])`, atualizada em `afterRender`. Cor do texto =
  cor do grupo, halo branco (como na figura). Clicar no rótulo também seleciona.
- Eventos: `clickNode` → seleciona `community` do nó (navega). Zoom/pan padrão do Sigma;
  botão "recentrar" chama `camera.animatedReset()`.
- Primeiro render: `camera` ajustada para caber todos os nós (Sigma faz isso por padrão).

### 7.4 Card do tweet (estilo X)

Anatomia, de cima para baixo, com as classes/medidas como referência do X (não exigência):

1. **Linha do autor.** Avatar 40 px redondo (`profile_image_url`; `onError` → iniciais do `name`
   sobre a cor do grupo). Nome em negrito; selo de verificado (ícone genérico, tooltip
   `verified_type`); `@username` em cinza; `·`; data/hora `formatDate(created_at)`; à direita,
   ícone "abrir no X" → `tweet.url` (nova aba). Tooltip do nome: `description`, `location`,
   `followers_count` seguidores.
2. **Texto.** `TweetText` (§7.5). 15–16 px, quebra de linha preservada (`whitespace-pre-wrap`).
3. **Anexos.** Chip "Mídia ↗" (→ `tweet.url`) se houver url com `media_key`. Linha "citando um
   tweet ↗" / "em resposta a um tweet ↗" para `referenced_tweets` (link
   `https://x.com/i/web/status/<id>`).
4. **Métricas públicas.** Linha cinza com ícones: respostas, reposts, citações, curtidas, salvos,
   impressões — `formatCompact`. `null` → "—". `lang` como badge pequeno. Se
   `possibly_sensitive`, badge "sensível".
5. **Faixa de pesquisa** (`ResearchStrip`, §7.6), separada por uma linha fina, fundo levemente
   tingido com a cor do grupo.

Card fantasma (`GhostCard`): mesma largura, borda tracejada cinza, ícone de aviso, título pelo
`status` (RF7), `tweet_id` monoespaçado com link para x.com, e a mesma `ResearchStrip`.

### 7.5 Renderização do texto com entidades (`lib/entities.ts`)

Entrada: `text`, `entities`. Saída: `Segment[]` com `{ kind: "text" | "hashtag" | "mention" |
"url" | "media", text, href? }`.

Algoritmo:
1. `cps = Array.from(text)` (code points). Todos os offsets da API referem-se a `cps`.
2. Coletar entidades: hashtags → `{start,end,kind:"hashtag",href:"https://x.com/hashtag/"+tag}`;
   mentions → `{…,kind:"mention",href:"https://x.com/"+username}`; urls → se `media_key` →
   `kind:"media"` (texto exibido: "Mídia", href: `tweet.url`); senão `kind:"url"`, texto exibido
   `display_url ?? url`, href `expanded_url ?? url`.
3. Ordenar por `start`; descartar sobreposições (manter a primeira).
4. Varrer `cps` emitindo segmentos de texto entre entidades e os segmentos das entidades.
5. Colapsar segmentos `media` repetidos (vários `media_key` → um chip); se um `media` for o
   último segmento, não renderizar como texto — o chip fica na linha de anexos.

Links abrem em nova aba com `rel="noopener noreferrer"`. Hashtag e menção em azul do X
(`#1d9bf0`); url mostra `display_url`.

### 7.6 Faixa de pesquisa e glossário (tooltips)

Itens, nesta ordem, separados por `·`:

| Item | Texto | Tooltip |
|---|---|---|
| Posição | `#${rank} de ${k}` | Posição no ranking do cluster pelo nº de membros que retuitaram. |
| Membros | `${rt_cluster} RTs de membros` | Usuários deste cluster (nós do grafo) que retuitaram. Critério de seleção (D6). |
| Pureza | `pureza ${purity.toFixed(2)}` | Fração dos retweets de nós do grafo que vieram deste cluster. 1,00 = só este cluster. |
| Grafo | `${rt_graph} no grafo` | Nós do grafo (qualquer cluster) que retuitaram. |
| Evento | `${rt_event} no evento` | Usuários do evento que retuitaram, inclusive os filtrados por atividade (N). |
| API | `API ${retweet_count} (${(retweet_count/rt_event).toFixed(1)}×)` | Reposts totais segundo a API hoje, e a razão para o alcance dentro do evento. Só se hidratado. |
| Também em | `também em Grupo ${g} (#${rank})` por `also_in` | O mesmo tweet está no top-K de outro cluster deste evento. |

Cores: pureza ≥ 0,90 em verde-escuro discreto; < 0,50 em laranja discreto; entre, neutro.
São **sinalizações de leitura**, não juízo — o tooltip deve dizer só o que o número é.

### 7.7 Barra de ferramentas (RF9)

`<select>` ordenação: "ranking (padrão)", "pureza", "RTs no grafo", "reposts na API", "mais
antigo primeiro". `<select>` status: "todos", "só hidratados", "só não devolvidos". `<select>`
exclusividade: "todos", "exclusivos (pureza ≥ 0,90)", "compartilhados (pureza < 0,50)". Campo de
busca com debounce de 200 ms; `normalize()` remove acentos e caixa (NFD + regex). Contador
`mostrando ${n} de ${k}` e botão "limpar".

### 7.8 Formatação (`lib/format.ts`)

- `formatCompact(n)`: `Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 })`
  → "28,3 mil", "1,2 mi". `null` → "—".
- `formatInt(n)`: `Intl.NumberFormat("pt-BR")` → "3.389".
- `formatPct(x, d=0)`: `x*100` com `d` casas e "%" → "44%", "35,8%".
- `formatDate(iso)`: `Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeStyle: "short",
  timeZone: "America/Sao_Paulo" })` → "8 de jan. de 2023, 15:42".
- `normalize(s)`: `s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase()`.

## 8. Comportamentos e estados

- **Carregando:** esqueleto simples no lugar do mapa e dos cards.
- **Erro de fetch:** mensagem "não encontrei `data/export/...`; rode a célula M10 do
  `pipeline_tcc2.ipynb`" — sem retry automático.
- **Cluster sem slots filtrados:** "nenhum tweet com esses filtros" + botão limpar.
- **Slug ou community inválidos na URL:** redireciona para o padrão do evento (ou do índice).
- **Avatar quebrado:** fallback de iniciais (X remove imagens de contas suspensas).
- **Trocar de evento** mantém ordenação/filtros; **trocar de cluster** também. Busca é limpa ao
  trocar de evento.

## 9. Critérios de aceitação

- [ ] `npm run dev` em `web/` abre `/` e redireciona para o primeiro evento, Grupo 1.
- [ ] As quatro abas funcionam; cada uma mostra seus clusters na ordem por tamanho com as cores
      da paleta e a numeração "Grupo g" igual à das figuras da fase 1.
- [ ] O mini-mapa da invasão (33 mil pontos) renderiza em < 2 s, destaca o cluster selecionado,
      mostra os rótulos nos centróides e seleciona ao clicar em um nó.
- [ ] A lista mostra K cards (100 ou 20) na ordem do ranking; slots não devolvidos aparecem como
      cards fantasma no lugar certo, com o motivo.
- [ ] Um card hidratado exibe autor (ou fallback com motivo), texto com hashtags/menções/links
      clicáveis e offsets corretos em textos com emoji, chip de mídia quando há `media_key`,
      métricas abreviadas em pt-BR, data em horário de Brasília, link para o X.
- [ ] A faixa de pesquisa mostra posição, RTs de membros, pureza, grafo, evento, razão API e
      "também em" com os valores do JSON; tooltips com o glossário.
- [ ] Ordenar por cada opção, filtrar por status e exclusividade, e buscar (sem acento/caixa)
      funcionam e o contador reflete o resultado.
- [ ] A URL `/eleicoes/3` abre o cluster c3 de eleicoes diretamente.
- [ ] `vitest` passa para `entities.ts` e `format.ts`.
- [ ] `npm run build` gera `dist/` sem erros de tipo.
- [ ] `web/README.md` explica: rodar, de onde vêm os dados, como atualizar (célula M10), e o
      que está fora de escopo.

## 10. Testes

Mínimo, no espírito YAGNI do projeto:

- `entities.test.ts`: (a) hashtag + menção + url em texto ASCII; (b) texto com emoji antes de
  uma hashtag — offsets em code points; (c) url com `media_key` vira `media` e é removida do
  fim do texto; (d) entidades sobrepostas — mantém a primeira; (e) sem entidades → um segmento.
- `format.test.ts`: `formatCompact(28348) === "28,3 mil"`, `formatCompact(null) === "—"`,
  `normalize("Ação") === "acao"`, `formatPct(0.4423) === "44%"`.

Resto é verificação manual pela lista da §9.

## 11. Plano de implementação em uma sessão

Ordem pensada para ter algo visível cedo e deixar o mais arriscado (Sigma) com o básico já
funcionando. Tempos são estimativas.

| # | Passo | Resultado verificável | ~min |
|---|---|---|---|
| 0 | Pré-voo: `ls data/export/index.json`, `node -v` (25.x), ler §5 e §7 | — | 10 |
| 1 | Scaffold: Vite react-ts em `web/`, Tailwind, router, `publicDir`, `types.ts` copiado de §5 | página em branco com título; `fetch("/index.json")` no console | 30 |
| 2 | `loadIndex` + `EventTabs` + redirecionamento de `/` | abas trocam a URL | 30 |
| 3 | `loadEvent` + `ClusterPanel` + seleção via URL | painel lista clusters, clique navega | 45 |
| 4 | `TweetCard` (texto plano) + `GhostCard` + `ResearchStrip` + `format.ts` | 100 cards do cluster, fantasmas no lugar | 90 |
| 5 | `entities.ts` + `TweetText` + testes Vitest | links clicáveis; testes verdes | 45 |
| 6 | `MiniMap` (Sigma nós-apenas, reducer, rótulos, clique) | mapa destaca e seleciona | 90 |
| 7 | `Toolbar`: ordenar, filtros, busca, contador | RF9 completo | 45 |
| 8 | Polimento: avatar fallback, estados de erro/carregando, largura mínima, `README.md` | lista da §9 | 45 |
| 9 | `npm run build`; commit | — | 10 |

Se o tempo apertar, a ordem de corte é: 7 (toolbar) → rótulos do mini-mapa → tooltips. O
mini-mapa em si e os cards com a faixa de pesquisa **não** são cortáveis: são o objetivo.

## 12. Riscos e notas

- **Offsets em code points.** Erro clássico: usar `text.slice(start, end)`. Textos com emoji
  quebram. Sempre `Array.from`.
- **Orientação do mini-mapa.** Sigma usa y para cima; matplotlib também, mas a figura da fase 1
  pode ter sido gerada com eixos invertidos por padrão. Comparar com
  `data/processed/<evento>/grafo-*-drl.png` e inverter `y` se preciso. Layout é apresentação;
  não afeta dados.
- **Avatares.** `profile_image_url` aponta para `pbs.twimg.com`; pode falhar (conta suspensa,
  CORS não é problema para `<img>`). Fallback obrigatório.
- **Cluster com `n_selected < k`.** Possível em clusters pequenos; o cabeçalho usa `n_selected`.
- **Mesmo tweet em vários clusters.** É esperado (333 pares em 2026-09-15). `also_in` existe
  para isso; não deduplicar na lista.
- **`purity` nulo** só se `rt_graph = 0`, o que não ocorre na seleção atual; tratar mesmo assim.
- **Não computar no front.** Se faltar um número, ele entra no export (`modules/export.py` +
  teste), não em JavaScript.

## 13. Referências

- `docs/visao-projeto.md` (stack fixada, entregável 3) · `docs/especificacao-tecnica.md` §5
  (visualização) e §3 (seleção/hidratação) · `docs/decisoes-metodologicas.md` D6, D9, D15.
- `modules/export.py` (contrato, fonte da verdade) · `modules/layout.py` (`PALETTE`, numeração
  "Grupo k", parâmetros do DRL) · `modules/select_tweets.py` (semântica de rt_cluster/rt_graph/rt_event).
- `assets/grafo-comunidades-drl-anotado.png` (referência visual do mini-mapa).
- `notebooks/pipeline_tcc2.ipynb` (gera `data/export/`).
