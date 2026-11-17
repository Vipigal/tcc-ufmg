import type { ReactNode } from "react";
import { memo, useMemo } from "react";
import { BadgeCheck, ChartNoAxesColumn, Heart, MessageCircle, Repeat2 } from "lucide-react";
import type { Slot, Tweet } from "../types";
import { OMITTED_MEDIA } from "../content/events";
import { segmentText } from "../lib/entities";
import { formatCompact, formatDate, formatInt, formatPct } from "../lib/format";
import { VERIFIED_TYPE_TEXT } from "../lib/glossary";
import type { AxisColors } from "../lib/palette";
import { Avatar } from "./Avatar";
import { MediaGrid } from "./MediaGrid";
import { TweetText } from "./TweetText";

interface Props {
  slot: Slot & { tweet: Tweet };
  label: string;
  colors: AxisColors;
}

const BADGE_COLOR: Record<string, string> = { government: "#829AAB", business: "#E2B719" };

function Metric({ icon, value, label }: { icon: ReactNode; value: number | null; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5" aria-label={`${formatInt(value)} ${label}`} title={label}>
      {icon}
      {formatCompact(value)}
    </span>
  );
}

function stripText(slot: Slot, label: string): string {
  const people = `${formatInt(slot.rt_cluster)} pessoas desta bolha retuitaram`;
  if (slot.origin === "amplified") return `#${label} nesta bolha: ${people}`;
  return slot.purity == null ? people : `${people} · ${formatPct(slot.purity)} de quem retuitou é desta bolha`;
}

/** Um tweet na thread da bolha: como no X, mais a faixa de quantas pessoas da bolha retuitaram. */
export const ThreadTweet = memo(function ThreadTweet({ slot, label, colors }: Props) {
  const { tweet, author } = slot;
  const segments = useMemo(() => segmentText(tweet.text, tweet.entities, tweet.url), [tweet]);
  const omitted = OMITTED_MEDIA[tweet.id];
  const m = tweet.metrics;
  const badge = author?.verified ? (BADGE_COLOR[author.verified_type ?? ""] ?? "var(--color-x-blue)") : null;
  return (
    <>
      <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[15px]">
        <b>{author?.name ?? "Autor indisponível"}</b>
        {badge && author && (
          <span title={VERIFIED_TYPE_TEXT[author.verified_type ?? "none"] ?? "verificado"} style={{ color: badge }} className="inline-flex">
            <BadgeCheck size={18} aria-label="conta verificada" />
          </span>
        )}
        <span className="text-faint">
          {author?.username ? `@${author.username} · ` : ""}
          <a href={tweet.url} target="_blank" rel="noopener noreferrer" className="text-faint no-underline hover:underline">
            {formatDate(tweet.created_at)}
          </a>
        </span>
      </div>
      <TweetText segments={segments} />
      {omitted ? (
        <div className="rounded-2xl border border-dashed border-line-strong px-3.5 py-3 text-[14px] text-muted">{omitted}</div>
      ) : (
        <MediaGrid media={tweet.media ?? []} tweetUrl={tweet.url} />
      )}
      <div className="mt-3 flex max-w-[440px] justify-between text-[14px] text-faint">
        <Metric icon={<MessageCircle size={18} />} value={m.reply_count} label="respostas" />
        <Metric icon={<Repeat2 size={18} />} value={m.retweet_count} label="retweets" />
        <Metric icon={<Heart size={18} />} value={m.like_count} label="curtidas" />
        <Metric icon={<ChartNoAxesColumn size={18} />} value={m.impression_count} label="visualizações" />
      </div>
      <p className="m-0 mt-3 rounded-xl px-3 py-2 text-[14px] font-bold" style={{ background: colors.tint, color: colors.ink }}>
        {stripText(slot, label)}
      </p>
    </>
  );
});

export function ThreadAvatar({ slot }: { slot: Slot }) {
  return <Avatar src={slot.author?.profile_image_url ?? null} name={slot.author?.name ?? null} color="#5E5A72" size={48} />;
}
