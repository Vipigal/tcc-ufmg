import type { ClusterMeta } from "../types";

/** Abaixo disso o grupo é lido como isolado (polos fechados medem 1–3%, fatias 22–77%; D17). */
export const ISOLATED_MAX = 0.1;

/** Frase da barra de conteúdo compartilhado (spec 2026-10-14 §2.1). Descreve; não julga. */
export function sharedPhrase(
  c: Pick<ClusterMeta, "shared" | "shared_with">,
  labelOf: (community: number) => string,
): { text: string; partner: number | null } | null {
  if (c.shared == null || !c.shared_with) return null;
  if (c.shared < ISOLATED_MAX) return { text: "quase nada em comum com os outros grupos", partner: null };
  const [partner, frac] = Object.entries(c.shared_with).sort((x, y) => y[1] - x[1])[0];
  return {
    text: `mais em comum com o ${labelOf(Number(partner))} (${Math.round(frac * 100)}% do que retuíta)`,
    partner: Number(partner),
  };
}
