import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import type { ClusterMeta, EventMeta, Index } from "./types";
import { useEvent, useIndex } from "./data/hooks";
import { DEFAULT_TOOLBAR, type ToolbarState } from "./lib/filter";
import { clusterPath, eventDefaultPath, indexDefaultPath } from "./lib/paths";
import { CardList } from "./components/CardList";
import { ClusterPanel } from "./components/ClusterPanel";
import { EventTabs } from "./components/EventTabs";
import { MiniMap } from "./components/MiniMap";
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
  const event = useEvent(meta);
  const [toolbar, setToolbar] = useState<ToolbarState>(DEFAULT_TOOLBAR);
  // spec §8: trocar de evento mantém ordenação/filtros e limpa a busca; trocar de cluster mantém tudo
  useEffect(() => {
    setToolbar((t) => ({ ...t, query: "" }));
  }, [meta.slug]);
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
          {event.status === "ready" && (
            <CardList cluster={cluster} slots={clusterSlots} toolbar={toolbar} onToolbarChange={setToolbar} />
          )}
        </section>
      </div>
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
