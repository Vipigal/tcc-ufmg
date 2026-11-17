import type { DominantPair, GroupMapGrid, GroupMapLabel } from "../types";
import { formatPct } from "./format";

/** Grupo sob o ponto da imagem (x, y em 0–1, y de cima para baixo); null fora dos grupos. */
export function groupAt(grid: GroupMapGrid, x: number, y: number): number | null {
  const col = Math.min(grid.n - 1, Math.max(0, Math.floor(x * grid.n)));
  const row = Math.min(grid.n - 1, Math.max(0, Math.floor(y * grid.n)));
  const c = grid.cells[row * grid.n + col];
  return c === undefined || c < 0 ? null : c;
}

/** Legenda dos pares dominantes desenhados juntos (D18). */
export function pairNote(pairs: DominantPair[], labelOf: (community: number) => string): string | null {
  if (pairs.length === 0) return null;
  return pairs
    .map((p) => `${labelOf(p.a)} e ${labelOf(p.b)} aparecem juntos: ${formatPct(p.share)} do que um retuíta circula no outro.`)
    .join(" ");
}

const EDGE_X = 0.12;
const EDGE_Y = 0.08;

/** Posição do rótulo dentro do quadro: x preso às bordas; acima/abaixo do ponto conforme couber. */
export function labelPlacement(g: Pick<GroupMapLabel, "label_x" | "label_y" | "anchor">): {
  x: number;
  y: number;
  anchor: GroupMapLabel["anchor"];
} {
  const x = Math.min(1 - EDGE_X, Math.max(EDGE_X, g.label_x));
  const anchor = g.anchor === "bottom" && g.label_y < EDGE_Y ? "top" : g.anchor === "top" && g.label_y > 1 - EDGE_Y ? "bottom" : g.anchor;
  return { x, y: g.label_y, anchor };
}
