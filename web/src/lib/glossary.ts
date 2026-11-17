import type { Axis } from "../types";

export const CONFIDENCE_TEXT: Record<"alta" | "media" | "baixa", string> = {
  alta: "alta",
  media: "média",
  baixa: "baixa",
};

export const AXIS_TEXT: Record<Axis, string> = {
  direita: "Direita",
  esquerda: "Esquerda",
  outro: "Outro",
};

/** Tooltip do selo de verificado por `verified_type`. */
export const VERIFIED_TYPE_TEXT: Record<string, string> = {
  blue: "verificado (assinante)",
  business: "verificado (organização)",
  government: "verificado (governo)",
  none: "verificado",
};
