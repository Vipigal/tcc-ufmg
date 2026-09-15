# Leitor de clusters (web/) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir em `web/` o leitor de clusters (fase 2): app React estático que lê `data/export/` e mostra, por evento e cluster, o mini-mapa DRL e os top-K tweets em cards estilo X com a faixa de metadados da pesquisa.

**Architecture:** SPA Vite + React + TypeScript sem backend; `publicDir` aponta para `../data/export`, então o front só faz `fetch` de JSON estático. Estado de navegação (evento, cluster) vive na URL `/:evento/:community`; ordenação/filtros/busca vivem em estado local. Três utilitários puros e testados (`format.ts`, `entities.ts`, `filter.ts`) sustentam componentes de apresentação sem lógica de pesquisa — o app não computa nada: se um número aparece na tela, ele veio do JSON.

**Tech Stack:** Vite 8, React 19, TypeScript 6, Tailwind CSS 4 (`@tailwindcss/vite`), Sigma.js 3 + graphology (mini-mapa, nós apenas), react-router-dom 7, lucide-react, Vitest 5.

**Spec:** `docs/superpowers/specs/2026-09-15-leitor-de-clusters-design.md` (D15 em `docs/decisoes-metodologicas.md`).

## Global Constraints

- **Sem backend, sem estado global** (spec §4.2, §6.3): só `fetch` de `data/export/`; nenhum Redux/Zustand; cache em memória por slug.
- **Não computar no front** (spec §4.2 "Reprodutibilidade", §12): pureza, grupo, atrição, razões etc. vêm prontos do export. A única aritmética permitida é a razão `retweet_count / rt_event` (spec §7.6 pede exatamente isso) e formatação.
- **Português em toda a interface; números e datas em pt-BR; fuso `America/Sao_Paulo`** (spec §4.2, §7.8).
- **Sem rótulo nem juízo ideológico** (CLAUDE.md, spec §1): comunidades são "Grupo g (c<community>)", cores da paleta do export, tooltips dizem só o que o número é.
- **Offsets de entidades em code points** (spec §5.3, §12): sempre `Array.from(text)`, nunca `text.slice`.
- **Imitar o X sem marca registrada** (spec decisão 6): ícones genéricos (lucide), sem logotipo/assets.
- **Mini-mapa: Sigma nós-apenas, nenhuma aresta**; mesmas cores e numeração da fase 1; y **não** se inverte (verificado: `data/processed/invasao-3-poderes/grafo-invasao-drl.png` tem Grupo 1 — centróide y≈−108 — embaixo e Grupo 2 — y≈146 — em cima; o espaço `graph` do Sigma também tem y para cima).
- **Stack fixada**: React + Sigma.js + Tailwind (`docs/visao-projeto.md`). Nada de UI kit.
- **TypeScript com `erasableSyntaxOnly`, `verbatimModuleSyntax`, `noUnusedLocals`, `noUnusedParameters`** (template atual do Vite): sem `enum`, sem parameter properties, `import type` para tipos.
- **Tipos do contrato em um único arquivo** `web/src/types.ts` (spec §4.2).
- **Política de commits (herdada de `docs/superpowers/plans/2026-05-23-pipeline-modulos-1-6.md`):** o agente **não** commita; o autor revisa e commita. Os passos "Commit" abaixo indicam a granularidade pretendida e ficam marcados como pulados.
- **Versões**: usar as estáveis correntes (2026-09-15: vite 8.3, react 19.3, typescript ~6.0 — a 7.x é o compilador nativo e o template oficial do Vite ainda fixa ~6.0.2 —, tailwindcss 4.3, sigma 3.0.3, graphology 0.26, react-router-dom 7.18, lucide-react 1.46, vitest 5.0). Confirmadas na documentação via context7: `new Sigma(graph, container, settings)`, `nodeReducer`, `refresh({skipIndexation})`, `on("clickNode")`, `on("afterRender")`, `graphToViewport`, `getCamera().animatedReset({duration})`, `kill()`; Tailwind v4 = plugin `@tailwindcss/vite` + `@import "tailwindcss"`.

## Pré-voo (verificado em 2026-09-15)

- `data/export/` existe, é versionado, e bate com o contrato §5: 4 eventos, 1.340 slots (1.022 hidratados, 255 `not_found`, 63 `not_authorized`, 0 `error`, 0 `pending`), 0 slots hidratados com `author == null`, 0 `purity` nulo, 426 slots com `media_key`, 33 com `referenced_tweets`, 0 `possibly_sensitive`. Todo caminho de RF7/RF8 ainda deve ser implementado — o JSON pode mudar quando o export for re-executado.
- `layout.json`: `n_plotted` = `x.length` (33.303 na invasão), `centroids` inclui comunidades < 1% (o front só rotula as que têm `ClusterMeta`), `groups` cobre todas.
- `Intl` pt-BR no Node 25: `compact(28348)` = `"28,3 mil"` (NBSP — `formatCompact` troca por espaço normal para bater com o spec §10); `dateStyle medium + timeStyle short` = `"8 de jan. de 2023, 15:54"`.
- Node v25.2.1, npm 11.7.0. `web/` não existe.

## Estrutura de arquivos

```
web/
├── .gitignore                    # node_modules, dist, *.local, .tsbuildinfo
├── README.md                     # Task 10
├── index.html
├── package.json
├── tsconfig.json · tsconfig.app.json · tsconfig.node.json
├── vercel.json                   # rewrite SPA (Task 10)
├── vite.config.ts                # react + tailwind; publicDir ../data/export; vitest
└── src/
    ├── main.tsx                  # router: "/" → RootRedirect · "/:evento/:community?" → App
    ├── App.tsx                   # App (resolve params, redireciona) · Reader (dados + layout) · RootRedirect
    ├── types.ts                  # §5 do spec, literalmente + EventData
    ├── styles.css                # @import tailwindcss; @theme; .chip .badge .select .label-halo
    ├── data/
    │   ├── fetchJson.ts          # fetch + ExportNotFoundError (detecta fallback HTML do Vite)
    │   ├── loadIndex.ts          # cache de index.json
    │   ├── loadEvent.ts          # cache por slug de tweets.json + layout.json
    │   └── hooks.ts              # useIndex, useEvent (AsyncState)
    ├── lib/
    │   ├── format.ts             # formatCompact, formatInt, formatDec, formatPct, formatDate, formatDay, normalize — TESTADO
    │   ├── entities.ts           # segmentText, hasMedia — TESTADO
    │   ├── filter.ts             # ToolbarState, applyToolbar, sortSlots — TESTADO
    │   ├── glossary.ts           # textos: tooltips §7.6, status RF7/RF8, nomes curtos dos eventos
    │   ├── color.ts              # withAlpha(hex, alpha)
    │   ├── paths.ts              # clusterPath, eventDefaultPath, indexDefaultPath
    │   └── useDebounce.ts
    └── components/
        ├── States.tsx            # Skeleton, ErrorBox
        ├── EventTabs.tsx
        ├── ClusterPanel.tsx
        ├── MiniMap.tsx
        ├── Toolbar.tsx
        ├── CardList.tsx          # cabeçalho da lista + Toolbar + cards
        ├── TweetCard.tsx
        ├── GhostCard.tsx
        ├── ResearchStrip.tsx
        ├── Avatar.tsx
        └── TweetText.tsx
```

Ordem das tasks: utilitários puros primeiro (TDD, sem UI), depois dados/rota, painel, cards, mini-mapa, toolbar, polimento. Segue a prioridade do spec §11: mini-mapa e cards com faixa de pesquisa não são cortáveis; toolbar é o primeiro corte.

---

### Task 1: Scaffold do app (Vite + React + TS + Tailwind) e `types.ts`

**Files:**
- Create: `web/package.json`, `web/.gitignore`, `web/tsconfig.json`, `web/tsconfig.app.json`, `web/tsconfig.node.json`, `web/vite.config.ts`, `web/index.html`
- Create: `web/src/main.tsx`, `web/src/App.tsx` (placeholder), `web/src/styles.css`, `web/src/types.ts`

**Interfaces:**
- Produces: todos os tipos de `types.ts` (`Index`, `EventMeta`, `ClusterMeta`, `Slot`, `SlotStatus`, `AuthorStatus`, `Tweet`, `Author`, `Layout`, `EventData`); classes Tailwind customizadas `text-ink`, `text-muted`, `border-line`, `text-x-blue`, `.chip`, `.badge`, `.select`, `.label-halo`.

- [x] **Step 1: Criar `web/.gitignore` antes de instalar qualquer coisa**

```gitignore
node_modules
dist
*.local
*.tsbuildinfo
npm-debug.log*
```

- [x] **Step 2: Criar `web/package.json`**

```json
{
  "name": "leitor-de-clusters",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

- [x] **Step 3: Instalar dependências (registra as versões correntes)**

Run (em `web/`):
```bash
npm install react react-dom react-router-dom sigma graphology graphology-types lucide-react
npm install -D vite @vitejs/plugin-react typescript@~6.0.2 @types/react @types/react-dom @types/node tailwindcss @tailwindcss/vite vitest
```
Expected: `package.json` ganha `dependencies` e `devDependencies` com `^` nas versões correntes; sem `ERESOLVE`.

- [x] **Step 4: Criar os três `tsconfig` (cópia do template `create-vite react-ts` corrente, mais `strict` explícito)**

`web/tsconfig.json`:
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

`web/tsconfig.app.json`:
```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "esnext",
    "types": ["vite/client"],
    "allowArbitraryExtensions": true,
    "skipLibCheck": true,
    "strict": true,

    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

`web/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023"],
    "types": ["node"],
    "skipLibCheck": true,
    "strict": true,

    "module": "nodenext",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

- [x] **Step 5: Criar `web/vite.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // data/export/ é servido na raiz: fetch("/index.json"), fetch("/eleicoes/tweets.json")
  publicDir: "../data/export",
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
```

- [x] **Step 6: Criar `web/index.html`**

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Leitor de clusters</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [x] **Step 7: Criar `web/src/styles.css`**

```css
@import "tailwindcss";

@theme {
  /* paleta neutra do card (referência: X), sem assets de marca */
  --color-ink: #0f1419;
  --color-muted: #536471;
  --color-line: #eff3f4;
  --color-x-blue: #1d9bf0;
}

html,
body,
#root {
  height: 100%;
}

body {
  margin: 0;
  background: #fff;
  color: var(--color-ink);
  -webkit-font-smoothing: antialiased;
}

@layer components {
  .chip {
    @apply inline-flex items-center gap-1 rounded-full border border-line bg-gray-50 px-2.5 py-1 text-[13px] text-ink hover:bg-gray-100;
  }
  .badge {
    @apply inline-flex items-center gap-1 rounded border border-line px-1.5 py-0.5 text-[11px] uppercase tracking-wide text-muted;
  }
  .select {
    @apply rounded-md border border-gray-300 bg-white px-2 py-1 text-[13px] text-ink;
  }
  /* rótulo do mini-mapa: halo branco como na figura da fase 1 */
  .label-halo {
    text-shadow:
      0 0 3px #fff,
      0 0 3px #fff,
      0 0 4px #fff,
      0 0 4px #fff;
  }
}
```

- [x] **Step 8: Criar `web/src/main.tsx` e `web/src/App.tsx` placeholder**

`web/src/main.tsx` (versão provisória; a Task 5 troca por router):
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

`web/src/App.tsx` (placeholder):
```tsx
export default function App() {
  return <h1 className="p-4 text-[17px] font-bold">Leitor de clusters</h1>;
}
```

- [x] **Step 9: Criar `web/src/types.ts` — §5 do spec, literalmente**

```ts
/**
 * Contrato de `data/export/` (spec §5). Fonte da verdade: `modules/export.py` (WebExporter, M10).
 * O front não deriva nada daqui — só exibe.
 */

export interface Index {
  generated_at: string; // ISO-8601 UTC — único carimbo de tempo do export
  palette: string[]; // 10 cores hex; cor do Grupo g = palette[(g-1) % palette.length]
  events: EventMeta[]; // na ordem da pipeline (mobilizacao, roberto, eleicoes, invasao)
}

export interface EventMeta {
  slug: string; // = nome da pasta; usado na URL
  name: string; // "Ataques de 8 de janeiro de 2023"
  event_date: string | null; // "2023-01-08"
  n_nodes: number; // nós do grafo (usuários)
  n_edges: number; // arestas do backbone
  n_communities: number; // comunidades Leiden, incluindo as < 1%
  run_config: Record<string, unknown>; // parâmetros da fase 1 (N, τ, resolução…)
  selection: { k: number; k_small: number; min_frac: number; small_weight_frac: number };
  clusters: ClusterMeta[]; // só os selecionados (≥ min_frac), ordenados por group
  files: { tweets: string; layout: string }; // caminhos relativos a data/export/
}

export interface ClusterMeta {
  community: number; // id Leiden (estável nos dados; usar na URL)
  group: number; // 1..n por tamanho (numeração das figuras da fase 1)
  label: string; // "Grupo 1"
  color: string; // hex, da paleta
  n_nodes: number;
  frac_nodes: number; // 0–1
  intra_weight_frac: number; // peso interno / peso total do grafo (0–1); ≤ 0.05 ⇒ k = k_small
  k: number; // 100 ou 20
  n_selected: number; // = k, salvo cluster com menos candidatos
  n_hydrated: number;
  n_not_found: number;
  n_not_authorized: number;
  n_other_errors: number;
  n_pending: number;
  attrition: number; // (n_selected − n_hydrated) / n_selected
}

export type SlotStatus = "hydrated" | "not_found" | "not_authorized" | "error" | "pending";
export type AuthorStatus = "hydrated" | "not_found" | "not_authorized" | "error" | "pending" | null;

export interface Slot {
  community: number;
  group: number;
  rank: number;
  k: number;
  tweet_id: string;
  rt_cluster: number; // membros do cluster que retuitaram (critério do ranking)
  rt_graph: number; // nós do grafo (qualquer cluster) que retuitaram
  rt_event: number; // usuários do evento, inclusive periferia filtrada
  purity: number | null; // rt_cluster / rt_graph, 4 casas
  also_in: { community: number; group: number; rank: number }[]; // outros clusters do MESMO evento
  status: SlotStatus;
  error: { title: string; detail: string } | null; // só quando status ∉ {hydrated, pending}
  tweet: Tweet | null; // null se não hidratado
  author_id: string | null; // null se não hidratado
  author: Author | null; // null se autor não hidratado/negado
  author_status: AuthorStatus; // null quando o tweet não foi hidratado
}

export interface TweetUrlEntity {
  start: number;
  end: number;
  url: string;
  expanded_url?: string;
  display_url?: string;
  media_key?: string;
}

export interface TweetEntities {
  urls: TweetUrlEntity[];
  hashtags: { start: number; end: number; tag: string }[];
  mentions: { start: number; end: number; username: string; id?: string }[];
}

export type ReferencedTweetType = "quoted" | "replied_to" | "retweeted";

export interface Tweet {
  id: string;
  text: string;
  created_at: string;
  lang: string | null;
  source: string | null;
  possibly_sensitive: boolean | null;
  reply_settings: string | null;
  conversation_id: string | null;
  in_reply_to_user_id: string | null;
  metrics: {
    retweet_count: number | null;
    reply_count: number | null;
    like_count: number | null;
    quote_count: number | null;
    bookmark_count: number | null;
    impression_count: number | null;
  };
  entities: TweetEntities; // offsets em code points Unicode (Array.from), não UTF-16
  referenced_tweets: { type: ReferencedTweetType; id: string }[];
  url: string; // https://x.com/i/web/status/<id>
}

export interface Author {
  id: string;
  username: string | null;
  name: string | null;
  description: string | null;
  location: string | null;
  url: string | null;
  profile_image_url: string | null;
  protected: boolean | null;
  verified: boolean | null;
  verified_type: string | null; // "blue" | "business" | "government" | "none"
  created_at: string | null;
  metrics: {
    followers_count: number | null;
    following_count: number | null;
    tweet_count: number | null;
    listed_count: number | null;
  };
}

export interface Layout {
  n_nodes: number; // nós do grafo
  n_plotted: number; // nós da componente gigante (= x.length)
  top_k: number;
  seed: number; // parâmetros do DRL (reprodutibilidade)
  x: number[];
  y: number[]; // coordenadas (2 casas), mesma ordem que `community`
  community: number[]; // comunidade de cada nó plotado
  centroids: Record<string, [number, number]>; // mediana (x, y) por comunidade — onde pôr o rótulo
  groups: Record<string, number>; // community → group (todas as comunidades, inclusive < 1%)
}

/** Tudo que o front carrega para um evento (tweets.json + layout.json), em memória por slug. */
export interface EventData {
  meta: EventMeta;
  slots: Slot[];
  layout: Layout;
}
```

- [x] **Step 10: Verificar tipos e servir os dados**

Run (em `web/`): `npx tsc -b`
Expected: sem saída (sem erros).

Run (em `web/`): `npm run dev -- --port 5173 &` e em seguida `curl -s -o /dev/null -w "%{http_code} %{content_type}\n" http://localhost:5173/index.json` e `curl -s http://localhost:5173/invasao-3-poderes/event.json | head -c 120`; depois matar o servidor.
Expected: `200 application/json`; os primeiros bytes do `event.json` (`{"slug": "invasao-3-poderes"…`).

- [x] **Step 11: Confirmar os nomes dos ícones lucide usados no plano**

Run (em `web/`):
```bash
node --input-type=module -e "import * as L from 'lucide-react'; const need=['BadgeCheck','Bookmark','ExternalLink','Eye','Heart','Image','LocateFixed','MessageCircle','Quote','Repeat2','Search','TriangleAlert','UserRound','X']; console.log(need.filter(n=>!(n in L)))"
```
Expected: `[]`. Se algum nome faltar, trocar pelo nome atual (ex.: `AlertTriangle` → `TriangleAlert`) em todos os componentes que o usam.

- [ ] **Step 12: Commit** — *pulado (política do repo: o autor commita)*. Granularidade pretendida: `feat(web): scaffold Vite+React+Tailwind e tipos do contrato de export`.

---

### Task 2: `lib/format.ts` (TDD)

**Files:**
- Create: `web/src/lib/format.ts`
- Test: `web/src/lib/format.test.ts`

**Interfaces:**
- Produces:
  - `formatCompact(n: number | null | undefined): string` — "28,3 mil", "1,2 mi"; `null` → "—"
  - `formatInt(n: number | null | undefined): string` — "3.389"; `null` → "—"
  - `formatDec(x: number | null | undefined, digits: number): string` — "0,75"; `null` → "—"
  - `formatPct(x: number | null | undefined, digits = 0): string` — 0.4423 → "44%", (0.358, 1) → "35,8%"
  - `formatDate(iso: string): string` — "8 de jan. de 2023, 15:54" (Brasília)
  - `formatDay(isoDate: string): string` — "2023-01-08" → "8 de janeiro de 2023"
  - `normalize(s: string): string` — sem acento, minúsculas

- [x] **Step 1: Escrever os testes**

`web/src/lib/format.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { formatCompact, formatDate, formatDay, formatDec, formatInt, formatPct, normalize } from "./format";

describe("formatCompact", () => {
  it("abrevia em pt-BR com uma casa", () => {
    expect(formatCompact(28348)).toBe("28,3 mil");
    expect(formatCompact(1_200_000)).toBe("1,2 mi");
    expect(formatCompact(890)).toBe("890");
  });
  it("devolve travessão para null/undefined", () => {
    expect(formatCompact(null)).toBe("—");
    expect(formatCompact(undefined)).toBe("—");
  });
});

describe("formatInt", () => {
  it("usa ponto de milhar", () => {
    expect(formatInt(3389)).toBe("3.389");
    expect(formatInt(12_023_243)).toBe("12.023.243");
  });
  it("devolve travessão para null", () => {
    expect(formatInt(null)).toBe("—");
  });
});

describe("formatDec / formatPct", () => {
  it("formatDec usa vírgula decimal e casas fixas", () => {
    expect(formatDec(0.7538, 2)).toBe("0,75");
    expect(formatDec(1.00229, 1)).toBe("1,0");
    expect(formatDec(null, 2)).toBe("—");
  });
  it("formatPct multiplica por 100", () => {
    expect(formatPct(0.4423)).toBe("44%");
    expect(formatPct(0.358, 1)).toBe("35,8%");
    expect(formatPct(null)).toBe("—");
  });
});

describe("datas", () => {
  it("formatDate em horário de Brasília", () => {
    expect(formatDate("2023-01-08T18:54:38.000Z")).toBe("8 de jan. de 2023, 15:54");
  });
  it("formatDay não desloca o dia pelo fuso", () => {
    expect(formatDay("2023-01-08")).toBe("8 de janeiro de 2023");
    expect(formatDay("2022-09-07")).toBe("7 de setembro de 2022");
  });
});

describe("normalize", () => {
  it("remove acentos e caixa", () => {
    expect(normalize("Ação")).toBe("acao");
    expect(normalize("BRASÍLIA")).toBe("brasilia");
    expect(normalize("já")).toBe("ja");
  });
});
```

- [x] **Step 2: Rodar e ver falhar**

Run (em `web/`): `npx vitest run src/lib/format.test.ts`
Expected: FAIL — `Failed to resolve import "./format"`.

- [x] **Step 3: Implementar `web/src/lib/format.ts`**

```ts
/** Formatação pt-BR (spec §7.8). Tudo aqui é apresentação; nada é cálculo de pesquisa. */

const EMPTY = "—";

const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat("pt-BR");
const dateTime = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Sao_Paulo",
});
const day = new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" });
const decimals = new Map<number, Intl.NumberFormat>();

function decimalFormatter(digits: number): Intl.NumberFormat {
  let f = decimals.get(digits);
  if (!f) {
    f = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    decimals.set(digits, f);
  }
  return f;
}

/** 28348 → "28,3 mil"; 1200000 → "1,2 mi"; null → "—". Troca o NBSP do Intl por espaço normal. */
export function formatCompact(n: number | null | undefined): string {
  return n == null ? EMPTY : compact.format(n).replace(/ /g, " ");
}

/** 3389 → "3.389"; null → "—". */
export function formatInt(n: number | null | undefined): string {
  return n == null ? EMPTY : integer.format(n);
}

/** 0.7538, 2 → "0,75"; null → "—". */
export function formatDec(x: number | null | undefined, digits: number): string {
  return x == null ? EMPTY : decimalFormatter(digits).format(x);
}

/** 0.4423 → "44%"; (0.358, 1) → "35,8%"; null → "—". */
export function formatPct(x: number | null | undefined, digits = 0): string {
  return x == null ? EMPTY : `${formatDec(x * 100, digits)}%`;
}

/** ISO-8601 → "8 de jan. de 2023, 15:54" (fuso de Brasília). */
export function formatDate(iso: string): string {
  return dateTime.format(new Date(iso));
}

/** "2023-01-08" → "8 de janeiro de 2023" (interpreta a data como UTC para não deslocar o dia). */
export function formatDay(isoDate: string): string {
  return day.format(new Date(`${isoDate}T00:00:00Z`));
}

/** Busca sem acento e sem caixa: NFD + remoção de marcas combinantes. */
export function normalize(s: string): string {
  return s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}
```

- [x] **Step 4: Rodar e ver passar**

Run (em `web/`): `npx vitest run src/lib/format.test.ts`
Expected: PASS, 9 testes.

- [ ] **Step 5: Commit** — *pulado*. `feat(web): utilitários de formatação pt-BR`.

---

### Task 3: `lib/entities.ts` (TDD) — texto → segmentos em code points

**Files:**
- Create: `web/src/lib/entities.ts`
- Test: `web/src/lib/entities.test.ts`

**Interfaces:**
- Consumes: `Tweet`, `TweetEntities` de `types.ts`.
- Produces:
  - `type SegmentKind = "text" | "hashtag" | "mention" | "url" | "media"`
  - `interface Segment { kind: SegmentKind; text: string; href?: string }`
  - `segmentText(text: string, entities: TweetEntities, tweetUrl: string): Segment[]`
  - `hasMedia(entities: TweetEntities): boolean`

- [x] **Step 1: Escrever os testes (casos a–e do spec §10 + colapso de mídia)**

`web/src/lib/entities.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import type { TweetEntities } from "../types";
import { hasMedia, segmentText } from "./entities";

const TWEET_URL = "https://x.com/i/web/status/1";
const none: TweetEntities = { urls: [], hashtags: [], mentions: [] };

describe("segmentText", () => {
  it("(a) hashtag + menção + url em texto ASCII", () => {
    //            0123456789012345678901234567890123456
    const text = "Oi @ana veja #stf em https://t.co/abc";
    const entities: TweetEntities = {
      mentions: [{ start: 3, end: 7, username: "ana" }],
      hashtags: [{ start: 13, end: 17, tag: "stf" }],
      urls: [
        {
          start: 21,
          end: 37,
          url: "https://t.co/abc",
          expanded_url: "https://example.com/x",
          display_url: "example.com/x",
        },
      ],
    };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([
      { kind: "text", text: "Oi " },
      { kind: "mention", text: "@ana", href: "https://x.com/ana" },
      { kind: "text", text: " veja " },
      { kind: "hashtag", text: "#stf", href: "https://x.com/hashtag/stf" },
      { kind: "text", text: " em " },
      { kind: "url", text: "example.com/x", href: "https://example.com/x" },
    ]);
  });

  it("(b) offsets são em code points: emoji antes da hashtag", () => {
    const text = "🚨 #STF"; // 🚨 = 1 code point, 2 unidades UTF-16
    const entities: TweetEntities = { ...none, hashtags: [{ start: 2, end: 6, tag: "STF" }] };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([
      { kind: "text", text: "🚨 " },
      { kind: "hashtag", text: "#STF", href: "https://x.com/hashtag/STF" },
    ]);
  });

  it("(c) url com media_key vira mídia, sai do fim do texto e hasMedia é true", () => {
    const text = "Cavalo socorrido https://t.co/m1";
    const entities: TweetEntities = {
      ...none,
      urls: [
        {
          start: 17,
          end: 32,
          url: "https://t.co/m1",
          expanded_url: "https://x.com/u/status/1/photo/1",
          display_url: "pic.x.com/m1",
          media_key: "3_1",
        },
      ],
    };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([{ kind: "text", text: "Cavalo socorrido" }]);
    expect(hasMedia(entities)).toBe(true);
    expect(hasMedia(none)).toBe(false);
  });

  it("(d) entidades sobrepostas: mantém a primeira", () => {
    const text = "#abcd ef";
    const entities: TweetEntities = {
      ...none,
      hashtags: [{ start: 0, end: 5, tag: "abcd" }],
      mentions: [{ start: 2, end: 6, username: "cdef" }],
    };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([
      { kind: "hashtag", text: "#abcd", href: "https://x.com/hashtag/abcd" },
      { kind: "text", text: " ef" },
    ]);
  });

  it("(e) sem entidades → um segmento de texto", () => {
    expect(segmentText("Só texto", none, TWEET_URL)).toEqual([{ kind: "text", text: "Só texto" }]);
  });

  it("várias mídias no meio do texto colapsam em um chip; mídia no fim é removida", () => {
    //            0123456789012345678901234567890123
    const text = "a https://t.co/1 https://t.co/2 b https://t.co/3";
    const media = (start: number, end: number, k: string) => ({
      start,
      end,
      url: `https://t.co/${k}`,
      media_key: `3_${k}`,
    });
    const entities: TweetEntities = { ...none, urls: [media(2, 16, "1"), media(17, 31, "2"), media(34, 48, "3")] };
    const out = segmentText(text, entities, TWEET_URL);
    expect(out.filter((s) => s.kind === "media")).toHaveLength(1);
    expect(out[0]).toEqual({ kind: "text", text: "a " });
    expect(out[1]).toEqual({ kind: "media", text: "Mídia", href: TWEET_URL });
    expect(out[out.length - 1]).toEqual({ kind: "text", text: " b" });
  });

  it("descarta entidade com offset fora do texto", () => {
    const entities: TweetEntities = { ...none, hashtags: [{ start: 10, end: 14, tag: "x" }] };
    expect(segmentText("curto", entities, TWEET_URL)).toEqual([{ kind: "text", text: "curto" }]);
  });
});
```

- [x] **Step 2: Rodar e ver falhar**

Run (em `web/`): `npx vitest run src/lib/entities.test.ts`
Expected: FAIL — `Failed to resolve import "./entities"`.

- [x] **Step 3: Implementar `web/src/lib/entities.ts`**

```ts
import type { TweetEntities } from "../types";

/**
 * Texto do tweet → segmentos renderizáveis (spec §7.5).
 * Offsets da API do X são em code points Unicode: fatiar sempre `Array.from(text)`, nunca `text.slice`.
 */

export type SegmentKind = "text" | "hashtag" | "mention" | "url" | "media";

export interface Segment {
  kind: SegmentKind;
  text: string;
  href?: string;
}

interface Span {
  start: number;
  end: number;
  kind: Exclude<SegmentKind, "text">;
  text: string;
  href: string;
}

/** Há pelo menos uma url com `media_key` (foto/vídeo/gif sem objeto de mídia hidratado). */
export function hasMedia(entities: TweetEntities): boolean {
  return entities.urls.some((u) => Boolean(u.media_key));
}

export function segmentText(text: string, entities: TweetEntities, tweetUrl: string): Segment[] {
  const cps = Array.from(text);

  // 1. coletar entidades como spans
  const spans: Span[] = [];
  for (const h of entities.hashtags) {
    spans.push({ start: h.start, end: h.end, kind: "hashtag", text: `#${h.tag}`, href: `https://x.com/hashtag/${h.tag}` });
  }
  for (const m of entities.mentions) {
    spans.push({ start: m.start, end: m.end, kind: "mention", text: `@${m.username}`, href: `https://x.com/${m.username}` });
  }
  for (const u of entities.urls) {
    if (u.media_key) {
      spans.push({ start: u.start, end: u.end, kind: "media", text: "Mídia", href: tweetUrl });
    } else {
      spans.push({ start: u.start, end: u.end, kind: "url", text: u.display_url ?? u.url, href: u.expanded_url ?? u.url });
    }
  }

  // 2. ordenar por início; descartar sobreposições (mantém a primeira) e offsets inválidos
  spans.sort((a, b) => a.start - b.start || a.end - b.end);
  const kept: Span[] = [];
  let cursor = 0;
  for (const s of spans) {
    if (s.start < cursor || s.start < 0 || s.end > cps.length || s.end <= s.start) continue;
    kept.push(s);
    cursor = s.end;
  }

  // 3. varrer emitindo texto entre entidades e as entidades
  const out: Segment[] = [];
  let pos = 0;
  for (const s of kept) {
    if (s.start > pos) out.push({ kind: "text", text: cps.slice(pos, s.start).join("") });
    out.push({ kind: s.kind, text: s.text, href: s.href });
    pos = s.end;
  }
  if (pos < cps.length) out.push({ kind: "text", text: cps.slice(pos).join("") });

  return mergeText(collapseMedia(out));
}

/** Mídia no fim não vira texto (o chip fica na linha de anexos); várias mídias no meio → um chip. */
function collapseMedia(segments: Segment[]): Segment[] {
  const out = [...segments];
  let dropped = false;
  while (out.length > 0) {
    const last = out[out.length - 1];
    if (last.kind === "media") {
      out.pop();
      dropped = true;
      continue;
    }
    if (dropped && last.kind === "text" && last.text.trim() === "") {
      out.pop();
      continue;
    }
    break;
  }
  if (dropped && out.length > 0) {
    const last = out[out.length - 1];
    if (last.kind === "text") out[out.length - 1] = { ...last, text: last.text.replace(/\s+$/u, "") };
  }
  // várias mídias → um chip; o espaço que separava as repetidas sai junto
  const result: Segment[] = [];
  let seen = false;
  for (const s of out) {
    if (s.kind === "media") {
      if (seen) {
        const prev = result[result.length - 1];
        if (prev && prev.kind === "text" && prev.text.trim() === "") result.pop();
        continue;
      }
      seen = true;
    }
    result.push(s);
  }
  return result;
}

/** Junta segmentos de texto adjacentes (sobram depois do colapso de mídia). */
function mergeText(segments: Segment[]): Segment[] {
  const out: Segment[] = [];
  for (const s of segments) {
    const prev = out[out.length - 1];
    if (prev && prev.kind === "text" && s.kind === "text") out[out.length - 1] = { kind: "text", text: prev.text + s.text };
    else out.push(s);
  }
  return out;
}
```

- [x] **Step 4: Rodar e ver passar**

Run (em `web/`): `npx vitest run src/lib/entities.test.ts`
Expected: PASS, 7 testes.

- [ ] **Step 5: Commit** — *pulado*. `feat(web): segmentação de texto por entidades em code points`.

---

### Task 4: `lib/filter.ts` (TDD) — ordenar, filtrar, buscar

**Files:**
- Create: `web/src/lib/filter.ts`
- Test: `web/src/lib/filter.test.ts`

**Interfaces:**
- Consumes: `Slot` de `types.ts`; `normalize` de `lib/format.ts`.
- Produces:
  - `type SortKey = "rank" | "purity" | "rt_graph" | "api_retweets" | "date"`
  - `type StatusFilter = "all" | "hydrated" | "ghost"`
  - `type ExclusivityFilter = "all" | "exclusive" | "shared"`
  - `interface ToolbarState { sort: SortKey; status: StatusFilter; exclusivity: ExclusivityFilter; query: string }`
  - `const DEFAULT_TOOLBAR: ToolbarState`
  - `const EXCLUSIVE_MIN_PURITY = 0.9`, `const SHARED_MAX_PURITY = 0.5`
  - `applyToolbar(slots: Slot[], state: ToolbarState): Slot[]` (novo array; não muta)
  - `sortSlots(slots: Slot[], sort: SortKey): Slot[]`

- [x] **Step 1: Escrever os testes**

`web/src/lib/filter.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import type { Slot, Tweet } from "../types";
import { DEFAULT_TOOLBAR, applyToolbar } from "./filter";

function tweet(over: Partial<Tweet> & { text: string; created_at: string; retweet_count?: number | null }): Tweet {
  return {
    id: "1",
    text: over.text,
    created_at: over.created_at,
    lang: "pt",
    source: null,
    possibly_sensitive: false,
    reply_settings: null,
    conversation_id: null,
    in_reply_to_user_id: null,
    metrics: {
      retweet_count: over.retweet_count ?? null,
      reply_count: null,
      like_count: null,
      quote_count: null,
      bookmark_count: null,
      impression_count: null,
    },
    entities: { urls: [], hashtags: [], mentions: [] },
    referenced_tweets: [],
    url: "https://x.com/i/web/status/1",
  };
}

function slot(over: Partial<Slot> & { rank: number }): Slot {
  return {
    community: 0,
    group: 1,
    k: 100,
    tweet_id: String(over.rank),
    rt_cluster: 10,
    rt_graph: 10,
    rt_event: 10,
    purity: 1,
    also_in: [],
    status: over.tweet ? "hydrated" : "not_found",
    error: null,
    tweet: null,
    author_id: null,
    author: null,
    author_status: over.tweet ? "hydrated" : null,
    ...over,
  };
}

const slots: Slot[] = [
  slot({ rank: 1, purity: 0.95, rt_graph: 500, tweet: tweet({ text: "Ação em Brasília", created_at: "2023-01-08T20:00:00Z", retweet_count: 100 }),
    author: { id: "a", username: "Ana_Flor", name: "Ana Flor", description: null, location: null, url: null, profile_image_url: null, protected: null, verified: null, verified_type: null, created_at: null, metrics: { followers_count: null, following_count: null, tweet_count: null, listed_count: null } } }),
  slot({ rank: 2, purity: 0.4, rt_graph: 900, tweet: tweet({ text: "Outro texto", created_at: "2023-01-08T18:00:00Z", retweet_count: null }) }),
  slot({ rank: 3, purity: 0.7, rt_graph: 700 }), // fantasma
];

describe("applyToolbar", () => {
  it("padrão: todos, na ordem do ranking", () => {
    expect(applyToolbar(slots, DEFAULT_TOOLBAR).map((s) => s.rank)).toEqual([1, 2, 3]);
  });
  it("ordena por pureza decrescente", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "purity" }).map((s) => s.rank)).toEqual([1, 3, 2]);
  });
  it("ordena por RTs no grafo decrescente", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "rt_graph" }).map((s) => s.rank)).toEqual([2, 3, 1]);
  });
  it("ordena por reposts na API com nulos (e fantasmas) por último", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "api_retweets" }).map((s) => s.rank)).toEqual([1, 2, 3]);
  });
  it("ordena por data crescente com fantasmas por último", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "date" }).map((s) => s.rank)).toEqual([2, 1, 3]);
  });
  it("filtra por status", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, status: "hydrated" }).map((s) => s.rank)).toEqual([1, 2]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, status: "ghost" }).map((s) => s.rank)).toEqual([3]);
  });
  it("filtra por exclusividade (pureza ≥ 0,90 / < 0,50)", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, exclusivity: "exclusive" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, exclusivity: "shared" }).map((s) => s.rank)).toEqual([2]);
  });
  it("busca sem acento nem caixa no texto, nome e @handle", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "brasilia" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "ana flor" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "ANA_FLOR" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "nada" })).toEqual([]);
  });
  it("não muta a entrada", () => {
    const before = slots.map((s) => s.rank);
    applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "rt_graph" });
    expect(slots.map((s) => s.rank)).toEqual(before);
  });
});
```

- [x] **Step 2: Rodar e ver falhar**

Run (em `web/`): `npx vitest run src/lib/filter.test.ts`
Expected: FAIL — `Failed to resolve import "./filter"`.

- [x] **Step 3: Implementar `web/src/lib/filter.ts`**

```ts
import type { Slot } from "../types";
import { normalize } from "./format";

/** Estado da barra de ferramentas (RF9). Vive fora da URL. */

export type SortKey = "rank" | "purity" | "rt_graph" | "api_retweets" | "date";
export type StatusFilter = "all" | "hydrated" | "ghost";
export type ExclusivityFilter = "all" | "exclusive" | "shared";

export interface ToolbarState {
  sort: SortKey;
  status: StatusFilter;
  exclusivity: ExclusivityFilter;
  query: string;
}

export const DEFAULT_TOOLBAR: ToolbarState = { sort: "rank", status: "all", exclusivity: "all", query: "" };

/** Limiares de leitura do spec §7.6/§7.7 — sinalização, não juízo. */
export const EXCLUSIVE_MIN_PURITY = 0.9;
export const SHARED_MAX_PURITY = 0.5;

export function applyToolbar(slots: Slot[], state: ToolbarState): Slot[] {
  const q = normalize(state.query.trim());
  const filtered = slots.filter((s) => {
    if (state.status === "hydrated" && s.status !== "hydrated") return false;
    if (state.status === "ghost" && s.status === "hydrated") return false;
    if (state.exclusivity === "exclusive" && !(s.purity != null && s.purity >= EXCLUSIVE_MIN_PURITY)) return false;
    if (state.exclusivity === "shared" && !(s.purity != null && s.purity < SHARED_MAX_PURITY)) return false;
    if (q !== "" && !matchesQuery(s, q)) return false;
    return true;
  });
  return sortSlots(filtered, state.sort);
}

function matchesQuery(s: Slot, q: string): boolean {
  const fields = [s.tweet?.text, s.author?.name, s.author?.username];
  return fields.some((f) => typeof f === "string" && normalize(f).includes(q));
}

export function sortSlots(slots: Slot[], sort: SortKey): Slot[] {
  const out = [...slots];
  const byRank = (a: Slot, b: Slot) => a.rank - b.rank;
  switch (sort) {
    case "rank":
      return out.sort(byRank);
    case "purity":
      return out.sort((a, b) => desc(a.purity, b.purity) || byRank(a, b));
    case "rt_graph":
      return out.sort((a, b) => desc(a.rt_graph, b.rt_graph) || byRank(a, b));
    case "api_retweets":
      return out.sort(
        (a, b) => desc(a.tweet?.metrics.retweet_count ?? null, b.tweet?.metrics.retweet_count ?? null) || byRank(a, b),
      );
    case "date":
      return out.sort((a, b) => asc(createdAt(a), createdAt(b)) || byRank(a, b));
  }
}

function createdAt(s: Slot): number | null {
  return s.tweet ? Date.parse(s.tweet.created_at) : null;
}

/** Decrescente; null sempre por último. */
function desc(a: number | null, b: number | null): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return b - a;
}

/** Crescente; null sempre por último. */
function asc(a: number | null, b: number | null): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return a - b;
}
```

- [x] **Step 4: Rodar e ver passar**

Run (em `web/`): `npx vitest run`
Expected: PASS — 3 arquivos (format, entities, filter), 25 testes.

- [ ] **Step 5: Commit** — *pulado*. `feat(web): ordenar/filtrar/buscar slots`.

---

### Task 5: Camada de dados, glossário, router, abas de evento

**Files:**
- Create: `web/src/data/fetchJson.ts`, `web/src/data/loadIndex.ts`, `web/src/data/loadEvent.ts`, `web/src/data/hooks.ts`
- Create: `web/src/lib/glossary.ts`, `web/src/lib/paths.ts`, `web/src/lib/color.ts`
- Create: `web/src/components/States.tsx`, `web/src/components/EventTabs.tsx`
- Modify: `web/src/main.tsx`, `web/src/App.tsx`

**Interfaces:**
- Consumes: `Index`, `EventMeta`, `EventData`, `Slot`, `Layout` (types.ts); `formatDay` (format.ts).
- Produces:
  - `fetchJson<T>(path: string): Promise<T>`; `class ExportNotFoundError extends Error { readonly path: string }`
  - `loadIndex(): Promise<Index>`; `loadEvent(meta: EventMeta): Promise<EventData>`
  - `type AsyncState<T> = { status: "loading" } | { status: "error"; error: Error } | { status: "ready"; data: T }`
  - `useIndex(): AsyncState<Index>`; `useEvent(meta: EventMeta): AsyncState<EventData>`
  - `GLOSSARY` (chaves `rank, rt_cluster, purity, rt_graph, rt_event, api, also_in, frac_nodes, intra_weight_frac, hydrated, attrition`), `SLOT_STATUS_TEXT`, `AUTHOR_STATUS_TEXT`, `EVENT_SHORT_NAMES`, `VERIFIED_TYPE_TEXT`, `REFERENCE_TEXT`
  - `clusterPath(slug, community)`, `eventDefaultPath(meta)`, `indexDefaultPath(index)`
  - `withAlpha(hex: string, alpha: number): string`
  - `<Skeleton className? />`, `<ErrorBox error />`, `<EventTabs events activeSlug onSelect(meta) />`
  - `App` (default; rota `/:evento/:community?`), `RootRedirect` (rota `/`), `Reader` interno — o `Reader` ganha corpo nas Tasks 6–9.

- [x] **Step 1: `web/src/data/fetchJson.ts`**

```ts
/** Erro padrão de dados ausentes (spec §8): sem retry automático. */
export class ExportNotFoundError extends Error {
  readonly path: string;

  constructor(path: string) {
    super(`não encontrei data/export${path}; rode a célula M10 do pipeline_tcc2.ipynb`);
    this.name = "ExportNotFoundError";
    this.path = path;
  }
}

/**
 * fetch de JSON estático servido pelo Vite a partir de data/export/.
 * O dev server devolve index.html (200, text/html) para caminhos desconhecidos — por isso
 * o content-type também é verificado.
 */
export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  const type = res.headers.get("content-type") ?? "";
  if (!res.ok || !type.includes("json")) throw new ExportNotFoundError(path);
  return (await res.json()) as T;
}
```

- [x] **Step 2: `web/src/data/loadIndex.ts` e `web/src/data/loadEvent.ts`**

`web/src/data/loadIndex.ts`:
```ts
import type { Index } from "../types";
import { fetchJson } from "./fetchJson";

let cache: Promise<Index> | null = null;

/** index.json, carregado uma vez por sessão. */
export function loadIndex(): Promise<Index> {
  if (!cache) {
    cache = fetchJson<Index>("/index.json").catch((err: unknown) => {
      cache = null; // permite tentar de novo depois de rodar a M10
      throw err;
    });
  }
  return cache;
}
```

`web/src/data/loadEvent.ts`:
```ts
import type { EventData, EventMeta, Layout, Slot } from "../types";
import { fetchJson } from "./fetchJson";

const cache = new Map<string, Promise<EventData>>();

/** tweets.json + layout.json de um evento, em memória por slug (trocar de aba não re-baixa). */
export function loadEvent(meta: EventMeta): Promise<EventData> {
  let pending = cache.get(meta.slug);
  if (!pending) {
    pending = Promise.all([fetchJson<Slot[]>(`/${meta.files.tweets}`), fetchJson<Layout>(`/${meta.files.layout}`)])
      .then(([slots, layout]) => ({ meta, slots, layout }))
      .catch((err: unknown) => {
        cache.delete(meta.slug);
        throw err;
      });
    cache.set(meta.slug, pending);
  }
  return pending;
}
```

- [x] **Step 3: `web/src/data/hooks.ts`**

```ts
import { useEffect, useState } from "react";
import type { EventData, EventMeta, Index } from "../types";
import { loadEvent } from "./loadEvent";
import { loadIndex } from "./loadIndex";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "ready"; data: T };

const LOADING: { status: "loading" } = { status: "loading" };

/**
 * Executa `start` quando `key` muda; ignora resultados de execuções antigas.
 * O estado guarda a chave a que pertence: se a chave pedida for outra, devolve `loading`
 * já no mesmo render — nunca entrega dados de um evento sob o rótulo de outro.
 * (Correção feita na execução, 2026-09-15: a versão que fazia `setState(loading)` dentro do efeito
 * deixava um render com `meta` novo e `event.data` do evento anterior.)
 */
function useAsync<T>(start: () => Promise<T>, key: string): AsyncState<T> {
  const [state, setState] = useState<{ key: string; value: AsyncState<T> }>({ key, value: LOADING });
  useEffect(() => {
    let alive = true;
    start().then(
      (data) => {
        if (alive) setState({ key, value: { status: "ready", data } });
      },
      (err: unknown) => {
        if (alive) setState({ key, value: { status: "error", error: err instanceof Error ? err : new Error(String(err)) } });
      },
    );
    return () => {
      alive = false;
    };
    // `start` é recriado a cada render; `key` é a identidade do que se carrega.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state.key === key ? state.value : LOADING;
}

export function useIndex(): AsyncState<Index> {
  return useAsync(loadIndex, "index");
}

export function useEvent(meta: EventMeta): AsyncState<EventData> {
  return useAsync(() => loadEvent(meta), meta.slug);
}
```

- [x] **Step 4: `web/src/lib/glossary.ts` — todos os textos fixos da interface**

```ts
import type { ReferencedTweetType, SlotStatus } from "../types";

/** Tooltips da faixa de pesquisa e do painel (spec §7.6). Dizem o que o número É — nunca um juízo. */
export const GLOSSARY = {
  rank: "Posição no ranking do cluster pelo nº de membros que retuitaram.",
  rt_cluster: "Usuários deste cluster (nós do grafo) que retuitaram. Critério de seleção (D6).",
  purity: "Fração dos retweets de nós do grafo que vieram deste cluster. 1,00 = só este cluster.",
  rt_graph: "Nós do grafo (qualquer cluster) que retuitaram.",
  rt_event: "Usuários do evento que retuitaram, inclusive os filtrados por atividade (N).",
  api: "Reposts totais segundo a API hoje, e a razão para o alcance dentro do evento. Só se hidratado.",
  also_in: "O mesmo tweet está no top-K de outro cluster deste evento.",
  frac_nodes: "Fração dos nós (usuários) do grafo que pertencem a este cluster.",
  intra_weight_frac: "Peso das arestas internas ao cluster sobre o peso total do grafo. ≤ 5% ⇒ K = 20.",
  hydrated: "Slots selecionados que a API devolveu / slots selecionados.",
  attrition: "Fração dos slots selecionados que a API não devolveu (removidos, suspensos ou protegidos).",
} as const;

/** RF7: título do card fantasma por status. `error` usa `error.title` quando existir. */
export const SLOT_STATUS_TEXT: Record<Exclude<SlotStatus, "hydrated">, string> = {
  not_found: "Tweet removido ou indisponível",
  not_authorized: "Conta suspensa ou protegida",
  error: "Erro na API",
  pending: "Ainda não hidratado",
};

/** RF8: motivo de autor indisponível em tweet hidratado. */
export const AUTHOR_STATUS_TEXT: Record<string, string> = {
  not_found: "conta removida",
  not_authorized: "conta suspensa ou protegida",
  pending: "não hidratado",
  error: "erro na API",
};

/** Rótulo curto das abas (spec §7.1). Chave = slug do export. */
export const EVENT_SHORT_NAMES: Record<string, string> = {
  "mobilizacao-0709": "Mobilização 7/9",
  "roberto-jefferson": "Roberto Jefferson",
  eleicoes: "Eleições 30/10",
  "invasao-3-poderes": "8 de janeiro",
};

/** Tooltip do selo de verificado por `verified_type`. */
export const VERIFIED_TYPE_TEXT: Record<string, string> = {
  blue: "verificado (assinante)",
  business: "verificado (organização)",
  government: "verificado (governo)",
  none: "verificado",
};

export const REFERENCE_TEXT: Record<ReferencedTweetType, string> = {
  quoted: "citando um tweet",
  replied_to: "em resposta a um tweet",
  retweeted: "repostando um tweet",
};
```

- [x] **Step 5: `web/src/lib/paths.ts` e `web/src/lib/color.ts`**

`web/src/lib/paths.ts`:
```ts
import type { EventMeta, Index } from "../types";

export function clusterPath(slug: string, community: number): string {
  return `/${slug}/${community}`;
}

/** Grupo 1 do evento (clusters vêm ordenados por group no export). */
export function eventDefaultPath(meta: EventMeta): string {
  return clusterPath(meta.slug, meta.clusters[0]?.community ?? 0);
}

/** Primeiro evento do índice, Grupo 1 (RF10). */
export function indexDefaultPath(index: Index): string {
  return eventDefaultPath(index.events[0]);
}
```

`web/src/lib/color.ts`:
```ts
/** "#RRGGBB" → "rgba(r, g, b, alpha)"; devolve a entrada se não for hex de 6 dígitos. */
export function withAlpha(hex: string, alpha: number): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!m) return hex;
  const n = parseInt(m[1], 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}
```

- [x] **Step 6: `web/src/components/States.tsx` e `web/src/components/EventTabs.tsx`**

`web/src/components/States.tsx`:
```tsx
/** Estados de carregamento e erro (spec §8): esqueleto simples; erro sem retry automático. */

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`animate-pulse rounded-xl bg-gray-100 ${className}`} />;
}

export function ErrorBox({ error }: { error: Error }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-[14px] text-red-900">
      <strong>Não consegui carregar os dados.</strong>
      <pre className="mt-1 whitespace-pre-wrap font-mono text-[12.5px]">{error.message}</pre>
    </div>
  );
}
```

`web/src/components/EventTabs.tsx`:
```tsx
import type { EventMeta } from "../types";
import { formatDay } from "../lib/format";
import { EVENT_SHORT_NAMES } from "../lib/glossary";

interface Props {
  events: EventMeta[];
  activeSlug: string;
  onSelect: (meta: EventMeta) => void;
}

/** RF1: uma aba por evento do índice, com nome curto e data; a ativa fica sublinhada. */
export function EventTabs({ events, activeSlug, onSelect }: Props) {
  return (
    <nav aria-label="Eventos" className="flex gap-1 overflow-x-auto">
      {events.map((e) => {
        const active = e.slug === activeSlug;
        return (
          <button
            key={e.slug}
            type="button"
            onClick={() => onSelect(e)}
            title={e.name}
            aria-current={active ? "page" : undefined}
            className={`flex flex-col items-start rounded-lg px-3 py-1.5 text-left leading-tight hover:bg-gray-100 ${
              active ? "text-ink" : "text-muted"
            }`}
          >
            <span className={`text-[14px] font-semibold ${active ? "underline decoration-2 underline-offset-4" : ""}`}>
              {EVENT_SHORT_NAMES[e.slug] ?? e.name}
            </span>
            <span className="text-[11.5px]">{e.event_date ? formatDay(e.event_date) : "—"}</span>
          </button>
        );
      })}
    </nav>
  );
}
```

- [x] **Step 7: Router em `web/src/main.tsx`**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App, { RootRedirect } from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/:evento/:community?" element={<App />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
```

- [x] **Step 8: `web/src/App.tsx` — resolução de parâmetros, redirecionamentos, moldura da página, abas**

```tsx
import type { ReactNode } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import type { ClusterMeta, EventMeta, Index } from "./types";
import { useIndex } from "./data/hooks";
import { eventDefaultPath, indexDefaultPath } from "./lib/paths";
import { EventTabs } from "./components/EventTabs";
import { ErrorBox, Skeleton } from "./components/States";

/** `/` → primeiro evento do índice, Grupo 1 (RF10). */
export function RootRedirect() {
  const index = useIndex();
  if (index.status === "loading") return <PageFrame><Skeleton className="h-40" /></PageFrame>;
  if (index.status === "error") return <PageFrame><ErrorBox error={index.error} /></PageFrame>;
  return <Navigate to={indexDefaultPath(index.data)} replace />;
}

/** `/:evento/:community?` — valida os parâmetros (spec §8) e delega ao Reader. */
export default function App() {
  const { evento, community } = useParams();
  const index = useIndex();
  if (index.status === "loading") return <PageFrame><Skeleton className="h-40" /></PageFrame>;
  if (index.status === "error") return <PageFrame><ErrorBox error={index.error} /></PageFrame>;

  const meta = index.data.events.find((e) => e.slug === evento);
  if (!meta) return <Navigate to={indexDefaultPath(index.data)} replace />;
  const cluster = meta.clusters.find((c) => String(c.community) === community);
  if (!cluster) return <Navigate to={eventDefaultPath(meta)} replace />;

  return <Reader index={index.data} meta={meta} cluster={cluster} />;
}

interface ReaderProps {
  index: Index;
  meta: EventMeta;
  cluster: ClusterMeta;
}

/** Corpo do leitor. Fica montado entre trocas de evento/cluster (mesma rota), então o estado local sobrevive. */
function Reader({ index, meta, cluster }: ReaderProps) {
  const navigate = useNavigate();
  const selectEvent = (e: EventMeta) => navigate(eventDefaultPath(e));

  return (
    <PageFrame header={<EventTabs events={index.events} activeSlug={meta.slug} onSelect={selectEvent} />}>
      <p className="text-muted">
        {meta.name} · {cluster.label} (c{cluster.community})
      </p>
    </PageFrame>
  );
}

export function PageFrame({ header, children }: { header?: ReactNode; children: ReactNode }) {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-line bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-1 px-4 py-2">
          <h1 className="text-[17px] font-bold tracking-tight">Leitor de clusters</h1>
          {header}
        </div>
      </header>
      <main className="mx-auto max-w-[1600px] px-4 py-4">{children}</main>
    </div>
  );
}
```

- [x] **Step 9: Verificar**

Run (em `web/`): `npx tsc -b`
Expected: sem erros.

Run (em `web/`): `npm run dev -- --port 5173 &`; `curl -s http://localhost:5173/ | grep -c 'src="/src/main.tsx"'`; matar o servidor.
Expected: `1` (a SPA é servida). Verificação manual no navegador: abrir `http://localhost:5173/` → redireciona para `/mobilizacao-0709/0`; as quatro abas trocam a URL para `/<slug>/<community do Grupo 1>` (`/roberto-jefferson/1`, `/eleicoes/1`, `/invasao-3-poderes/1`); `/nao-existe/9` volta para `/mobilizacao-0709/0`; `/eleicoes/99` volta para `/eleicoes/1`; `/eleicoes` (sem community) vai para `/eleicoes/1`.

- [ ] **Step 10: Commit** — *pulado*. `feat(web): carga de index/eventos, router e abas`.

---

### Task 6: Painel de clusters + seleção via URL

**Files:**
- Create: `web/src/components/ClusterPanel.tsx`
- Modify: `web/src/App.tsx` (função `Reader`)

**Interfaces:**
- Consumes: `EventMeta`, `ClusterMeta`; `formatCompact`, `formatInt`, `formatPct`; `GLOSSARY`; `withAlpha`; `clusterPath`.
- Produces: `<ClusterPanel event selected onSelect(community) />`.

- [x] **Step 1: `web/src/components/ClusterPanel.tsx`**

```tsx
import type { EventMeta } from "../types";
import { withAlpha } from "../lib/color";
import { formatCompact, formatInt, formatPct } from "../lib/format";
import { GLOSSARY } from "../lib/glossary";

interface Props {
  event: EventMeta;
  selected: number;
  onSelect: (community: number) => void;
}

/** RF2 / spec §7.2: um item por ClusterMeta na ordem `group`; rodapé com os parâmetros da fase 1. */
export function ClusterPanel({ event, selected, onSelect }: Props) {
  const rc = event.run_config;
  return (
    <section className="rounded-xl border border-line bg-white">
      <h2 className="px-4 pt-3 text-[11px] font-semibold uppercase tracking-wider text-muted">Clusters</h2>
      <ul className="mt-1">
        {event.clusters.map((c) => {
          const active = c.community === selected;
          return (
            <li key={c.community}>
              <button
                type="button"
                onClick={() => onSelect(c.community)}
                aria-pressed={active}
                className="w-full border-l-4 px-4 py-2 text-left hover:bg-gray-50"
                style={{
                  borderLeftColor: active ? c.color : "transparent",
                  backgroundColor: active ? withAlpha(c.color, 0.1) : undefined,
                }}
              >
                <div className="flex items-center gap-2 text-[14px]">
                  <span className="inline-block h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: c.color }} />
                  <span className="font-semibold">{c.label}</span>
                  <span className="text-muted">(c{c.community})</span>
                  <span className="ml-auto cursor-help" title={GLOSSARY.frac_nodes}>
                    {formatPct(c.frac_nodes)}
                  </span>
                  <span className="text-muted">K={c.k}</span>
                </div>
                <div className="mt-0.5 pl-5 text-[12px] text-muted">
                  <span className="cursor-help" title={GLOSSARY.intra_weight_frac}>
                    peso interno {formatPct(c.intra_weight_frac, 1)}
                  </span>
                  {" · "}
                  <span className="cursor-help" title={GLOSSARY.hydrated}>
                    {c.n_hydrated}/{c.n_selected} hidratados
                  </span>
                  {" · "}
                  <span className="cursor-help" title={GLOSSARY.attrition}>
                    atrição {formatPct(c.attrition)}
                  </span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
      <footer className="border-t border-line px-4 py-2 text-[12px] leading-5 text-muted">
        {formatInt(event.n_nodes)} nós · {formatCompact(event.n_edges)} arestas · {event.n_communities} comunidades
        <br />
        N={String(rc.min_user_retweets ?? "?")} τ={String(rc.tau ?? "?")} · K={event.selection.k}/{event.selection.k_small}
      </footer>
    </section>
  );
}
```

- [x] **Step 2: Montar o layout de duas colunas no `Reader` (`web/src/App.tsx`)**

Substituir a função `Reader` por:
```tsx
function Reader({ index, meta, cluster }: ReaderProps) {
  const navigate = useNavigate();
  const selectEvent = (e: EventMeta) => navigate(eventDefaultPath(e));
  const selectCluster = (community: number) => navigate(clusterPath(meta.slug, community));

  return (
    <PageFrame header={<EventTabs events={index.events} activeSlug={meta.slug} onSelect={selectEvent} />}>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[400px_minmax(0,1fr)]">
        <aside className="space-y-4 xl:sticky xl:top-[61px] xl:self-start">
          <Skeleton className="h-[360px]" />
          <ClusterPanel event={meta} selected={cluster.community} onSelect={selectCluster} />
        </aside>
        <section className="min-w-0">
          <p className="text-muted">
            {cluster.label} (c{cluster.community})
          </p>
        </section>
      </div>
    </PageFrame>
  );
}
```
e acrescentar os imports: `import { ClusterPanel } from "./components/ClusterPanel";` e `clusterPath` em `./lib/paths`.

- [x] **Step 3: Verificar**

Run (em `web/`): `npx tsc -b` → sem erros. Manual: em `/invasao-3-poderes/1` o painel lista Grupo 1 (c1) 44% K=100 · Grupo 2 (c0) 34% · Grupo 3 (c2) 21%, com as cores `#5E4FA2`, `#26A69A`, `#E8852B`; rodapé `33.305 nós · 12 mi arestas · 11 comunidades / N=7 τ=0.1 · K=100/20`; clicar em Grupo 2 leva a `/invasao-3-poderes/0` e o item fica tingido com borda esquerda na cor.

- [ ] **Step 4: Commit** — *pulado*. `feat(web): painel de clusters com seleção pela URL`.

---

### Task 7: Cards — `Avatar`, `TweetText`, `ResearchStrip`, `TweetCard`, `GhostCard`, `CardList`

**Files:**
- Create: `web/src/components/Avatar.tsx`, `web/src/components/TweetText.tsx`, `web/src/components/ResearchStrip.tsx`, `web/src/components/TweetCard.tsx`, `web/src/components/GhostCard.tsx`, `web/src/components/CardList.tsx`
- Modify: `web/src/App.tsx` (função `Reader`: carregar evento, filtrar slots do cluster, renderizar `CardList`)

**Interfaces:**
- Consumes: `Slot`, `Tweet`, `Author`, `ClusterMeta`, `EventData`; `segmentText`, `hasMedia`, `Segment`; `formatCompact`, `formatDate`, `formatDec`, `formatInt`; `GLOSSARY`, `SLOT_STATUS_TEXT`, `AUTHOR_STATUS_TEXT`, `VERIFIED_TYPE_TEXT`, `REFERENCE_TEXT`; `withAlpha`; `EXCLUSIVE_MIN_PURITY`, `SHARED_MAX_PURITY`; `useEvent`.
- Produces:
  - `<Avatar src name color size? />`
  - `<TweetText segments />`
  - `<ResearchStrip slot color />`
  - `<TweetCard slot color />` (exige `slot.tweet !== null`; o `CardList` garante)
  - `<GhostCard slot color />`
  - `<CardList cluster slots />` — nesta task sem toolbar (Task 9 acrescenta `toolbar`/`onToolbarChange`).

- [x] **Step 1: `web/src/components/Avatar.tsx`**

```tsx
import { useState } from "react";

interface Props {
  src: string | null;
  name: string | null;
  color: string;
  size?: number;
}

/** Avatar redondo com fallback de iniciais sobre a cor do grupo (X remove imagens de contas suspensas). */
export function Avatar({ src, name, color, size = 40 }: Props) {
  const [failed, setFailed] = useState(false);
  const style = { width: size, height: size };
  if (!src || failed) {
    return (
      <div
        aria-hidden
        style={{ ...style, backgroundColor: color }}
        className="flex shrink-0 select-none items-center justify-center rounded-full text-[14px] font-bold text-white"
      >
        {initials(name)}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt=""
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
      style={style}
      className="shrink-0 rounded-full bg-gray-100 object-cover"
    />
  );
}

function initials(name: string | null): string {
  const words = (name ?? "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
  const out = words.map((w) => Array.from(w)[0]?.toUpperCase() ?? "").join("");
  return out || "?";
}
```

- [x] **Step 2: `web/src/components/TweetText.tsx`**

```tsx
import type { Segment } from "../lib/entities";

/** Renderiza os segmentos de `segmentText`: texto puro, hashtag/menção/url/mídia como links em nova aba. */
export function TweetText({ segments }: { segments: Segment[] }) {
  return (
    <p className="whitespace-pre-wrap break-words text-[15px] leading-5 text-ink">
      {segments.map((s, i) =>
        s.kind === "text" ? (
          <span key={i}>{s.text}</span>
        ) : (
          <a key={i} href={s.href} target="_blank" rel="noopener noreferrer" className="text-x-blue hover:underline">
            {s.text}
          </a>
        ),
      )}
    </p>
  );
}
```

- [x] **Step 3: `web/src/components/ResearchStrip.tsx`**

```tsx
import { Fragment } from "react";
import type { Slot } from "../types";
import { withAlpha } from "../lib/color";
import { EXCLUSIVE_MIN_PURITY, SHARED_MAX_PURITY } from "../lib/filter";
import { formatDec, formatInt } from "../lib/format";
import { GLOSSARY } from "../lib/glossary";

interface Props {
  slot: Slot;
  color: string;
}

interface Item {
  key: string;
  text: string;
  title: string;
  className?: string;
}

/**
 * RF6 / spec §7.6: faixa de metadados da pesquisa, presente em todo card (hidratado ou fantasma).
 * Todos os números vêm do slot; a única conta é a razão API/evento pedida pelo spec.
 */
export function ResearchStrip({ slot, color }: Props) {
  const apiRetweets = slot.tweet?.metrics.retweet_count ?? null;
  const items: Item[] = [
    { key: "rank", text: `#${slot.rank} de ${slot.k}`, title: GLOSSARY.rank, className: "font-semibold text-ink" },
    { key: "rt_cluster", text: `${formatInt(slot.rt_cluster)} RTs de membros`, title: GLOSSARY.rt_cluster },
    { key: "purity", text: `pureza ${formatDec(slot.purity, 2)}`, title: GLOSSARY.purity, className: purityClass(slot.purity) },
    { key: "rt_graph", text: `${formatInt(slot.rt_graph)} no grafo`, title: GLOSSARY.rt_graph },
    { key: "rt_event", text: `${formatInt(slot.rt_event)} no evento`, title: GLOSSARY.rt_event },
  ];
  if (apiRetweets != null) {
    const ratio = slot.rt_event > 0 ? `${formatDec(apiRetweets / slot.rt_event, 1)}×` : "—";
    items.push({ key: "api", text: `API ${formatInt(apiRetweets)} (${ratio})`, title: GLOSSARY.api });
  }
  for (const a of slot.also_in) {
    items.push({ key: `also-${a.community}`, text: `também em Grupo ${a.group} (#${a.rank})`, title: GLOSSARY.also_in });
  }

  return (
    <div
      className="flex flex-wrap items-center gap-x-1.5 gap-y-1 border-t border-line px-4 py-2 text-[12.5px] text-muted"
      style={{ backgroundColor: withAlpha(color, 0.06) }}
    >
      {items.map((it, i) => (
        <Fragment key={it.key}>
          {i > 0 && <span aria-hidden>·</span>}
          <span title={it.title} className={`cursor-help ${it.className ?? ""}`}>
            {it.text}
          </span>
        </Fragment>
      ))}
    </div>
  );
}

/** Sinalização de leitura (spec §7.6): ≥ 0,90 verde-escuro discreto; < 0,50 laranja discreto; entre, neutro. */
function purityClass(purity: number | null): string {
  if (purity == null) return "";
  if (purity >= EXCLUSIVE_MIN_PURITY) return "text-emerald-800";
  if (purity < SHARED_MAX_PURITY) return "text-orange-700";
  return "";
}
```

- [x] **Step 4: `web/src/components/TweetCard.tsx`**

```tsx
import type { ReactNode } from "react";
import { useMemo } from "react";
import {
  BadgeCheck,
  Bookmark,
  ExternalLink,
  Eye,
  Heart,
  Image as ImageIcon,
  MessageCircle,
  Quote,
  Repeat2,
  TriangleAlert,
  UserRound,
} from "lucide-react";
import type { Author, Slot, Tweet } from "../types";
import { hasMedia, segmentText } from "../lib/entities";
import { formatCompact, formatDate, formatInt } from "../lib/format";
import { AUTHOR_STATUS_TEXT, REFERENCE_TEXT, VERIFIED_TYPE_TEXT } from "../lib/glossary";
import { Avatar } from "./Avatar";
import { ResearchStrip } from "./ResearchStrip";
import { TweetText } from "./TweetText";

interface Props {
  slot: Slot & { tweet: Tweet };
  color: string;
}

const MISSING_AUTHOR_COLOR = "#9ca3af";

/** RF5 / spec §7.4: card estilo X (sem marca) + faixa de pesquisa. */
export function TweetCard({ slot, color }: Props) {
  const { tweet, author } = slot;
  const segments = useMemo(() => segmentText(tweet.text, tweet.entities, tweet.url), [tweet]);
  const media = hasMedia(tweet.entities);
  const m = tweet.metrics;

  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-white">
      <div className="px-4 pt-3">
        <header className="flex items-start gap-3">
          <Avatar
            src={author?.profile_image_url ?? null}
            name={author?.name ?? null}
            color={author ? color : MISSING_AUTHOR_COLOR}
          />
          <div className="min-w-0 flex-1 text-[15px] leading-5">
            {author ? (
              <AuthorLine author={author} createdAt={tweet.created_at} />
            ) : (
              <MissingAuthor slot={slot} createdAt={tweet.created_at} />
            )}
          </div>
          <a
            href={tweet.url}
            target="_blank"
            rel="noopener noreferrer"
            title="abrir no X"
            className="shrink-0 rounded-full p-1 text-muted hover:bg-gray-100 hover:text-x-blue"
          >
            <ExternalLink size={16} />
          </a>
        </header>

        <div className="mt-2">
          <TweetText segments={segments} />
        </div>

        {(media || tweet.referenced_tweets.length > 0) && (
          <div className="mt-2 flex flex-wrap gap-2">
            {media && (
              <a href={tweet.url} target="_blank" rel="noopener noreferrer" className="chip" title="mídia não hidratada; abre o tweet no X">
                <ImageIcon size={14} /> Mídia <ExternalLink size={12} />
              </a>
            )}
            {tweet.referenced_tweets.map((r) => (
              <a
                key={`${r.type}-${r.id}`}
                href={`https://x.com/i/web/status/${r.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="chip"
              >
                {REFERENCE_TEXT[r.type]} <ExternalLink size={12} />
              </a>
            ))}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 pb-3 text-[13px] text-muted">
          <Metric icon={<MessageCircle size={16} />} value={m.reply_count} label="respostas" />
          <Metric icon={<Repeat2 size={16} />} value={m.retweet_count} label="reposts" />
          <Metric icon={<Quote size={16} />} value={m.quote_count} label="citações" />
          <Metric icon={<Heart size={16} />} value={m.like_count} label="curtidas" />
          <Metric icon={<Bookmark size={16} />} value={m.bookmark_count} label="salvos" />
          <Metric icon={<Eye size={16} />} value={m.impression_count} label="impressões" />
          <span className="ml-auto flex items-center gap-1.5">
            {tweet.lang && (
              <span className="badge" title="idioma segundo a API">
                {tweet.lang}
              </span>
            )}
            {tweet.possibly_sensitive && (
              <span className="badge border-amber-300 text-amber-800" title="marcado pela API como possivelmente sensível">
                <TriangleAlert size={11} /> sensível
              </span>
            )}
          </span>
        </div>
      </div>
      <ResearchStrip slot={slot} color={color} />
    </article>
  );
}

function Metric({ icon, value, label }: { icon: ReactNode; value: number | null; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 whitespace-nowrap" title={value == null ? label : `${formatInt(value)} ${label}`}>
      {icon}
      {formatCompact(value)}
    </span>
  );
}

function AuthorLine({ author, createdAt }: { author: Author; createdAt: string }) {
  const tooltip = [
    author.description,
    author.location,
    author.metrics.followers_count != null ? `${formatInt(author.metrics.followers_count)} seguidores` : null,
  ]
    .filter((v): v is string => Boolean(v))
    .join("\n");
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-1">
      <span className="truncate font-bold text-ink" title={tooltip}>
        {author.name ?? "—"}
      </span>
      {author.verified && (
        <span className="inline-flex shrink-0 text-x-blue" title={VERIFIED_TYPE_TEXT[author.verified_type ?? "none"] ?? "verificado"}>
          <BadgeCheck size={16} />
        </span>
      )}
      <span className="truncate text-muted">@{author.username ?? author.id}</span>
      <span className="text-muted">·</span>
      <time dateTime={createdAt} className="whitespace-nowrap text-muted">
        {formatDate(createdAt)}
      </time>
    </div>
  );
}

/** RF8: tweet hidratado cujo autor a API não devolveu. */
function MissingAuthor({ slot, createdAt }: { slot: Slot; createdAt: string }) {
  const reason = slot.author_status ? AUTHOR_STATUS_TEXT[slot.author_status] : null;
  return (
    <div className="flex flex-wrap items-center gap-x-1 text-muted">
      <UserRound size={14} />
      <span className="font-semibold">Autor não disponível</span>
      {reason && <span>({reason})</span>}
      {slot.author_id && <span className="font-mono text-[12.5px]">id {slot.author_id}</span>}
      <span>·</span>
      <time dateTime={createdAt} className="whitespace-nowrap">
        {formatDate(createdAt)}
      </time>
    </div>
  );
}
```

- [x] **Step 5: `web/src/components/GhostCard.tsx`**

```tsx
import { ExternalLink, TriangleAlert } from "lucide-react";
import type { Slot } from "../types";
import { SLOT_STATUS_TEXT } from "../lib/glossary";
import { ResearchStrip } from "./ResearchStrip";

interface Props {
  slot: Slot;
  color: string;
}

/** RF7: slot não devolvido pela API — mesmo lugar na lista, borda tracejada, motivo e link para o X. */
export function GhostCard({ slot, color }: Props) {
  const title =
    slot.status === "error"
      ? (slot.error?.title ?? SLOT_STATUS_TEXT.error)
      : slot.status === "hydrated"
        ? "Tweet sem conteúdo no export"
        : SLOT_STATUS_TEXT[slot.status];
  return (
    <article className="overflow-hidden rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50/60">
      <div className="flex items-center gap-3 px-4 py-3 text-muted">
        <TriangleAlert size={20} className="shrink-0" />
        <div className="min-w-0 flex-1 text-[14px]">
          <div className="font-semibold text-ink/80" title={slot.error?.detail ?? undefined}>
            {title}
          </div>
          <a
            href={`https://x.com/i/web/status/${slot.tweet_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-mono text-[12.5px] hover:text-x-blue hover:underline"
          >
            id {slot.tweet_id} <ExternalLink size={12} />
          </a>
        </div>
      </div>
      <ResearchStrip slot={slot} color={color} />
    </article>
  );
}
```

- [x] **Step 6: `web/src/components/CardList.tsx` (sem toolbar ainda)**

```tsx
import type { ClusterMeta, Slot, Tweet } from "../types";
import { GhostCard } from "./GhostCard";
import { TweetCard } from "./TweetCard";

interface Props {
  cluster: ClusterMeta;
  slots: Slot[]; // só os do cluster, na ordem do ranking
}

function isHydrated(s: Slot): s is Slot & { tweet: Tweet } {
  return s.status === "hydrated" && s.tweet !== null;
}

/** RF4: cabeçalho da lista e um card por slot (hidratado ou fantasma), na ordem do ranking. */
export function CardList({ cluster, slots }: Props) {
  const ghosts = cluster.n_selected - cluster.n_hydrated;
  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-center gap-x-2 text-[15px]">
        <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: cluster.color }} />
        <h2 className="font-bold">
          {cluster.label} <span className="font-normal text-muted">(c{cluster.community})</span>
        </h2>
        <span className="text-muted">
          · {cluster.n_selected} slots · {cluster.n_hydrated} hidratados · {ghosts} não devolvidos
        </span>
      </header>
      <ol className="space-y-3">
        {slots.map((s) => (
          <li key={`${s.community}-${s.rank}`}>
            {isHydrated(s) ? <TweetCard slot={s} color={cluster.color} /> : <GhostCard slot={s} color={cluster.color} />}
          </li>
        ))}
      </ol>
    </div>
  );
}
```

- [x] **Step 7: Carregar o evento e renderizar a lista no `Reader` (`web/src/App.tsx`)**

Substituir a função `Reader` por:
```tsx
function Reader({ index, meta, cluster }: ReaderProps) {
  const navigate = useNavigate();
  const event = useEvent(meta);
  const selectEvent = (e: EventMeta) => navigate(eventDefaultPath(e));
  const selectCluster = (community: number) => navigate(clusterPath(meta.slug, community));

  const clusterSlots = useMemo(
    () => (event.status === "ready" ? event.data.slots.filter((s) => s.community === cluster.community) : []),
    [event, cluster.community],
  );

  return (
    <PageFrame header={<EventTabs events={index.events} activeSlug={meta.slug} onSelect={selectEvent} />}>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[400px_minmax(0,1fr)]">
        <aside className="space-y-4 xl:sticky xl:top-[61px] xl:self-start">
          <Skeleton className="h-[360px]" />
          <ClusterPanel event={meta} selected={cluster.community} onSelect={selectCluster} />
        </aside>
        <section className="min-w-0">
          {event.status === "loading" && (
            <div className="space-y-3">
              <Skeleton className="h-7 w-1/2" />
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-40" />
              ))}
            </div>
          )}
          {event.status === "error" && <ErrorBox error={event.error} />}
          {event.status === "ready" && <CardList cluster={cluster} slots={clusterSlots} />}
        </section>
      </div>
    </PageFrame>
  );
}
```
Imports a acrescentar: `import { useMemo } from "react";`, `import { useEvent, useIndex } from "./data/hooks";` (substitui o import só de `useIndex`), `import { CardList } from "./components/CardList";`.

- [x] **Step 8: Verificar**

Run (em `web/`): `npx tsc -b` → sem erros. Manual em `/invasao-3-poderes/0` (Grupo 2, c0): cabeçalho `Grupo 2 (c0) · 100 slots · 84 hidratados · 16 não devolvidos`; o card #1 é da @Ana_Flor com avatar, nome, data `8 de jan. de 2023, 15:54`, texto com `#STF` e `#brasilia` azuis e clicáveis, chip "Mídia" (o `https://t.co/…` não aparece no texto), métricas `3,2 mil · 11,8 mil · 5,1 mil · 48,3 mil · 730 · 4,9 mi`, badge `pt`, faixa `#1 de 100 · 3.389 RTs de membros · pureza 0,75 · 4.496 no grafo · 11.802 no evento · API 11.829 (1,0×) · também em Grupo 3 (#16)`. O slot #13 é um card fantasma "Conta suspensa ou protegida" com `id 1612203522090758145` e faixa `#13 de 100 · 1.380 RTs de membros · pureza 0,86 … · também em Grupo 3 (#81)`. Passar o mouse nos itens da faixa mostra os tooltips do glossário.

- [ ] **Step 9: Commit** — *pulado*. `feat(web): cards estilo X, cards fantasma e faixa de pesquisa`.

---

### Task 8: Mini-mapa em Sigma.js (nós apenas, reducer, rótulos, clique)

**Files:**
- Create: `web/src/components/MiniMap.tsx`
- Modify: `web/src/App.tsx` (função `Reader`: trocar o `Skeleton` do mapa pelo `MiniMap` quando o evento estiver pronto)

**Interfaces:**
- Consumes: `Layout`, `ClusterMeta`; `formatPct`; Sigma v3 (`new Sigma(graph, container, settings)`, `nodeReducer`, `on("clickNode")`, `on("afterRender")`, `graphToViewport`, `refresh`, `getCamera().animatedReset`, `kill`); graphology `Graph`.
- Produces: `<MiniMap layout clusters selected onSelect(community) />`.

- [x] **Step 1: `web/src/components/MiniMap.tsx`**

```tsx
import { useEffect, useMemo, useRef } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import { LocateFixed } from "lucide-react";
import type { ClusterMeta, Layout } from "../types";
import { formatPct } from "../lib/format";

/** Cinza da fase 1 para nós fora do cluster selecionado e comunidades < 1%. */
const GREY = "#c7ccd6";
const NODE_SIZE = 1.3;

interface Props {
  layout: Layout;
  clusters: ClusterMeta[];
  selected: number;
  onSelect: (community: number) => void;
}

/**
 * RF3 / spec §7.3: scatter das coordenadas DRL (componente gigante) em Sigma, nós apenas — nenhuma aresta.
 * O grafo é construído uma vez por `layout`; trocar a seleção só chama `refresh()` (o reducer lê um ref).
 * Rótulos "Grupo g · XX%" são HTML absoluto reposicionado em `afterRender` via `graphToViewport(centroid)`.
 * Orientação: o espaço `graph` do Sigma tem y para cima, igual ao matplotlib da figura da fase 1 — não inverter.
 */
export function MiniMap({ layout, clusters, selected, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const labelRefs = useRef(new Map<number, HTMLButtonElement>());

  // refs lidos pelo reducer e pelos handlers, para não reconstruir o Sigma a cada mudança
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const colorByCommunity = useMemo(() => new Map(clusters.map((c) => [c.community, c.color])), [clusters]);
  const colorRef = useRef(colorByCommunity);
  colorRef.current = colorByCommunity;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const graph = new Graph({ type: "undirected" });
    const n = layout.x.length;
    for (let i = 0; i < n; i++) {
      graph.addNode(String(i), {
        x: layout.x[i],
        y: layout.y[i],
        size: NODE_SIZE,
        color: GREY,
        community: layout.community[i],
      });
    }

    const sigma = new Sigma(graph, container, {
      renderLabels: false,
      enableEdgeEvents: false,
      allowInvalidContainer: true,
      nodeReducer: (_node, data) => {
        const community = data.community as number;
        const color = community === selectedRef.current ? (colorRef.current.get(community) ?? GREY) : GREY;
        return { ...data, color };
      },
    });

    sigma.on("clickNode", ({ node }) => {
      onSelectRef.current(graph.getNodeAttribute(node, "community") as number);
    });

    const placeLabels = () => {
      for (const [community, el] of labelRefs.current) {
        const centroid = layout.centroids[String(community)];
        if (!centroid) continue;
        const p = sigma.graphToViewport({ x: centroid[0], y: centroid[1] });
        el.style.transform = `translate(-50%, -50%) translate(${p.x}px, ${p.y}px)`;
      }
    };
    sigma.on("afterRender", placeLabels);
    placeLabels();

    sigmaRef.current = sigma;
    return () => {
      sigma.kill();
      sigmaRef.current = null;
    };
  }, [layout]);

  // seleção mudou → recolorir sem reconstruir (o reducer lê selectedRef)
  useEffect(() => {
    sigmaRef.current?.refresh({ skipIndexation: true });
  }, [selected, colorByCommunity]);

  return (
    <div className="relative h-[360px] w-full overflow-hidden rounded-xl border border-line bg-white">
      <div ref={containerRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute inset-0">
        {clusters.map((c) => (
          <button
            key={c.community}
            type="button"
            ref={(el) => {
              if (el) labelRefs.current.set(c.community, el);
              else labelRefs.current.delete(c.community);
            }}
            onClick={() => onSelect(c.community)}
            title={`${c.label} (c${c.community}) — clique para selecionar`}
            className="label-halo pointer-events-auto absolute left-0 top-0 whitespace-nowrap text-[13px] font-bold"
            style={{ color: c.color, opacity: c.community === selected ? 1 : 0.8 }}
          >
            {c.label} · {formatPct(c.frac_nodes)}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => sigmaRef.current?.getCamera().animatedReset({ duration: 300 })}
        title="recentrar"
        className="absolute right-2 top-2 rounded-md border border-line bg-white/90 p-1 text-muted hover:text-ink"
      >
        <LocateFixed size={14} />
      </button>
      <div className="pointer-events-none absolute bottom-1 left-2 text-[10.5px] text-muted">
        {layout.n_plotted.toLocaleString("pt-BR")} nós da componente gigante · layout DRL
      </div>
    </div>
  );
}
```

- [x] **Step 2: Usar o `MiniMap` no `Reader` (`web/src/App.tsx`)**

Trocar `<Skeleton className="h-[360px]" />` dentro do `<aside>` por:
```tsx
{event.status === "ready" ? (
  <MiniMap
    layout={event.data.layout}
    clusters={meta.clusters}
    selected={cluster.community}
    onSelect={selectCluster}
  />
) : (
  <Skeleton className="h-[360px]" />
)}
```
e acrescentar `import { MiniMap } from "./components/MiniMap";`.

- [x] **Step 3: Verificar**

Run (em `web/`): `npx tsc -b` → sem erros. Manual em `/invasao-3-poderes/1`: o mapa aparece em < 2 s com 33.303 pontos; Grupo 1 (roxo) embaixo, Grupo 2 (verde) em cima à esquerda, Grupo 3 (laranja) à direita — mesma orientação de `data/processed/invasao-3-poderes/grafo-invasao-drl.png`; só o cluster selecionado está colorido; os três rótulos estão nos centróides e acompanham zoom/pan; clicar num nó verde navega para `/invasao-3-poderes/0` e o mapa recolore sem piscar; clicar no rótulo também seleciona; "recentrar" volta ao enquadramento inicial. Trocar de aba reconstrói o mapa do novo evento. Se a figura sair espelhada verticalmente em relação ao PNG, usar `y: -layout.y[i]` e `{ x: centroid[0], y: -centroid[1] }` — e registrar no README.

- [ ] **Step 4: Commit** — *pulado*. `feat(web): mini-mapa DRL em Sigma com destaque e seleção`.

---

### Task 9: Barra de ferramentas (RF9): ordenar, filtrar, buscar, contador

**Files:**
- Create: `web/src/components/Toolbar.tsx`, `web/src/lib/useDebounce.ts`
- Modify: `web/src/components/CardList.tsx` (props `toolbar`, `onToolbarChange`; aplica `applyToolbar`; estado vazio), `web/src/App.tsx` (função `Reader`: estado `toolbar`; limpar busca ao trocar de evento)

**Interfaces:**
- Consumes: `ToolbarState`, `DEFAULT_TOOLBAR`, `SortKey`, `StatusFilter`, `ExclusivityFilter`, `applyToolbar` (lib/filter.ts).
- Produces: `<Toolbar state onChange(next) shown total />`; `useDebounce<T>(value: T, ms: number): T`; `CardList` passa a receber `toolbar: ToolbarState` e `onToolbarChange: (next: ToolbarState) => void`.

- [x] **Step 1: `web/src/lib/useDebounce.ts`**

```ts
import { useEffect, useState } from "react";

/** Devolve `value` com atraso de `ms` após a última mudança (busca: 200 ms, spec §7.7). */
export function useDebounce<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}
```

- [x] **Step 2: `web/src/components/Toolbar.tsx`**

```tsx
import { Search, X } from "lucide-react";
import type { ExclusivityFilter, SortKey, StatusFilter, ToolbarState } from "../lib/filter";
import { DEFAULT_TOOLBAR } from "../lib/filter";

interface Props {
  state: ToolbarState;
  onChange: (next: ToolbarState) => void;
  shown: number;
  total: number;
}

const SORT_LABELS: Record<SortKey, string> = {
  rank: "ranking (padrão)",
  purity: "pureza",
  rt_graph: "RTs no grafo",
  api_retweets: "reposts na API",
  date: "mais antigo primeiro",
};
const STATUS_LABELS: Record<StatusFilter, string> = {
  all: "todos",
  hydrated: "só hidratados",
  ghost: "só não devolvidos",
};
const EXCLUSIVITY_LABELS: Record<ExclusivityFilter, string> = {
  all: "todos",
  exclusive: "exclusivos (pureza ≥ 0,90)",
  shared: "compartilhados (pureza < 0,50)",
};

function keys<K extends string>(labels: Record<K, string>): K[] {
  return Object.keys(labels) as K[];
}

/** RF9 / spec §7.7. O debounce da busca fica em quem consome `state.query` (CardList). */
export function Toolbar({ state, onChange, shown, total }: Props) {
  const set = <K extends keyof ToolbarState>(key: K, value: ToolbarState[K]) => onChange({ ...state, [key]: value });
  const dirty =
    state.sort !== DEFAULT_TOOLBAR.sort ||
    state.status !== DEFAULT_TOOLBAR.status ||
    state.exclusivity !== DEFAULT_TOOLBAR.exclusivity ||
    state.query !== DEFAULT_TOOLBAR.query;

  return (
    <div className="flex flex-wrap items-center gap-2 text-[13px]">
      <label className="flex items-center gap-1 text-muted">
        ordenar
        <select className="select" value={state.sort} onChange={(e) => set("sort", e.target.value as SortKey)}>
          {keys(SORT_LABELS).map((k) => (
            <option key={k} value={k}>
              {SORT_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1 text-muted">
        status
        <select className="select" value={state.status} onChange={(e) => set("status", e.target.value as StatusFilter)}>
          {keys(STATUS_LABELS).map((k) => (
            <option key={k} value={k}>
              {STATUS_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1 text-muted">
        exclusividade
        <select
          className="select"
          value={state.exclusivity}
          onChange={(e) => set("exclusivity", e.target.value as ExclusivityFilter)}
        >
          {keys(EXCLUSIVITY_LABELS).map((k) => (
            <option key={k} value={k}>
              {EXCLUSIVITY_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      <label className="relative flex items-center">
        <Search size={14} className="pointer-events-none absolute left-2 text-muted" />
        <input
          type="search"
          value={state.query}
          onChange={(e) => set("query", e.target.value)}
          placeholder="buscar no texto, nome ou @handle"
          aria-label="buscar"
          className="select w-64 pl-7"
        />
      </label>
      <span className="ml-auto text-muted">
        mostrando {shown} de {total}
      </span>
      {dirty && (
        <button type="button" onClick={() => onChange(DEFAULT_TOOLBAR)} className="chip">
          <X size={12} /> limpar
        </button>
      )}
    </div>
  );
}
```

- [x] **Step 3: Integrar no `web/src/components/CardList.tsx`**

Substituir o arquivo por:
```tsx
import { useMemo } from "react";
import type { ClusterMeta, Slot, Tweet } from "../types";
import { applyToolbar, DEFAULT_TOOLBAR, type ToolbarState } from "../lib/filter";
import { useDebounce } from "../lib/useDebounce";
import { GhostCard } from "./GhostCard";
import { Toolbar } from "./Toolbar";
import { TweetCard } from "./TweetCard";

interface Props {
  cluster: ClusterMeta;
  slots: Slot[]; // só os do cluster, na ordem do ranking
  toolbar: ToolbarState;
  onToolbarChange: (next: ToolbarState) => void;
}

function isHydrated(s: Slot): s is Slot & { tweet: Tweet } {
  return s.status === "hydrated" && s.tweet !== null;
}

/** RF4 + RF9: cabeçalho, barra de ferramentas e um card por slot visível (hidratado ou fantasma). */
export function CardList({ cluster, slots, toolbar, onToolbarChange }: Props) {
  const query = useDebounce(toolbar.query, 200);
  const visible = useMemo(() => applyToolbar(slots, { ...toolbar, query }), [slots, toolbar, query]);
  const ghosts = cluster.n_selected - cluster.n_hydrated;

  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-center gap-x-2 text-[15px]">
        <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: cluster.color }} />
        <h2 className="font-bold">
          {cluster.label} <span className="font-normal text-muted">(c{cluster.community})</span>
        </h2>
        <span className="text-muted">
          · {cluster.n_selected} slots · {cluster.n_hydrated} hidratados · {ghosts} não devolvidos
        </span>
      </header>
      <Toolbar state={toolbar} onChange={onToolbarChange} shown={visible.length} total={cluster.n_selected} />
      {visible.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-muted">
          nenhum tweet com esses filtros
          <div className="mt-3">
            <button type="button" className="chip" onClick={() => onToolbarChange(DEFAULT_TOOLBAR)}>
              limpar
            </button>
          </div>
        </div>
      ) : (
        <ol className="space-y-3">
          {visible.map((s) => (
            <li key={`${s.community}-${s.rank}`}>
              {isHydrated(s) ? <TweetCard slot={s} color={cluster.color} /> : <GhostCard slot={s} color={cluster.color} />}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
```

- [x] **Step 4: Estado da toolbar no `Reader` (`web/src/App.tsx`)**

Dentro de `Reader`, logo após `const event = useEvent(meta);`:
```tsx
const [toolbar, setToolbar] = useState<ToolbarState>(DEFAULT_TOOLBAR);
// spec §8: trocar de evento mantém ordenação/filtros e limpa a busca; trocar de cluster mantém tudo
useEffect(() => {
  setToolbar((t) => ({ ...t, query: "" }));
}, [meta.slug]);
```
e trocar a renderização da lista por:
```tsx
{event.status === "ready" && (
  <CardList cluster={cluster} slots={clusterSlots} toolbar={toolbar} onToolbarChange={setToolbar} />
)}
```
Imports: `import { useEffect, useMemo, useState } from "react";` e `import { DEFAULT_TOOLBAR, type ToolbarState } from "./lib/filter";`.

- [x] **Step 5: Verificar**

Run (em `web/`): `npx tsc -b && npx vitest run` → sem erros, 25 testes verdes. Manual em `/eleicoes/1`: ordenar por pureza reordena (fantasmas participam, pois têm pureza); "só não devolvidos" mostra 17 cards fantasma e o contador `mostrando 17 de 100`; "exclusivos" reduz a lista; digitar `lula` (sem acento, caixa baixa) filtra por texto/nome/handle após ~200 ms; combinação sem resultado mostra "nenhum tweet com esses filtros" + limpar; trocar para a aba "8 de janeiro" mantém ordenação/filtros e limpa a busca; trocar de cluster mantém tudo.

- [ ] **Step 6: Commit** — *pulado*. `feat(web): toolbar de ordenação, filtros e busca`.

---

### Task 10: Polimento, `vercel.json`, `README.md`, build e checklist de aceitação

**Files:**
- Create: `web/README.md`, `web/vercel.json`
- Verify: `web/src/App.tsx` (largura mínima / empilhamento < 1280 px já coberto por `xl:`), estados de erro

**Interfaces:** nenhuma nova.

- [x] **Step 1: `web/vercel.json` — deep links da SPA (arquivos estáticos são servidos antes do rewrite)**

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

- [x] **Step 2: `web/README.md`**

```markdown
# Leitor de clusters (web/)

Primeiro módulo da aplicação web do TCC (D9, D15): lê `data/export/` e mostra, por evento e
cluster, o mini-mapa DRL e os top-K tweets em cards estilo X com a faixa de metadados da pesquisa.
Spec: `docs/superpowers/specs/2026-09-15-leitor-de-clusters-design.md`.

## Rodar

```bash
cd web
npm install
npm run dev        # http://localhost:5173 → redireciona para o primeiro evento, Grupo 1
npm test           # vitest: lib/format, lib/entities, lib/filter
npm run build      # tsc -b + vite build → dist/ (inclui uma cópia de data/export/)
```

Rotas: `/` → `/<primeiro evento>/<community do Grupo 1>`; `/:evento/:community`
(ex.: `/eleicoes/3` abre o cluster c3 de eleicoes). Slug ou community inválidos redirecionam
para o padrão.

## De onde vêm os dados

`vite.config.ts` aponta `publicDir` para `../data/export`, então o app faz `fetch("/index.json")`,
`fetch("/<slug>/tweets.json")` e `fetch("/<slug>/layout.json")` — JSON estático, sem backend.
O contrato está em `src/types.ts` (cópia literal do §5 do spec); a fonte da verdade é
`modules/export.py` (`WebExporter`, M10).

**O app não computa nada da pesquisa.** Pureza, grupo, atrição, `rt_cluster/rt_graph/rt_event`
e `also_in` vêm prontos do export. A única aritmética é a razão `retweet_count / rt_event`
pedida pelo spec (§7.6) e a formatação pt-BR.

## Atualizar os dados

Re-executar a célula "Módulo 10" de `notebooks/pipeline_tcc2.ipynb` (regenera `data/export/`);
o dev server recarrega sozinho. Rodar o notebook inteiro é seguro e não chama a API se nada mudou.

## Estrutura

- `src/data/` — fetch com cache em memória (`loadIndex`, `loadEvent`) e hooks (`useIndex`, `useEvent`).
- `src/lib/` — utilitários puros: `format` (pt-BR), `entities` (texto → segmentos, offsets em
  code points), `filter` (ordenar/filtrar/buscar), `glossary` (todos os textos fixos: tooltips,
  status, nomes curtos), `paths`, `color`, `useDebounce`.
- `src/components/` — `EventTabs`, `ClusterPanel`, `MiniMap` (Sigma v3, nós apenas), `CardList`,
  `Toolbar`, `TweetCard`, `GhostCard`, `ResearchStrip`, `Avatar`, `TweetText`, `States`.
- `src/App.tsx` — `App` resolve `/:evento/:community?` e redireciona; `Reader` carrega o evento e
  monta o layout; `RootRedirect` trata `/`.

## Notas

- Mini-mapa: o espaço `graph` do Sigma tem y para cima, como o matplotlib da figura da fase 1;
  as coordenadas do DRL entram sem inversão.
- Avatares vêm de `pbs.twimg.com` e podem falhar (conta suspensa); o fallback são as iniciais
  sobre a cor do grupo.
- `vercel.json` só faz o rewrite da SPA; deploy está fora do escopo da v1.

## Fora de escopo (v1)

Anotações ou rótulos manuais; grafo com arestas; filtro temporal; painel de síntese narrativa;
comparação lado a lado de dois clusters; hidratação de mídia (o chip "Mídia" abre o tweet no X);
tweets citados com texto; autenticação; dark mode; deploy.
```

- [x] **Step 3: Build de produção e testes**

Run (em `web/`): `npm run build`
Expected: `tsc -b` sem erros; `vite build` gera `dist/` com `index.html`, `assets/*.js|css` e a cópia de `data/export/` (`dist/index.json`, `dist/eleicoes/tweets.json` …). Nenhum aviso de tipo.

Run (em `web/`): `npm test`
Expected: 3 arquivos, 25 testes verdes.

Run (na raiz): `git status --short`
Expected: só `web/` (sem `node_modules`/`dist`) e `docs/superpowers/plans/2026-09-15-leitor-de-clusters.md` como não rastreados.

- [x] **Step 4: Checklist de aceitação (spec §9) — verificação manual com `npm run dev`**

- [x] `/` redireciona para `/mobilizacao-0709/0` (primeiro evento do índice, Grupo 1).
- [x] As quatro abas funcionam; clusters na ordem por tamanho, cores da paleta, numeração "Grupo g" igual às figuras da fase 1 (invasão: c1→1 roxo, c0→2 verde, c2→3 laranja).
- [x] Mini-mapa da invasão (33.303 pontos) renderiza em < 2 s, destaca o selecionado, rótulos nos centróides, clique no nó seleciona.
- [x] Lista mostra K cards (100 ou 20 — `/mobilizacao-0709/3` e `/eleicoes/3` têm 20) na ordem do ranking; fantasmas no lugar certo com motivo.
- [x] Card hidratado: autor (ou fallback), hashtags/menções/links clicáveis com offsets certos em texto com emoji (ex.: o tweet "🚨VEJA: Cavalo…" da invasão c0 mostra "Mídia" e nenhum `t.co`), chip de mídia, métricas pt-BR, data de Brasília, link para o X.
- [x] Faixa de pesquisa com posição, RTs de membros, pureza, grafo, evento, razão API e "também em"; tooltips do glossário.
- [x] Ordenar/filtrar/buscar funcionam e o contador reflete.
- [x] `/eleicoes/3` abre c3 de eleicoes (Grupo 5, K=20).
- [x] `vitest` verde; `npm run build` sem erros; `README.md` cobre rodar / dados / atualizar / fora de escopo.
- [x] Erro de dados: renomear temporariamente `data/export/index.json` → a tela mostra "não encontrei data/export/index.json; rode a célula M10 do pipeline_tcc2.ipynb"; restaurar o arquivo.

- [ ] **Step 5: Commit** — *pulado*. `feat(web): leitor de clusters v1 (D15)`; o autor commita após revisar.

---

## Notas de execução (2026-09-15)

- Executado inline na mesma sessão em que o plano foi escrito; nada commitado (o autor revisa e commita).
- Desvios registrados no próprio plano: offset do teste (c) de `entities` (32, não 33); colapso de mídia
  também remove o espaço entre mídias repetidas; `useAsync` guarda a chave do estado (evitava um render
  com `meta` novo e dados do evento anterior). `vitest` resolveu para 4.1.x (não 5.0) — sem efeito.
- Verificação da §9 feita com Playwright + Chromium headless instalados no scratchpad da sessão (bibliotecas
  `libnss3`/`libnspr4`/`libasound2` extraídas localmente, sem `sudo`): redirecionamentos, abas, mini-mapa
  (orientação igual à figura da fase 1; clique em nó e em rótulo; recentrar), 100/20 cards com fantasmas
  no lugar, card com emoji + mídia, faixa com 14 tooltips, toolbar (5 ordenações, filtros, busca com
  debounce, contador, limpar, estado vazio), persistência ao trocar cluster/evento, `/eleicoes/3`,
  estado de erro sem `index.json`, empilhamento a 1000 px, `npm run build` e 25 testes verdes.
- Limitação observada (não coberta pelo spec): rótulos de clusters com centróides próximos podem se
  sobrepor no mini-mapa (Grupo 1 e Grupo 4 de eleicoes); a figura da fase 1 tem anti-sobreposição.
- Dados observados na verificação: eleicoes c1 não tem nenhum slot com pureza ≥ 0,90 ("exclusivos" fica
  vazio); "democracia" casa com todos os 83 tweets hidratados de eleicoes c1 (termo de coleta do evento).

## Ajustes pós-validação com o autor (2026-09-15, mesma data, sessão posterior)

Validação interativa via Chrome DevTools MCP (Chrome for Testing 153 no WSLg, GPU real D3D12/GTX 1070 Ti).
O autor relatou "pequeno delay" ao clicar no mapa e ao aplicar filtros. Medido com Event Timing + long tasks:

| Interação (invasão, 100 slots) | dev antes | dev depois | prod antes | prod depois |
|---|---|---|---|---|
| clique em rótulo do mapa → próximo paint | ~730–790 ms | **248 ms** | long task ~200 ms | **96 ms** |
| tecla na busca (processamento) | 80–500 ms | 25–34 ms | — | 1 ms |
| filtro de status (maior tarefa) | 858–1.093 ms | ~100–180 ms por bloco | ~180 ms | ≤ 50 ms |
| `sigma.refresh()` (33.303 nós) | — | 32–69 ms | — | 31–97 ms |

**Causa raiz:** todos os 100 cards eram re-renderizados a cada mudança de estado (inclusive a cada tecla, porque
`toolbar.query` cru chegava ao `CardList`), e a troca de cluster/filtro **montava** 100 cards (~5.600 elementos DOM,
~800 SVGs de ícones) num único commit — ~200 ms em produção e 700–1.000 ms em dev (React dev + StrictMode). Como o
`navigate()` do React Router é uma transition, o render fatiado não aparece como long task, mas a tela antiga fica
parada até o commit.

**Correções (uma por vez, medindo):**
- A. `TweetCard` e `GhostCard` em `React.memo`; `visible` calculado só do estado efetivo (busca com debounce). Tecla: 3–15× mais barata; troca de cluster inalterada (esperado — são cards novos).
- B. `ProgressiveList` no `CardList`: 12 cards no commit da mudança, +10 por frame (`requestAnimationFrame`), com
  `key` = cluster + ordenação + filtros + busca (qualquer mudança recomeça a lista). Troca de cluster 3× mais rápida em dev.
- `performance.measure("minimap:refresh")` em volta do `sigma.refresh()` fica no código para profiling futuro.
- A spec §4.2 dizia "lista virtualizada não é necessária (≤ 100 cards)": a medição mostrou que montar 100 cards de uma vez é
  perceptível mesmo em produção; a renderização progressiva é o meio-termo sem virtualização.

**Requisito novo do autor:** link "abrir no X" em **todos** os cards → acrescentado ao fim da `ResearchStrip`
(hidratados e fantasmas), apontando para `https://x.com/i/web/status/<tweet_id>`. O ícone no cabeçalho do card hidratado
e o `id` clicável do fantasma continuam.

**Nota:** `npm run dev` roda React em modo de desenvolvimento com StrictMode (render duplo) — 3–4× mais lento que
`npm run build && npm run preview`. Para sessões longas de leitura, o preview é mais fluido.

## Self-review (cobertura do spec)

| Requisito | Task |
|---|---|
| RF1 abas de evento, troca carrega dados e seleciona Grupo 1 | 5 (EventTabs, `eventDefaultPath`), 7 (`useEvent`) |
| RF2 painel de clusters com cor, label, %, peso, K, hidratados, atrição; selecionado evidente; rodapé | 6 |
| RF3 mini-mapa Sigma nós-apenas, cluster na cor, resto cinza, rótulos no centróide, clique seleciona, recentrar | 8 |
| RF4 lista de K cards na ordem do ranking; cabeçalho `Grupo g · K slots · h hidratados · a não devolvidos` | 7 |
| RF5 card estilo X: avatar, nome, handle, selo, data pt-BR/Brasília, texto com entidades, chip mídia, citando/respondendo, métricas abreviadas, idioma, abrir no X, sensível | 7 (TweetCard, TweetText, Avatar), 2, 3 |
| RF6 faixa de pesquisa com tooltips do glossário; cores da pureza | 7 (ResearchStrip), 5 (glossary) |
| RF7 card fantasma com motivo por status, id monoespaçado, link, mesma faixa | 7 (GhostCard) |
| RF8 autor indisponível com motivo por `author_status` + `author_id` | 7 (MissingAuthor) |
| RF9 ordenar (5 opções), filtros de status e exclusividade, busca normalizada com debounce, contador, limpar, estado vazio | 4, 9 |
| RF10 URL `/:evento/:community`; `/` redireciona; slug/community inválidos redirecionam | 5 |
| §4.2 sem backend; local-first; pt-BR; reprodutibilidade (nada computado no front); tipos em um arquivo | 1, 5 |
| §6.1 stack: Vite/React/TS, Tailwind v4 plugin, Sigma v3 + graphology, react-router-dom, lucide-react, Vitest | 1 |
| §6.3 estado derivado da URL; ordenação/filtros/busca locais; cache por slug | 5, 9 |
| §6.4 layout duas colunas ≥ 1280 px (`xl:`), empilha abaixo; sem dark mode | 6 |
| §7.5 algoritmo de entidades (code points, sobreposição, colapso de mídia) | 3 |
| §7.8 formatação | 2 |
| §8 carregando (esqueleto), erro sem retry com mensagem M10, filtros sem resultado, URL inválida, avatar quebrado, busca limpa ao trocar de evento | 5 (States, fetchJson), 7 (Avatar), 9 |
| §9 critérios de aceitação | 10 |
| §10 testes `entities` (a–e) e `format` | 2, 3 (+ `filter` além do mínimo) |
| §12 riscos: code points, orientação, avatares, `n_selected < k`, mesmo tweet em vários clusters (não deduplica), `purity` nulo, não computar no front | 3, 8, 7 (Avatar; cabeçalho usa `n_selected`; `formatDec(null)` → "—") |

**Placeholder scan:** nenhum "TBD/TODO/implementar depois"; todo passo de código tem o código.

**Consistência de nomes:** `segmentText`/`hasMedia` (Task 3) usados em `TweetCard` (Task 7); `applyToolbar`/`DEFAULT_TOOLBAR`/`ToolbarState`/`EXCLUSIVE_MIN_PURITY`/`SHARED_MAX_PURITY` (Task 4) usados em `ResearchStrip`, `Toolbar`, `CardList`, `Reader` (Tasks 7, 9); `useIndex`/`useEvent` e `AsyncState` (Task 5) usados em `App`/`Reader`; `clusterPath`/`eventDefaultPath`/`indexDefaultPath` (Task 5) usados em `App`, `Reader`; `withAlpha` (Task 5) em `ClusterPanel` e `ResearchStrip`; `formatDay` (Task 2) em `EventTabs`; `REFERENCE_TEXT`, `VERIFIED_TYPE_TEXT`, `AUTHOR_STATUS_TEXT`, `SLOT_STATUS_TEXT`, `GLOSSARY`, `EVENT_SHORT_NAMES` (Task 5) nos componentes das Tasks 6–7. `CardList` muda de assinatura entre a Task 7 (`cluster, slots`) e a Task 9 (`+ toolbar, onToolbarChange`) — a Task 9 substitui o arquivo inteiro e o trecho correspondente do `Reader`.
