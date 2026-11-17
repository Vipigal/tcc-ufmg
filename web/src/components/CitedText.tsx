import { Fragment } from "react";
import { splitCitations } from "../lib/citations";

interface Props {
  text: string;
  labels: Map<string, string>;
  onCite: (tweetId: string) => void;
}

const CHIP =
  "mx-0.5 inline-grid h-6 min-w-6 place-items-center rounded-xl px-1.5 align-[2px] text-[13px] font-extrabold no-underline";

/** Texto da síntese com as citações `[id]` como números que levam ao tweet na thread. */
export function CitedText({ text, labels, onCite }: Props) {
  return (
    <>
      {splitCitations(text).map((seg, i) =>
        seg.kind === "text" ? (
          <Fragment key={i}>{seg.text}</Fragment>
        ) : (
          seg.ids.map((id) => {
            const label = labels.get(id);
            if (!label)
              return (
                <span key={`${i}-${id}`} title="tweet indisponível ou fora dos tweets lidos desta bolha" className={`${CHIP} bg-chip text-faint line-through`}>
                  ?
                </span>
              );
            return (
              <a
                key={`${i}-${id}`}
                href={`https://x.com/i/web/status/${id}`}
                onClick={(e) => {
                  e.preventDefault();
                  onCite(id);
                }}
                className={`${CHIP} bg-line text-ink hover:bg-ink hover:text-bg`}
              >
                {label}
              </a>
            );
          })
        ),
      )}
    </>
  );
}
