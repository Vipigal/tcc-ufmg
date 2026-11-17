import type { Slot, Tweet } from "../types";

type ReadySlot = Slot & { tweet: Tweet };

export interface PairComparison {
  onlyA: ReadySlot[];
  onlyB: ReadySlot[];
  both: (ReadySlot & { rtA: number; rtB: number })[];
  counts: { common: number; a: number; b: number };
}

function ready(slot: Slot): slot is ReadySlot {
  return slot.status === "hydrated" && slot.tweet !== null;
}

function topAmplified(slots: Slot[], community: number): ReadySlot[] {
  return slots
    .filter((s) => s.community === community && s.origin === "amplified")
    .filter(ready)
    .sort((x, y) => x.rank - y.rank);
}

/** Tweets lidos (top-K ∪ cauda) de duas bolhas: os que só uma retuitou e os que circularam nas duas. */
export function comparePair(slots: Slot[], a: number, b: number, n: number): PairComparison {
  const idsA = new Set(slots.filter((s) => s.community === a).map((s) => s.tweet_id));
  const rtB = new Map(slots.filter((s) => s.community === b).map((s) => [s.tweet_id, s.rt_cluster]));
  const topA = topAmplified(slots, a);
  const topB = topAmplified(slots, b);
  const both = topA.flatMap((s) => {
    const other = rtB.get(s.tweet_id);
    return other === undefined ? [] : [{ ...s, rtA: s.rt_cluster, rtB: other }];
  });
  return {
    onlyA: topA.filter((s) => !rtB.has(s.tweet_id)).slice(0, n),
    onlyB: topB.filter((s) => !idsA.has(s.tweet_id)).slice(0, n),
    both: both.slice(0, n),
    counts: { common: [...idsA].filter((id) => rtB.has(id)).length, a: idsA.size, b: rtB.size },
  };
}
