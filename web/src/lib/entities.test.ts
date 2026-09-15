import { describe, expect, it } from "vitest";
import type { TweetEntities } from "../types";
import { hasMedia, segmentText } from "./entities";

const TWEET_URL = "https://x.com/i/web/status/1";
const none: TweetEntities = { urls: [], hashtags: [], mentions: [] };

describe("segmentText", () => {
  it("(a) hashtag + menção + url em texto ASCII", () => {
    //            0123456789012345678901234567890123456
    const text = "Oi @ana veja #stf em https://t.co/abc";
    const entities: TweetEntities = {
      mentions: [{ start: 3, end: 7, username: "ana" }],
      hashtags: [{ start: 13, end: 17, tag: "stf" }],
      urls: [
        {
          start: 21,
          end: 37,
          url: "https://t.co/abc",
          expanded_url: "https://example.com/x",
          display_url: "example.com/x",
        },
      ],
    };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([
      { kind: "text", text: "Oi " },
      { kind: "mention", text: "@ana", href: "https://x.com/ana" },
      { kind: "text", text: " veja " },
      { kind: "hashtag", text: "#stf", href: "https://x.com/hashtag/stf" },
      { kind: "text", text: " em " },
      { kind: "url", text: "example.com/x", href: "https://example.com/x" },
    ]);
  });

  it("(b) offsets são em code points: emoji antes da hashtag", () => {
    const text = "🚨 #STF"; // 🚨 = 1 code point, 2 unidades UTF-16
    const entities: TweetEntities = { ...none, hashtags: [{ start: 2, end: 6, tag: "STF" }] };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([
      { kind: "text", text: "🚨 " },
      { kind: "hashtag", text: "#STF", href: "https://x.com/hashtag/STF" },
    ]);
  });

  it("(c) url com media_key vira mídia, sai do fim do texto e hasMedia é true", () => {
    const text = "Cavalo socorrido https://t.co/m1";
    const entities: TweetEntities = {
      ...none,
      urls: [
        {
          start: 17,
          end: 32,
          url: "https://t.co/m1",
          expanded_url: "https://x.com/u/status/1/photo/1",
          display_url: "pic.x.com/m1",
          media_key: "3_1",
        },
      ],
    };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([{ kind: "text", text: "Cavalo socorrido" }]);
    expect(hasMedia(entities)).toBe(true);
    expect(hasMedia(none)).toBe(false);
  });

  it("(d) entidades sobrepostas: mantém a primeira", () => {
    const text = "#abcd ef";
    const entities: TweetEntities = {
      ...none,
      hashtags: [{ start: 0, end: 5, tag: "abcd" }],
      mentions: [{ start: 2, end: 6, username: "cdef" }],
    };
    expect(segmentText(text, entities, TWEET_URL)).toEqual([
      { kind: "hashtag", text: "#abcd", href: "https://x.com/hashtag/abcd" },
      { kind: "text", text: " ef" },
    ]);
  });

  it("(e) sem entidades → um segmento de texto", () => {
    expect(segmentText("Só texto", none, TWEET_URL)).toEqual([{ kind: "text", text: "Só texto" }]);
  });

  it("várias mídias no meio do texto colapsam em um chip; mídia no fim é removida", () => {
    //            0123456789012345678901234567890123
    const text = "a https://t.co/1 https://t.co/2 b https://t.co/3";
    const media = (start: number, end: number, k: string) => ({
      start,
      end,
      url: `https://t.co/${k}`,
      media_key: `3_${k}`,
    });
    const entities: TweetEntities = { ...none, urls: [media(2, 16, "1"), media(17, 31, "2"), media(34, 48, "3")] };
    const out = segmentText(text, entities, TWEET_URL);
    expect(out.filter((s) => s.kind === "media")).toHaveLength(1);
    expect(out[0]).toEqual({ kind: "text", text: "a " });
    expect(out[1]).toEqual({ kind: "media", text: "Mídia", href: TWEET_URL });
    expect(out[out.length - 1]).toEqual({ kind: "text", text: " b" });
  });

  it("descarta entidade com offset fora do texto", () => {
    const entities: TweetEntities = { ...none, hashtags: [{ start: 10, end: 14, tag: "x" }] };
    expect(segmentText("curto", entities, TWEET_URL)).toEqual([{ kind: "text", text: "curto" }]);
  });
});
