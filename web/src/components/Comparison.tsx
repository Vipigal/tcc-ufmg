import { useEffect, useMemo, useRef } from "react";
import type { ClusterMeta, Slot, Tweet } from "../types";
import { comparePair } from "../lib/compare";
import { formatInt } from "../lib/format";
import { axisColors, shownAxis } from "../lib/palette";
import { pairSummary } from "../lib/shared";

interface Props {
  slots: Slot[];
  a: ClusterMeta;
  b: ClusterMeta;
  showTags: boolean;
}

const PER_COLUMN = 2;
const TCO = /https:\/\/t\.co\/\S+/g;

function Item({ slot, stat, muted }: { slot: Slot & { tweet: Tweet }; stat: string; muted?: boolean }) {
  return (
    <li className={`rounded-[20px] px-4 py-3.5 text-ink ${muted ? "bg-soft" : "bg-bg"}`}>
      <div className="text-[14px]">
        <b>{slot.author?.name ?? "Autor indisponível"}</b>{" "}
        {slot.author?.username && <span className="text-faint">@{slot.author.username}</span>}
      </div>
      <p className="my-1.5 line-clamp-4 text-[15px] leading-[1.45] whitespace-pre-line">{slot.tweet.text.replace(TCO, "").trim()}</p>
      <div className="text-[13px] text-muted">{stat}</div>
    </li>
  );
}

/** Duas bolhas lado a lado: o que só uma retuitou e o que circulou nas duas. */
export function Comparison({ slots, a, b, showTags }: Props) {
  const pair = useMemo(() => comparePair(slots, a.community, b.community, PER_COLUMN), [slots, a.community, b.community]);
  const { title, lede } = pairSummary(a, b);
  const ca = axisColors(shownAxis(a, showTags));
  const cb = axisColors(shownAxis(b, showTags));
  const column = "rounded-[28px] p-[22px]";
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    ref.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }, [a.community, b.community]);
  return (
    <section ref={ref} className="mt-12 scroll-mt-6">
      <h3 className="m-0 mb-1.5 text-[30px] font-extrabold tracking-[-0.02em]">{title}</h3>
      <p className="m-0 mb-5 max-w-[44em] text-[17px] leading-normal text-muted">
        {lede} {formatInt(pair.counts.common)} dos tweets lidos de cada bolha ({formatInt(pair.counts.a)} e{" "}
        {formatInt(pair.counts.b)}) aparecem nas duas.
      </p>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] items-start gap-4">
        <div className={column} style={{ background: ca.tint, color: ca.ink }}>
          <h4 className="m-0 mb-3 text-[18px] font-extrabold">Só no {a.label}</h4>
          <ul className="m-0 grid list-none gap-2.5 p-0">
            {pair.onlyA.map((s) => (
              <Item key={s.tweet_id} slot={s} stat={`${formatInt(s.rt_cluster)} pessoas do ${a.label}`} />
            ))}
          </ul>
        </div>
        <div className={`${column} border-2 border-dashed border-line-strong bg-bg`}>
          <h4 className="m-0 mb-3 text-[18px] font-extrabold">Nas duas</h4>
          {pair.both.length === 0 ? (
            <p className="m-0 text-[16px] leading-[1.6] text-muted">Nenhum dos tweets mais retuitados aparece nas duas bolhas.</p>
          ) : (
            <ul className="m-0 grid list-none gap-2.5 p-0">
              {pair.both.map((s) => (
                <Item
                  key={s.tweet_id}
                  slot={s}
                  muted
                  stat={`${formatInt(s.rtA)} pessoas do ${a.label} e ${formatInt(s.rtB)} do ${b.label}`}
                />
              ))}
            </ul>
          )}
        </div>
        <div className={column} style={{ background: cb.tint, color: cb.ink }}>
          <h4 className="m-0 mb-3 text-[18px] font-extrabold">Só no {b.label}</h4>
          <ul className="m-0 grid list-none gap-2.5 p-0">
            {pair.onlyB.map((s) => (
              <Item key={s.tweet_id} slot={s} stat={`${formatInt(s.rt_cluster)} pessoas do ${b.label}`} />
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
