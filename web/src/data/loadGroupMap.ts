import type { GroupMap } from "../types";
import { fetchJson } from "./fetchJson";

const cache = new Map<string, Promise<GroupMap>>();

/** `grafo.json` do evento (M12), em memória por slug. */
export function loadGroupMap(slug: string): Promise<GroupMap> {
  let pending = cache.get(slug);
  if (!pending) {
    pending = fetchJson<GroupMap>(`/${slug}/grafo.json`).catch((err: unknown) => {
      cache.delete(slug);
      throw err;
    });
    cache.set(slug, pending);
  }
  return pending;
}
