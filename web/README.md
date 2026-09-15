# Leitor de clusters (web/)

Primeiro módulo da aplicação web do TCC (D9, D15): lê `data/export/` e mostra, por evento e
cluster, o mini-mapa DRL e os top-K tweets em cards estilo X com a faixa de metadados da pesquisa.
Spec: `docs/superpowers/specs/2026-09-15-leitor-de-clusters-design.md` · plano de implementação:
`docs/superpowers/plans/2026-09-15-leitor-de-clusters.md`.

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
para o padrão do evento (ou do índice). Ordenação, filtros e busca ficam fora da URL.

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
Se `data/export/` não existir, a tela mostra o erro e pede a célula M10 — não há retry automático.

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
  as coordenadas do DRL entram sem inversão (conferido contra
  `data/processed/invasao-3-poderes/grafo-invasao-drl.png`).
- Avatares vêm de `pbs.twimg.com` e podem falhar (conta suspensa, imagem removida); o fallback
  são as iniciais sobre a cor do grupo.
- Tooltips são o atributo `title` nativo (passar o mouse e esperar).
- `vercel.json` só faz o rewrite da SPA; deploy está fora do escopo da v1.

## Desempenho

- Cards são memoizados e a lista é montada progressivamente (12 no commit, +10 por frame), porque montar 100 cards de
  uma vez custava ~200 ms em produção e ~1 s em dev (medido em 2026-09-15). Ajustes em `CardList.tsx`
  (`INITIAL_CARDS`, `CARDS_PER_FRAME`).
- `npm run dev` usa React em modo de desenvolvimento com StrictMode (render duplo): 3–4× mais lento que a build.
  Para ler por horas, `npm run build && npm run preview` (porta 4173) é mais fluido.
- O recolorir do mini-mapa (`sigma.refresh()` sobre ~33 mil nós) custa 30–70 ms e está medido em
  `performance.getEntriesByName("minimap:refresh")` no DevTools.

## Fora de escopo (v1)

Anotações ou rótulos manuais; grafo com arestas; filtro temporal; painel de síntese narrativa;
comparação lado a lado de dois clusters; hidratação de mídia (o chip "Mídia" abre o tweet no X);
tweets citados com texto; autenticação; dark mode; deploy.
