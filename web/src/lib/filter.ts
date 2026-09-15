import type { Slot } from "../types";
import { normalize } from "./format";

/** Estado da barra de ferramentas (RF9). Vive fora da URL. */

export type SortKey = "rank" | "purity" | "rt_graph" | "api_retweets" | "date";
export type StatusFilter = "all" | "hydrated" | "ghost";
export type ExclusivityFilter = "all" | "exclusive" | "shared";

export interface ToolbarState {
  sort: SortKey;
  status: StatusFilter;
  exclusivity: ExclusivityFilter;
  query: string;
}

export const DEFAULT_TOOLBAR: ToolbarState = { sort: "rank", status: "all", exclusivity: "all", query: "" };

/** Limiares de leitura do spec §7.6/§7.7 — sinalização, não juízo. */
export const EXCLUSIVE_MIN_PURITY = 0.9;
export const SHARED_MAX_PURITY = 0.5;

export function applyToolbar(slots: Slot[], state: ToolbarState): Slot[] {
  const q = normalize(state.query.trim());
  const filtered = slots.filter((s) => {
    if (state.status === "hydrated" && s.status !== "hydrated") return false;
    if (state.status === "ghost" && s.status === "hydrated") return false;
    if (state.exclusivity === "exclusive" && !(s.purity != null && s.purity >= EXCLUSIVE_MIN_PURITY)) return false;
    if (state.exclusivity === "shared" && !(s.purity != null && s.purity < SHARED_MAX_PURITY)) return false;
    if (q !== "" && !matchesQuery(s, q)) return false;
    return true;
  });
  return sortSlots(filtered, state.sort);
}

function matchesQuery(s: Slot, q: string): boolean {
  const fields = [s.tweet?.text, s.author?.name, s.author?.username];
  return fields.some((f) => typeof f === "string" && normalize(f).includes(q));
}

export function sortSlots(slots: Slot[], sort: SortKey): Slot[] {
  const out = [...slots];
  const byRank = (a: Slot, b: Slot) => a.rank - b.rank;
  switch (sort) {
    case "rank":
      return out.sort(byRank);
    case "purity":
      return out.sort((a, b) => desc(a.purity, b.purity) || byRank(a, b));
    case "rt_graph":
      return out.sort((a, b) => desc(a.rt_graph, b.rt_graph) || byRank(a, b));
    case "api_retweets":
      return out.sort(
        (a, b) => desc(a.tweet?.metrics.retweet_count ?? null, b.tweet?.metrics.retweet_count ?? null) || byRank(a, b),
      );
    case "date":
      return out.sort((a, b) => asc(createdAt(a), createdAt(b)) || byRank(a, b));
  }
}

function createdAt(s: Slot): number | null {
  return s.tweet ? Date.parse(s.tweet.created_at) : null;
}

/** Decrescente; null sempre por último. */
function desc(a: number | null, b: number | null): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return b - a;
}

/** Crescente; null sempre por último. */
function asc(a: number | null, b: number | null): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return a - b;
}
