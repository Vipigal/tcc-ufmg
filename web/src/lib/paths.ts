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
