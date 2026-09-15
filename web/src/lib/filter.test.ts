import { describe, expect, it } from "vitest";
import type { Slot, Tweet } from "../types";
import { DEFAULT_TOOLBAR, applyToolbar } from "./filter";

function tweet(over: Partial<Tweet> & { text: string; created_at: string; retweet_count?: number | null }): Tweet {
  return {
    id: "1",
    text: over.text,
    created_at: over.created_at,
    lang: "pt",
    source: null,
    possibly_sensitive: false,
    reply_settings: null,
    conversation_id: null,
    in_reply_to_user_id: null,
    metrics: {
      retweet_count: over.retweet_count ?? null,
      reply_count: null,
      like_count: null,
      quote_count: null,
      bookmark_count: null,
      impression_count: null,
    },
    entities: { urls: [], hashtags: [], mentions: [] },
    referenced_tweets: [],
    url: "https://x.com/i/web/status/1",
  };
}

function slot(over: Partial<Slot> & { rank: number }): Slot {
  return {
    community: 0,
    group: 1,
    k: 100,
    tweet_id: String(over.rank),
    rt_cluster: 10,
    rt_graph: 10,
    rt_event: 10,
    purity: 1,
    also_in: [],
    status: over.tweet ? "hydrated" : "not_found",
    error: null,
    tweet: null,
    author_id: null,
    author: null,
    author_status: over.tweet ? "hydrated" : null,
    ...over,
  };
}

const slots: Slot[] = [
  slot({
    rank: 1,
    purity: 0.95,
    rt_graph: 500,
    tweet: tweet({ text: "Ação em Brasília", created_at: "2023-01-08T20:00:00Z", retweet_count: 100 }),
    author: {
      id: "a",
      username: "Ana_Flor",
      name: "Ana Flor",
      description: null,
      location: null,
      url: null,
      profile_image_url: null,
      protected: null,
      verified: null,
      verified_type: null,
      created_at: null,
      metrics: { followers_count: null, following_count: null, tweet_count: null, listed_count: null },
    },
  }),
  slot({
    rank: 2,
    purity: 0.4,
    rt_graph: 900,
    tweet: tweet({ text: "Outro texto", created_at: "2023-01-08T18:00:00Z", retweet_count: null }),
  }),
  slot({ rank: 3, purity: 0.7, rt_graph: 700 }), // fantasma
];

describe("applyToolbar", () => {
  it("padrão: todos, na ordem do ranking", () => {
    expect(applyToolbar(slots, DEFAULT_TOOLBAR).map((s) => s.rank)).toEqual([1, 2, 3]);
  });
  it("ordena por pureza decrescente", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "purity" }).map((s) => s.rank)).toEqual([1, 3, 2]);
  });
  it("ordena por RTs no grafo decrescente", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "rt_graph" }).map((s) => s.rank)).toEqual([2, 3, 1]);
  });
  it("ordena por reposts na API com nulos (e fantasmas) por último", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "api_retweets" }).map((s) => s.rank)).toEqual([1, 2, 3]);
  });
  it("ordena por data crescente com fantasmas por último", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "date" }).map((s) => s.rank)).toEqual([2, 1, 3]);
  });
  it("filtra por status", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, status: "hydrated" }).map((s) => s.rank)).toEqual([1, 2]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, status: "ghost" }).map((s) => s.rank)).toEqual([3]);
  });
  it("filtra por exclusividade (pureza ≥ 0,90 / < 0,50)", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, exclusivity: "exclusive" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, exclusivity: "shared" }).map((s) => s.rank)).toEqual([2]);
  });
  it("busca sem acento nem caixa no texto, nome e @handle", () => {
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "brasilia" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "ana flor" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "ANA_FLOR" }).map((s) => s.rank)).toEqual([1]);
    expect(applyToolbar(slots, { ...DEFAULT_TOOLBAR, query: "nada" })).toEqual([]);
  });
  it("não muta a entrada", () => {
    const before = slots.map((s) => s.rank);
    applyToolbar(slots, { ...DEFAULT_TOOLBAR, sort: "rt_graph" });
    expect(slots.map((s) => s.rank)).toEqual(before);
  });
});
