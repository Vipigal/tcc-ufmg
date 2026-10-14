import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, useLocation, useParams } from "react-router-dom";
import type { ClusterMeta, EventData, EventMeta, Index } from "./types";
import { useEvent, useIndex } from "./data/hooks";
import { lighten } from "./lib/color";
import { DEFAULT_TOOLBAR, type OriginFilter, type ToolbarState } from "./lib/filter";
import { useNav } from "./lib/nav";
import { clusterPath, eventDefaultPath, indexDefaultPath, pathForMode, type Mode } from "./lib/paths";
import { ThemeContext, applyTheme, browserStorage, readTheme, useTheme, writeTheme, type Theme } from "./lib/theme";
import { CardList } from "./components/CardList";
import { ClusterPanel } from "./components/ClusterPanel";
import { EventTabs } from "./components/EventTabs";
import { ModeSwitch, ThemeToggle } from "./components/HeaderControls";
import { MiniMap } from "./components/MiniMap";
import { ErrorBox, Skeleton } from "./components/States";
import { Compare } from "./pages/Compare";
import { Overview } from "./pages/Overview";

/** Clareamento das cores dos grupos no tema escuro (spec 2026-10-14 §2.4). */
const DARK_LIGHTEN = 0.28;

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => readTheme(browserStorage));
  useEffect(() => {
    applyTheme(theme);
    writeTheme(browserStorage, theme);
  }, [theme]);
  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  const value = useMemo(() => ({ theme, toggle }), [theme, toggle]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/** `/` → visão geral do primeiro evento. */
export function RootRedirect() {
  const index = useIndex();
  if (index.status === "loading") return <PageFrame><Skeleton className="h-40" /></PageFrame>;
  if (index.status === "error") return <PageFrame><ErrorBox error={index.error} /></PageFrame>;
  return <Navigate to={indexDefaultPath(index.data)} replace />;
}

export default function App({ mode }: { mode: Mode }) {
  return (
    <ThemeProvider>
      <Routed mode={mode} />
    </ThemeProvider>
  );
}

/** Valida os parâmetros da rota e delega à tela. */
function Routed({ mode }: { mode: Mode }) {
  const { evento, community, a, b } = useParams();
  const index = useIndex();
  if (index.status === "loading") return <PageFrame><Skeleton className="h-40" /></PageFrame>;
  if (index.status === "error") return <PageFrame><ErrorBox error={index.error} /></PageFrame>;

  const meta = index.data.events.find((e) => e.slug === evento);
  if (!meta) return <Navigate to={indexDefaultPath(index.data)} replace />;
  const find = (c?: string) => meta.clusters.find((x) => String(x.community) === c);
  if (mode === "reader" && !find(community)) return <Navigate to={eventDefaultPath(meta)} replace />;
  if (mode === "compare" && (!find(a) || !find(b) || a === b))
    return <Navigate to={pathForMode("compare", meta)} replace />;

  return <Shell index={index.data} rawMeta={meta} mode={mode} community={community} a={a} b={b} />;
}

interface ShellProps {
  index: Index;
  rawMeta: EventMeta;
  mode: Mode;
  community?: string;
  a?: string;
  b?: string;
}

function Shell({ index, rawMeta, mode, community, a, b }: ShellProps) {
  const nav = useNav();
  const { theme } = useTheme();
  // cores dos grupos clareadas no escuro, num só lugar (mapa, cartões, cards e barras herdam daqui)
  const meta = useMemo<EventMeta>(
    () =>
      theme === "dark"
        ? { ...rawMeta, clusters: rawMeta.clusters.map((c) => ({ ...c, color: lighten(c.color, DARK_LIGHTEN) })) }
        : rawMeta,
    [rawMeta, theme],
  );
  const event = useEvent(rawMeta);
  const find = (c?: string) => meta.clusters.find((x) => String(x.community) === c);
  const labelOf = useCallback(
    (c: number) => {
      const known = meta.clusters.find((x) => x.community === c);
      if (known) return known.label;
      const g = event.status === "ready" ? event.data.layout.groups[String(c)] : undefined;
      return g ? `Grupo ${g} (< 1%)` : `c${c}`;
    },
    [meta, event],
  );

  const current = mode === "reader" ? Number(community) : mode === "compare" ? Number(a) : undefined;
  const other = mode === "compare" ? Number(b) : undefined;
  const selectEvent = (e: EventMeta) => nav(pathForMode(mode, e, current, other));
  const selectMode = (m: Mode) => nav(pathForMode(m, meta, current, other));

  return (
    <PageFrame
      header={
        <>
          <EventTabs events={index.events} activeSlug={meta.slug} onSelect={selectEvent} />
          <div className="ml-auto flex items-center gap-2">
            <ModeSwitch mode={mode} onSelect={selectMode} />
            <ThemeToggle />
          </div>
        </>
      }
    >
      {event.status === "loading" && <Skeleton className="h-[420px]" />}
      {event.status === "error" && <ErrorBox error={event.error} />}
      {event.status === "ready" && mode === "overview" && <Overview meta={meta} data={event.data} labelOf={labelOf} />}
      {event.status === "ready" && mode === "compare" && (
        <Compare meta={meta} data={event.data} a={find(a)!} b={find(b)!} labelOf={labelOf} />
      )}
      {event.status === "ready" && mode === "reader" && <Reader meta={meta} data={event.data} cluster={find(community)!} />}
    </PageFrame>
  );
}

/** Leitor do grupo (o leitor original: mini-mapa, lista de grupos, síntese e thread de tweets). */
function Reader({ meta, data, cluster }: { meta: EventMeta; data: EventData; cluster: ClusterMeta }) {
  const nav = useNav();
  const location = useLocation();
  const [toolbar, setToolbar] = useState<ToolbarState>(DEFAULT_TOOLBAR);
  // `?origem=` (vindo do "ver todos" da comparação) define o filtro de origem
  useEffect(() => {
    const o = new URLSearchParams(location.search).get("origem");
    if (o === "amplified" || o === "characteristic") setToolbar((t) => ({ ...t, origin: o as OriginFilter }));
  }, [location.search]);
  // trocar de evento limpa a busca
  useEffect(() => {
    setToolbar((t) => ({ ...t, query: "" }));
  }, [meta.slug]);
  const selectCluster = (c: number) => nav(clusterPath(meta.slug, c));
  const slots = useMemo(() => data.slots.filter((s) => s.community === cluster.community), [data, cluster.community]);

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[400px_minmax(0,1fr)]">
      <aside className="space-y-4 xl:sticky xl:top-[61px] xl:self-start">
        <MiniMap layout={data.layout} clusters={meta.clusters} selected={cluster.community} onSelect={selectCluster} />
        <ClusterPanel event={meta} selected={cluster.community} onSelect={selectCluster} />
      </aside>
      <section className="min-w-0">
        <CardList cluster={cluster} slots={slots} toolbar={toolbar} onToolbarChange={setToolbar} />
      </section>
    </div>
  );
}

export function PageFrame({ header, children }: { header?: ReactNode; children: ReactNode }) {
  return (
    <div className="min-h-full bg-bg text-ink">
      <header className="sticky top-0 z-20 border-b border-line bg-bg/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-1 px-4 py-2">
          <h1 className="text-[17px] font-bold tracking-tight">Leitor de clusters</h1>
          {header}
        </div>
      </header>
      <main className="mx-auto max-w-[1600px] px-4 py-4">{children}</main>
    </div>
  );
}
