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
