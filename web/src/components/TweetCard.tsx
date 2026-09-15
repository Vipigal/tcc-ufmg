import type { ReactNode } from "react";
import { memo, useMemo } from "react";
import {
  BadgeCheck,
  Bookmark,
  ExternalLink,
  Eye,
  Heart,
  Image as ImageIcon,
  MessageCircle,
  Quote,
  Repeat2,
  TriangleAlert,
  UserRound,
} from "lucide-react";
import type { Author, Slot, Tweet } from "../types";
import { hasMedia, segmentText } from "../lib/entities";
import { formatCompact, formatDate, formatInt } from "../lib/format";
import { AUTHOR_STATUS_TEXT, REFERENCE_TEXT, VERIFIED_TYPE_TEXT } from "../lib/glossary";
import { Avatar } from "./Avatar";
import { ResearchStrip } from "./ResearchStrip";
import { TweetText } from "./TweetText";

interface Props {
  slot: Slot & { tweet: Tweet };
  color: string;
}

const MISSING_AUTHOR_COLOR = "#9ca3af";

/** RF5 / spec §7.4: card estilo X (sem marca) + faixa de pesquisa. Memoizado: `slot` vem do cache por evento, então a identidade é estável. */
export const TweetCard = memo(function TweetCard({ slot, color }: Props) {
  const { tweet, author } = slot;
  const segments = useMemo(() => segmentText(tweet.text, tweet.entities, tweet.url), [tweet]);
  const media = hasMedia(tweet.entities);
  const m = tweet.metrics;

  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-white">
      <div className="px-4 pt-3">
        <header className="flex items-start gap-3">
          <Avatar
            src={author?.profile_image_url ?? null}
            name={author?.name ?? null}
            color={author ? color : MISSING_AUTHOR_COLOR}
          />
          <div className="min-w-0 flex-1 text-[15px] leading-5">
            {author ? (
              <AuthorLine author={author} createdAt={tweet.created_at} />
            ) : (
              <MissingAuthor slot={slot} createdAt={tweet.created_at} />
            )}
          </div>
          <a
            href={tweet.url}
            target="_blank"
            rel="noopener noreferrer"
            title="abrir no X"
            className="shrink-0 rounded-full p-1 text-muted hover:bg-gray-100 hover:text-x-blue"
          >
            <ExternalLink size={16} />
          </a>
        </header>

        <div className="mt-2">
          <TweetText segments={segments} />
        </div>

        {(media || tweet.referenced_tweets.length > 0) && (
          <div className="mt-2 flex flex-wrap gap-2">
            {media && (
              <a
                href={tweet.url}
                target="_blank"
                rel="noopener noreferrer"
                className="chip"
                title="mídia não hidratada; abre o tweet no X"
              >
                <ImageIcon size={14} /> Mídia <ExternalLink size={12} />
              </a>
            )}
            {tweet.referenced_tweets.map((r) => (
              <a
                key={`${r.type}-${r.id}`}
                href={`https://x.com/i/web/status/${r.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="chip"
              >
                {REFERENCE_TEXT[r.type]} <ExternalLink size={12} />
              </a>
            ))}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 pb-3 text-[13px] text-muted">
          <Metric icon={<MessageCircle size={16} />} value={m.reply_count} label="respostas" />
          <Metric icon={<Repeat2 size={16} />} value={m.retweet_count} label="reposts" />
          <Metric icon={<Quote size={16} />} value={m.quote_count} label="citações" />
          <Metric icon={<Heart size={16} />} value={m.like_count} label="curtidas" />
          <Metric icon={<Bookmark size={16} />} value={m.bookmark_count} label="salvos" />
          <Metric icon={<Eye size={16} />} value={m.impression_count} label="impressões" />
          <span className="ml-auto flex items-center gap-1.5">
            {tweet.lang && (
              <span className="badge" title="idioma segundo a API">
                {tweet.lang}
              </span>
            )}
            {tweet.possibly_sensitive && (
              <span
                className="badge border-amber-300 text-amber-800"
                title="marcado pela API como possivelmente sensível"
              >
                <TriangleAlert size={11} /> sensível
              </span>
            )}
          </span>
        </div>
      </div>
      <ResearchStrip slot={slot} color={color} />
    </article>
  );
});

function Metric({ icon, value, label }: { icon: ReactNode; value: number | null; label: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 whitespace-nowrap"
      title={value == null ? label : `${formatInt(value)} ${label}`}
    >
      {icon}
      {formatCompact(value)}
    </span>
  );
}

function AuthorLine({ author, createdAt }: { author: Author; createdAt: string }) {
  const tooltip = [
    author.description,
    author.location,
    author.metrics.followers_count != null ? `${formatInt(author.metrics.followers_count)} seguidores` : null,
  ]
    .filter((v): v is string => Boolean(v))
    .join("\n");
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-1">
      <span className="truncate font-bold text-ink" title={tooltip}>
        {author.name ?? "—"}
      </span>
      {author.verified && (
        <span
          className="inline-flex shrink-0 text-x-blue"
          title={VERIFIED_TYPE_TEXT[author.verified_type ?? "none"] ?? "verificado"}
        >
          <BadgeCheck size={16} />
        </span>
      )}
      <span className="truncate text-muted">@{author.username ?? author.id}</span>
      <span className="text-muted">·</span>
      <time dateTime={createdAt} className="whitespace-nowrap text-muted">
        {formatDate(createdAt)}
      </time>
    </div>
  );
}

/** RF8: tweet hidratado cujo autor a API não devolveu. */
function MissingAuthor({ slot, createdAt }: { slot: Slot; createdAt: string }) {
  const reason = slot.author_status ? AUTHOR_STATUS_TEXT[slot.author_status] : null;
  return (
    <div className="flex flex-wrap items-center gap-x-1 text-muted">
      <UserRound size={14} />
      <span className="font-semibold">Autor não disponível</span>
      {reason && <span>({reason})</span>}
      {slot.author_id && <span className="font-mono text-[12.5px]">id {slot.author_id}</span>}
      <span>·</span>
      <time dateTime={createdAt} className="whitespace-nowrap">
        {formatDate(createdAt)}
      </time>
    </div>
  );
}
