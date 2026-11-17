import type { EventData, EventMeta, Slot } from "../types";
import { fetchJson } from "./fetchJson";

const cache = new Map<string, Promise<EventData>>();

/** tweets.json de um evento, em memória por slug (voltar ao evento não re-baixa). */
export function loadEvent(meta: EventMeta): Promise<EventData> {
  let pending = cache.get(meta.slug);
  if (!pending) {
    pending = fetchJson<Slot[]>(`/${meta.files.tweets}`)
      .then((slots) => ({ meta, slots }))
      .catch((err: unknown) => {
        cache.delete(meta.slug);
        throw err;
      });
    cache.set(meta.slug, pending);
  }
  return pending;
}
