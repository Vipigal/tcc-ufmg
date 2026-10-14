import type { EventMeta, Index } from "../types";

/** Rotas (spec 2026-10-14 §2): visão geral, leitor do grupo e comparação. */
export type Mode = "overview" | "reader" | "compare";

export function overviewPath(slug: string): string {
  return `/${slug}`;
}

export function clusterPath(slug: string, community: number): string {
  return `/${slug}/${community}`;
}

export function comparePath(slug: string, a: number, b: number): string {
  return `/${slug}/comparar/${a}/${b}`;
}

/** Entrada do evento = visão geral. */
export function eventDefaultPath(meta: EventMeta): string {
  return overviewPath(meta.slug);
}

export function indexDefaultPath(index: Index): string {
  return eventDefaultPath(index.events[0]);
}

/** Mesmo modo em outro evento: grupo 1 no leitor; grupos 1 e 2 na comparação. */
export function pathForMode(mode: Mode, meta: EventMeta, a?: number, b?: number): string {
  const first = meta.clusters[0]?.community ?? 0;
  const second = meta.clusters[1]?.community ?? first;
  const has = (c?: number) => c !== undefined && meta.clusters.some((x) => x.community === c);
  if (mode === "reader") return clusterPath(meta.slug, has(a) ? a! : first);
  if (mode === "compare") {
    const x = has(a) ? a! : first;
    const y = has(b) && b !== x ? b! : x === first ? second : first;
    return comparePath(meta.slug, x, y);
  }
  return overviewPath(meta.slug);
}
