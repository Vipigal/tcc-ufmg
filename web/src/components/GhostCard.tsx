import { memo } from "react";
import { ExternalLink, TriangleAlert } from "lucide-react";
import type { Slot } from "../types";
import { SLOT_STATUS_TEXT } from "../lib/glossary";
import { ResearchStrip } from "./ResearchStrip";

interface Props {
  slot: Slot;
  color: string;
}

/** RF7: slot não devolvido pela API — mesmo lugar na lista, borda tracejada, motivo e link para o X. Memoizado como o TweetCard. */
export const GhostCard = memo(function GhostCard({ slot, color }: Props) {
  const title =
    slot.status === "error"
      ? (slot.error?.title ?? SLOT_STATUS_TEXT.error)
      : slot.status === "hydrated"
        ? "Tweet sem conteúdo no export"
        : SLOT_STATUS_TEXT[slot.status];
  return (
    <article className="overflow-hidden rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50/60">
      <div className="flex items-center gap-3 px-4 py-3 text-muted">
        <TriangleAlert size={20} className="shrink-0" />
        <div className="min-w-0 flex-1 text-[14px]">
          <div className="font-semibold text-ink/80" title={slot.error?.detail ?? undefined}>
            {title}
          </div>
          <a
            href={`https://x.com/i/web/status/${slot.tweet_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-mono text-[12.5px] hover:text-x-blue hover:underline"
          >
            id {slot.tweet_id} <ExternalLink size={12} />
          </a>
        </div>
      </div>
      <ResearchStrip slot={slot} color={color} />
    </article>
  );
});
