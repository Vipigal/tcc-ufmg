import type { Axis, ClusterSummary } from "../types";
import { CONFIDENCE_TEXT, GLOSSARY } from "../lib/glossary";

const STYLE: Record<Axis, string> = {
  direita: "bg-axis-right text-white",
  esquerda: "bg-axis-left text-white",
  outro: "bg-axis-other text-black",
};

interface Props {
  eixo: Axis;
  confianca?: ClusterSummary["inclinacao_politica"]["confianca"];
  compact?: boolean;
}

/** Tag de inclinação (spec 2026-10-14 §3.2): eixo atribuído pelo autor a partir da leitura do LLM. */
export function InclinationTag({ eixo, confianca, compact = false }: Props) {
  return (
    <span
      title={GLOSSARY.axis_tag}
      className={`inline-flex cursor-help items-center gap-1 whitespace-nowrap rounded-full font-bold ${STYLE[eixo]} ${
        compact ? "px-1.5 text-[10px]" : "px-2 py-px text-[11.5px]"
      }`}
    >
      {compact ? eixo.slice(0, 3) + "." : eixo}
      {!compact && (
        <span className="font-medium opacity-80">
          · LLM{confianca ? ` · confiança ${CONFIDENCE_TEXT[confianca]}` : ""}
        </span>
      )}
    </span>
  );
}
