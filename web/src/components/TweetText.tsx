import type { Segment } from "../lib/entities";

/** Renderiza os segmentos de `segmentText`: texto puro, hashtag/menção/url/mídia como links em nova aba. */
export function TweetText({ segments }: { segments: Segment[] }) {
  return (
    <p className="whitespace-pre-wrap break-words text-[15px] leading-5 text-ink">
      {segments.map((s, i) =>
        s.kind === "text" ? (
          <span key={i}>{s.text}</span>
        ) : (
          <a key={i} href={s.href} target="_blank" rel="noopener noreferrer" className="text-x-blue hover:underline">
            {s.text}
          </a>
        ),
      )}
    </p>
  );
}
