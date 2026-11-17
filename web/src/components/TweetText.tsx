import type { Segment } from "../lib/entities";

/** Renderiza os segmentos de `segmentText`: texto puro, hashtag/menção/url/mídia como links em nova aba. */
export function TweetText({ segments }: { segments: Segment[] }) {
  return (
    <p className="m-0 mt-1 mb-3 text-[17px] leading-normal break-words whitespace-pre-wrap text-ink">
      {segments.map((s, i) =>
        s.kind === "text" ? (
          <span key={i}>{s.text}</span>
        ) : (
          <a key={i} href={s.href} target="_blank" rel="noopener noreferrer" className="text-x-blue no-underline hover:underline">
            {s.text}
          </a>
        ),
      )}
    </p>
  );
}
