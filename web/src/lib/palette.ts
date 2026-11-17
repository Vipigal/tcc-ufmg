import type { Axis } from "../types";

const GROUP_TONES = 5;

/** Cor do grupo pela ordem (roxo, verde, laranja, amarelo, marrom): só identifica o grupo, sem sugerir lado. */
export function groupColor(group: number): string {
  return `var(--group-${((group - 1) % GROUP_TONES) + 1})`;
}

export interface AxisColors {
  ink: string;
  tint: string;
  line: string;
}

const NEUTRAL: AxisColors = { ink: "var(--ink)", tint: "var(--soft)", line: "var(--line-strong)" };

const AXIS_PREFIX: Record<Axis, string> = { direita: "right", esquerda: "left", outro: "other" };

/** Cores do painel pela inclinação curada; neutras sem curadoria ou com `?tags=0`. */
export function axisColors(eixo: Axis | null): AxisColors {
  if (eixo === null) return NEUTRAL;
  const p = AXIS_PREFIX[eixo];
  return { ink: `var(--${p}-ink)`, tint: `var(--${p}-tint)`, line: `var(--${p}-line)` };
}

/** Inclinação que a tela mostra: a curada, salvo com `?tags=0`. */
export function shownAxis(cluster: { curation: { eixo: Axis } | null }, showTags: boolean): Axis | null {
  return showTags ? (cluster.curation?.eixo ?? null) : null;
}
