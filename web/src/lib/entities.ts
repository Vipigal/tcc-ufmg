import type { TweetEntities } from "../types";

/**
 * Texto do tweet → segmentos renderizáveis (spec §7.5).
 * Offsets da API do X são em code points Unicode: fatiar sempre `Array.from(text)`, nunca `text.slice`.
 */

export type SegmentKind = "text" | "hashtag" | "mention" | "url" | "media";

export interface Segment {
  kind: SegmentKind;
  text: string;
  href?: string;
}

interface Span {
  start: number;
  end: number;
  kind: Exclude<SegmentKind, "text">;
  text: string;
  href: string;
}

/** Há pelo menos uma url com `media_key` (foto/vídeo/gif sem objeto de mídia hidratado). */
export function hasMedia(entities: TweetEntities): boolean {
  return entities.urls.some((u) => Boolean(u.media_key));
}

export function segmentText(text: string, entities: TweetEntities, tweetUrl: string): Segment[] {
  const cps = Array.from(text);

  // 1. coletar entidades como spans
  const spans: Span[] = [];
  for (const h of entities.hashtags) {
    spans.push({ start: h.start, end: h.end, kind: "hashtag", text: `#${h.tag}`, href: `https://x.com/hashtag/${h.tag}` });
  }
  for (const m of entities.mentions) {
    spans.push({ start: m.start, end: m.end, kind: "mention", text: `@${m.username}`, href: `https://x.com/${m.username}` });
  }
  for (const u of entities.urls) {
    if (u.media_key) {
      spans.push({ start: u.start, end: u.end, kind: "media", text: "Mídia", href: tweetUrl });
    } else {
      spans.push({ start: u.start, end: u.end, kind: "url", text: u.display_url ?? u.url, href: u.expanded_url ?? u.url });
    }
  }

  // 2. ordenar por início; descartar sobreposições (mantém a primeira) e offsets inválidos
  spans.sort((a, b) => a.start - b.start || a.end - b.end);
  const kept: Span[] = [];
  let cursor = 0;
  for (const s of spans) {
    if (s.start < cursor || s.start < 0 || s.end > cps.length || s.end <= s.start) continue;
    kept.push(s);
    cursor = s.end;
  }

  // 3. varrer emitindo texto entre entidades e as entidades
  const out: Segment[] = [];
  let pos = 0;
  for (const s of kept) {
    if (s.start > pos) out.push({ kind: "text", text: cps.slice(pos, s.start).join("") });
    out.push({ kind: s.kind, text: s.text, href: s.href });
    pos = s.end;
  }
  if (pos < cps.length) out.push({ kind: "text", text: cps.slice(pos).join("") });

  return mergeText(collapseMedia(out));
}

/** Mídia no fim não vira texto (o chip fica na linha de anexos); várias mídias no meio → um chip. */
function collapseMedia(segments: Segment[]): Segment[] {
  const out = [...segments];
  let dropped = false;
  while (out.length > 0) {
    const last = out[out.length - 1];
    if (last.kind === "media") {
      out.pop();
      dropped = true;
      continue;
    }
    if (dropped && last.kind === "text" && last.text.trim() === "") {
      out.pop();
      continue;
    }
    break;
  }
  if (dropped && out.length > 0) {
    const last = out[out.length - 1];
    if (last.kind === "text") out[out.length - 1] = { ...last, text: last.text.replace(/\s+$/u, "") };
  }
  // várias mídias → um chip; o espaço que separava as repetidas sai junto
  const result: Segment[] = [];
  let seen = false;
  for (const s of out) {
    if (s.kind === "media") {
      if (seen) {
        const prev = result[result.length - 1];
        if (prev && prev.kind === "text" && prev.text.trim() === "") result.pop();
        continue;
      }
      seen = true;
    }
    result.push(s);
  }
  return result;
}

/** Junta segmentos de texto adjacentes (sobram depois do colapso de mídia). */
function mergeText(segments: Segment[]): Segment[] {
  const out: Segment[] = [];
  for (const s of segments) {
    const prev = out[out.length - 1];
    if (prev && prev.kind === "text" && s.kind === "text") out[out.length - 1] = { kind: "text", text: prev.text + s.text };
    else out.push(s);
  }
  return out;
}
