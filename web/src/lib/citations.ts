export type CitedSegment = { kind: "text"; text: string } | { kind: "cite"; ids: string[] };

const CITATION = /\[([\d,;\s]+)\]/g;

/** Texto da síntese (M11) → trechos e citações `[id, id]`. */
export function splitCitations(text: string): CitedSegment[] {
  const out: CitedSegment[] = [];
  let last = 0;
  for (const m of text.matchAll(CITATION)) {
    const ids = m[1].match(/\d+/g) ?? [];
    if (ids.length === 0) continue;
    if (m.index > last) out.push({ kind: "text", text: text.slice(last, m.index) });
    out.push({ kind: "cite", ids });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ kind: "text", text: text.slice(last) });
  return out;
}
