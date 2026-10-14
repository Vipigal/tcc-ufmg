import type { ClusterMeta } from "../types";
import { formatPct } from "../lib/format";
import { GLOSSARY } from "../lib/glossary";
import { sharedPhrase } from "../lib/shared";

interface Props {
  cluster: ClusterMeta;
  labelOf: (community: number) => string;
}

/** Barra de conteúdo compartilhado (D17) + frase de leitura. */
export function SharedBar({ cluster, labelOf }: Props) {
  const phrase = sharedPhrase(cluster, labelOf);
  if (!phrase || cluster.shared == null) return null;
  return (
    <div title={GLOSSARY.shared} className="cursor-help">
      <div className="flex items-center gap-2 text-[11.5px] text-muted">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line">
          <div
            className="h-full rounded-full"
            style={{ width: `${Math.max(cluster.shared * 100, 1.5)}%`, backgroundColor: cluster.color }}
          />
        </div>
        <span className="tabular-nums">{formatPct(cluster.shared)} compartilhado</span>
      </div>
      <div className="mt-0.5 text-[12px] text-muted">{phrase.text}</div>
    </div>
  );
}
