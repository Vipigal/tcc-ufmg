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
