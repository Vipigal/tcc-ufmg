import type { Slot, SlotOrigin, Tweet } from "../types";

export type ThreadItem =
  | { kind: "tweet"; label: string; slot: Slot & { tweet: Tweet } }
  | { kind: "gap"; labels: string[] };

/** Rótulo do tweet na bolha: "7" no ranking dos mais retuitados, "C2" nos característicos. */
export function slotLabel(slot: Pick<Slot, "rank" | "origin">): string {
  return slot.origin === "characteristic" ? `C${slot.rank}` : String(slot.rank);
}

export function gapText(labels: string[]): string {
  if (labels.length === 1) return `A posição ${labels[0]} foi apagada ou vem de conta suspensa.`;
  const joined =
    labels.length === 2 ? `${labels[0]} e ${labels[1]}` : `${labels[0]} a ${labels[labels.length - 1]}`;
  return `As posições ${joined} foram apagadas ou vêm de contas suspensas.`;
}

function hasTweet(slot: Slot): slot is Slot & { tweet: Tweet } {
  return slot.status === "hydrated" && slot.tweet !== null;
}

/** Tweets de um grupo e origem na ordem do ranking; indisponíveis seguidos viram um aviso só. */
export function buildThread(slots: Slot[], community: number, origin: SlotOrigin): ThreadItem[] {
  const mine = slots.filter((s) => s.community === community && s.origin === origin).sort((a, b) => a.rank - b.rank);
  const out: ThreadItem[] = [];
  for (const s of mine) {
    const label = slotLabel(s);
    if (hasTweet(s)) {
      out.push({ kind: "tweet", label, slot: s });
      continue;
    }
    const prev = out[out.length - 1];
    if (prev && prev.kind === "gap") prev.labels.push(label);
    else out.push({ kind: "gap", labels: [label] });
  }
  return out;
}
