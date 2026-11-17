import type { ClusterMeta } from "../types";
import { formatInt, formatPct } from "./format";

/** Abaixo disso o grupo é lido como isolado (polos fechados medem 1–3%, fatias 22–77%; D17). */
export const ISOLATED_MAX = 0.1;

const CONCENTRATED_MIN = 0.8;

export function sharePct(x: number): string {
  if (x < 0.01) return "menos de 1%";
  return formatPct(x, x < ISOLATED_MAX ? 1 : 0);
}

function roundPct(x: number): string {
  return x < 0.01 ? "menos de 1%" : formatPct(x);
}

/** Frase do painel da bolha: tamanho e quanto do que ela retuíta circula nas outras. Descreve; não julga. */
export function bubbleSentence(
  c: Pick<ClusterMeta, "n_nodes" | "frac_nodes" | "shared" | "shared_with">,
  labelOf: (community: number) => string,
): string {
  const base = `${formatInt(c.n_nodes)} pessoas, ${formatPct(c.frac_nodes)} do evento.`;
  if (c.shared == null || !c.shared_with) return base;
  if (c.shared < ISOLATED_MAX) return `${base} Só ${roundPct(c.shared)} do que esta bolha retuíta aparece nas outras.`;
  const [partner, frac] = Object.entries(c.shared_with).sort((x, y) => y[1] - x[1])[0];
  const where = frac >= CONCENTRATED_MIN * c.shared ? "quase tudo no" : "mais no";
  return `${base} ${roundPct(c.shared)} do que esta bolha retuíta aparece nas outras, ${where} ${labelOf(Number(partner))}.`;
}

type PairSide = Pick<ClusterMeta, "community" | "label" | "shared_with">;

/** Título e frase da comparação de duas bolhas, pelos dois sentidos de `shared_with`. */
export function pairSummary(a: PairSide, b: PairSide): { title: string; lede: string } {
  const ab = a.shared_with?.[String(b.community)] ?? 0;
  const ba = b.shared_with?.[String(a.community)] ?? 0;
  const isolated = Math.max(ab, ba) < ISOLATED_MAX;
  return {
    title: `${a.label} e ${b.label}${isolated ? ": quase nada em comum" : ""}`,
    lede: `${sharePct(ab)} do que o ${a.label} retuíta circula no ${b.label}, e ${sharePct(ba)} no sentido contrário.`,
  };
}
