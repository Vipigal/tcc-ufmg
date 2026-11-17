import { useEffect, useMemo, useRef, useState } from "react";
import type { Slot, SlotOrigin } from "../types";
import type { AxisColors } from "../lib/palette";
import { buildThread, gapText } from "../lib/thread";
import { ThreadAvatar, ThreadTweet } from "./ThreadTweet";

interface Props {
  slots: Slot[];
  community: number;
  origin: SlotOrigin;
  onOrigin: (origin: SlotOrigin) => void;
  colors: AxisColors;
  focus: { tweetId: string; seq: number } | null;
}

const PAGE = 20;
const SETTLE_MS = [200, 600, 1200];

const HELP: Record<SlotOrigin, string> = {
  amplified: "Do mais retuitado para o menos, entre as pessoas desta bolha.",
  characteristic:
    "Característicos são tweets que apareceram nesta bolha e quase não apareceram nas outras. Não estão entre os mais retuitados, mas mostram o que é próprio dela.",
};

const TABS: { origin: SlotOrigin; label: string }[] = [
  { origin: "amplified", label: "Mais retuitados" },
  { origin: "characteristic", label: "Característicos" },
];

const threadAnchor = (community: number, tweetId: string) => `tweet-${community}-${tweetId}`;

/** Os tweets da bolha em thread, na ordem do ranking; citações da síntese rolam até eles. */
export function TweetThread({ slots, community, origin, onOrigin, colors, focus }: Props) {
  const items = useMemo(() => buildThread(slots, community, origin), [slots, community, origin]);
  const [limit, setLimit] = useState(PAGE);
  const [pending, setPending] = useState<{ tweetId: string; seq: number } | null>(null);
  const handled = useRef(0);
  const timers = useRef<number[]>([]);
  useEffect(() => setLimit(PAGE), [community, origin]);
  useEffect(() => () => timers.current.forEach((t) => window.clearTimeout(t)), []);

  useEffect(() => {
    if (!focus) return;
    const at = items.findIndex((it) => it.kind === "tweet" && it.slot.tweet_id === focus.tweetId);
    if (at < 0) return;
    setLimit((l) => Math.max(l, at + 1));
    setPending(focus);
  }, [focus, items]);

  useEffect(() => {
    if (!pending || pending.seq === handled.current) return;
    const el = document.getElementById(threadAnchor(community, pending.tweetId));
    if (!el) return;
    handled.current = pending.seq;
    timers.current.forEach((t) => window.clearTimeout(t));
    const center = () => el.scrollIntoView({ block: "center" });
    center();
    el.classList.add("cite-flash");
    timers.current = [
      ...SETTLE_MS.map((ms) => window.setTimeout(center, ms)),
      window.setTimeout(() => el.classList.remove("cite-flash"), 1600),
    ];
  }, [pending, limit, community]);

  const shown = items.slice(0, limit);
  return (
    <section className="mt-14 max-w-[720px]">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <h3 className="m-0 mr-auto text-[30px] font-extrabold tracking-[-0.02em]">Os tweets</h3>
        <div role="tablist" aria-label="Ordenar" className="flex gap-1 rounded-full bg-chip p-1">
          {TABS.map((t) => (
            <button
              key={t.origin}
              type="button"
              role="tab"
              aria-selected={origin === t.origin}
              onClick={() => onOrigin(t.origin)}
              className={`min-h-10 cursor-pointer rounded-full border-0 px-4 text-[15px] ${
                origin === t.origin ? "bg-ink font-bold text-bg" : "bg-transparent text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <p className="m-0 mt-3 text-[16px] leading-[1.55] text-muted">{HELP[origin]}</p>

      <ol className="m-0 mt-2 list-none p-0">
        {shown.length === 0 && <li className="pt-5 text-[16px] text-muted">Esta bolha não tem tweets nesta lista.</li>}
        {shown.map((it, i) => (
          <li
            key={it.kind === "tweet" ? it.slot.tweet_id : `gap-${it.labels[0]}`}
            id={it.kind === "tweet" ? threadAnchor(community, it.slot.tweet_id) : undefined}
            className="grid grid-cols-[48px_minmax(0,1fr)] gap-x-3 pt-[18px]"
          >
            <div className="flex flex-col items-center">
              {it.kind === "tweet" ? <ThreadAvatar slot={it.slot} /> : <span aria-hidden className="size-12 rounded-full bg-line" />}
              <span
                aria-hidden
                className="mt-1 w-0.5 flex-1"
                style={{ background: i === shown.length - 1 ? "transparent" : colors.line }}
              />
            </div>
            <div className="min-w-0 border-b border-line pb-5">
              {it.kind === "tweet" ? (
                <ThreadTweet slot={it.slot} label={it.label} colors={colors} />
              ) : (
                <div className="rounded-2xl bg-chip px-4 py-3 text-[15px] text-muted">{gapText(it.labels)}</div>
              )}
            </div>
          </li>
        ))}
      </ol>
      {items.length > limit && (
        <button
          type="button"
          onClick={() => setLimit((l) => l + PAGE)}
          className="mt-5 min-h-11 cursor-pointer rounded-full border-0 bg-chip px-5 text-[15px] font-bold text-ink"
        >
          Mostrar mais {Math.min(PAGE, items.length - limit)}
        </button>
      )}
      <p className="m-0 mt-5 text-[13px] text-muted">
        Respostas, retweets, curtidas e visualizações são os totais públicos de cada tweet, consultados em 2026. A faixa
        colorida mostra quantas pessoas desta bolha retuitaram.
      </p>
    </section>
  );
}
