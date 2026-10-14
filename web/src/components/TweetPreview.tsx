import { memo, useMemo } from "react";
import { BadgeCheck, ExternalLink, Heart, Repeat2 } from "lucide-react";
import type { Slot, Tweet } from "../types";
import { segmentText } from "../lib/entities";
import { formatCompact, formatDec, formatInt } from "../lib/format";
import { GLOSSARY } from "../lib/glossary";
import { Avatar } from "./Avatar";
import { MediaGrid } from "./MediaGrid";
import { TweetText } from "./TweetText";

interface Props {
  slot: Slot & { tweet: Tweet };
  color: string;
}

/** Preview compacto de tweet para a comparação (spec 2026-10-14 §2.3): autor, texto, mídia e 2–3 números. */
export const TweetPreview = memo(function TweetPreview({ slot, color }: Props) {
  const { tweet, author } = slot;
  const segments = useMemo(() => segmentText(tweet.text, tweet.entities, tweet.url), [tweet]);
  return (
    <article className="rounded-2xl border border-line bg-surface px-3 py-2.5">
      <header className="flex items-center gap-2 text-[14px]">
        <Avatar src={author?.profile_image_url ?? null} name={author?.name ?? null} color={color} size={30} />
        <span className="truncate font-bold text-ink">{author?.name ?? "Autor não disponível"}</span>
        {author?.verified && <BadgeCheck size={15} className="shrink-0 text-x-blue" />}
        <span className="truncate text-muted">{author?.username ? `@${author.username}` : ""}</span>
        <a href={tweet.url} target="_blank" rel="noopener noreferrer" title="abrir no X" className="ml-auto shrink-0 text-muted hover:text-x-blue">
          <ExternalLink size={14} />
        </a>
      </header>
      <div className="mt-1.5 line-clamp-6 text-[14px] leading-5">
        <TweetText segments={segments} />
      </div>
      <MediaGrid media={tweet.media ?? []} tweetUrl={tweet.url} compact />
      <footer className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-muted">
        <span className="inline-flex items-center gap-1" title={`${formatInt(tweet.metrics.retweet_count)} reposts (API)`}>
          <Repeat2 size={14} /> {formatCompact(tweet.metrics.retweet_count)}
        </span>
        <span className="inline-flex items-center gap-1" title={`${formatInt(tweet.metrics.like_count)} curtidas (API)`}>
          <Heart size={14} /> {formatCompact(tweet.metrics.like_count)}
        </span>
        <span className="cursor-help" title={GLOSSARY.rt_cluster}>
          {formatInt(slot.rt_cluster)} RTs no grupo
        </span>
        {slot.lift != null && (
          <span className="cursor-help font-semibold text-violet-800 dark:text-violet-300" title={GLOSSARY.lift}>
            lift {formatDec(slot.lift, 1)}
          </span>
        )}
      </footer>
    </article>
  );
});
