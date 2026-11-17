# Polarização no Twitter brasileiro — leitor de clusters (web/)

Primeiro módulo da aplicação web do TCC (D9, D15): lê `data/export/` e mostra, por evento e
cluster, o mini-mapa DRL e os top-K tweets em cards estilo X com a faixa de metadados da pesquisa.
Spec: `docs/superpowers/specs/2026-09-15-leitor-de-clusters-design.md` · plano de implementação:
`docs/superpowers/plans/2026-09-15-leitor-de-clusters.md`. A v2 (visão geral, comparação, sínteses por
LLM, mídias, tema escuro) está em `docs/superpowers/specs/2026-10-14-visao-geral-comparacao-design.md`.
A v3 (2026-11-17) segue o protótipo **E** do redesign (`C:\Users\vinic\Documents\redesign-leitor-propostas\E-*.html`):
abertura com os quatro eventos, "como as bolhas se formam" e a página do evento com a bolha aberta logo abaixo.
Na página do evento, o grafo de grupos (M12, D18): imagem gerada no pipeline com os grupos clicáveis; cores da paleta sem azul e vermelho, e a cor da inclinação só aparece depois de abrir um grupo (D8, adendo de 2026-11-17).

## Rodar

```bash
cd web
npm install
npm run dev        # http://localhost:5173 → abertura com os quatro eventos
npm test           # vitest: lib/citations, compare, entities, format, groupMap, paths, shared, theme, thread, timeline
npm run build      # tsc -b + vite build → dist/ (inclui uma cópia de data/export/)
```

Rotas: `/` (os quatro eventos); `/como-funciona` (a animação em quatro passos); `/:evento` (bolhas do dia,
com a maior aberta); `/:evento/:community` (bolha aberta, ex.: `/eleicoes/3`; aceita `?comparar=<community>`).
Slug inválido volta para `/`; community inválida abre a primeira bolha. `?tags=0` oculta a inclinação e
deixa o painel neutro (D8). Tema escuro por padrão, lembrado em `localStorage`.

## De onde vêm os dados

`vite.config.ts` aponta `publicDir` para `../data/export`, então o app faz `fetch("/index.json")`,
`fetch("/<slug>/tweets.json")` — JSON estático, sem backend. O `layout.json` (DRL) continua exportado,
mas o leitor não o usa desde a v3. O grafo de cada evento vem da célula M12 (`modules/group_map.py`):
`grafo-claro.webp`, `grafo-escuro.webp`, as miniaturas `*-mini.webp` e `grafo.json` (rótulos + grade de
clique); sem eles, a página do evento avisa e segue funcionando. Os textos de contexto dos eventos, com fontes, ficam em
`src/content/events.ts`.
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
- `src/content/events.ts` — contexto factual de cada evento (texto, fontes, data curta), marcos da linha do
  tempo e mídias omitidas de propósito (ex.: colagem de rostos para identificar pessoas).
- `src/lib/` — utilitários puros: `groupMap` (clique na imagem → grupo; legenda dos pares dominantes), `timeline`, `citations` (síntese → trechos e `[id]`), `thread` (ranking → thread, com
  posições indisponíveis agrupadas), `compare` (só A / nas duas / só B), `shared` (frases do painel e da
  comparação), `palette` (cores dos grupos e do eixo), `format`, `entities`, `paths`, `nav`,
  `theme`, `glossary`.
- `src/components/` — `Timeline`, `EventGraph` e `GraphStage` (grafo clicável do evento),
  `GroupPanel` (bolha aberta), `CitedText`, `Comparison`, `TweetThread` e `ThreadTweet`, `OverlapDemo`
  (animação), `Avatar`, `MediaGrid`, `TweetText`, `States`.
- `src/pages/` — `Home` (os quatro eventos), `HowItWorks` (como as bolhas se formam), `EventPage`.
- `src/App.tsx` — tema, cabeçalho (`PageFrame`) e `WithIndex`; rotas em `src/main.tsx`.

## Notas

- O grafo é apresentação (D18): o layout e os cortes de arestas não entram em nenhuma medida.
- Cores: grupos em `--group-*` (roxo, verde, laranja, amarelo, marrom); a cor do eixo da curadoria (`--right-*`, `--left-*`,
  `--other-*`) aparece só no painel, na thread e na comparação, e some com `?tags=0`.
- Citações da síntese viram números ("7" no ranking, "C2" nos característicos) que trocam a aba, abrem
  mais tweets se preciso e centralizam o tweet. Id citado fora dos tweets lidos da bolha aparece como "?" riscado.
- Avatares vêm de `pbs.twimg.com` e podem falhar (conta suspensa, imagem removida); o fallback
  são as iniciais.
- Deploy (projeto Vercel `leitor-de-clusters`, já vinculado em `web/.vercel/`): o `publicDir` aponta
  para fora de `web/`, então a build é local e o upload é do resultado pronto:
  `vercel build --prod && vercel deploy --prebuilt --prod` (dentro de `web/`). `vercel.json` só faz o
  rewrite da SPA.

## Desempenho

- A thread monta 20 tweets por vez ("Mostrar mais"); tweets são memoizados.
- `npm run dev` usa React em modo de desenvolvimento com StrictMode (render duplo): 3–4× mais lento que a build.
  Para ler por horas, `npm run build && npm run preview` (porta 4173) é mais fluido.

## Fora de escopo (v1)

Anotações ou rótulos manuais; grafo com arestas; filtro temporal; painel de síntese narrativa;
comparação lado a lado de dois clusters; hidratação de mídia (o chip "Mídia" abre o tweet no X);
tweets citados com texto; autenticação; dark mode; deploy.
