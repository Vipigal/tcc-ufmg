import { useState } from "react";
import { Play } from "lucide-react";
import type { Media } from "../types";

interface Props {
  media: Media[];
  tweetUrl: string;
  compact?: boolean;
}

/**
 * Mídias do tweet (M9c, spec 2026-10-14 §5): fotos direto do servidor do X; vídeo e GIF como miniatura
 * com ▶, que abre o tweet no X (sem player embutido). Sem desfoque, por decisão do autor.
 */
export function MediaGrid({ media, tweetUrl, compact = false }: Props) {
  const items = media.slice(0, 4);
  if (items.length === 0) return null;
  const cols = items.length === 1 ? "grid-cols-1" : "grid-cols-2";
  const h = compact ? (items.length === 1 ? "max-h-56" : "h-28") : items.length === 1 ? "max-h-[420px]" : "h-44";
  return (
    <div className={`mt-2 grid ${cols} gap-0.5 overflow-hidden rounded-2xl border border-line`}>
      {items.map((m) => (
        <MediaItem key={m.media_key} m={m} tweetUrl={tweetUrl} sizeClass={h} />
      ))}
    </div>
  );
}

function MediaItem({ m, tweetUrl, sizeClass }: { m: Media; tweetUrl: string; sizeClass: string }) {
  const [failed, setFailed] = useState(false);
  const src = m.type === "photo" ? (m.url ?? m.preview_image_url) : m.preview_image_url;
  if (!src || failed) {
    return (
      <a href={tweetUrl} target="_blank" rel="noopener noreferrer" className={`flex ${sizeClass} min-h-20 items-center justify-center bg-subtle text-[12px] text-muted`}>
        mídia indisponível · abrir no X
      </a>
    );
  }
  const isVideo = m.type !== "photo";
  const img = (
    <img
      src={src}
      alt={m.alt_text ?? ""}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
      className={`w-full ${sizeClass} bg-subtle object-cover`}
    />
  );
  if (!isVideo) return img;
  return (
    <a href={tweetUrl} target="_blank" rel="noopener noreferrer" className="relative block" title="vídeo: abrir no X">
      {img}
      <span className="absolute inset-0 flex items-center justify-center">
        <span className="rounded-full bg-black/70 p-3 text-white">
          <Play size={22} fill="currentColor" />
        </span>
      </span>
      {m.type === "animated_gif" && (
        <span className="absolute bottom-1.5 left-1.5 rounded bg-black/70 px-1 text-[11px] font-bold text-white">GIF</span>
      )}
    </a>
  );
}
