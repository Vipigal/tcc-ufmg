import { describe, expect, it } from "vitest";
import type { Slot, SlotOrigin, SlotStatus, Tweet } from "../types";
import { buildThread, gapText, slotLabel } from "./thread";

const tweet: Tweet = {
  id: "t",
  text: "",
  created_at: "2023-01-08T15:00:00Z",
  lang: null,
  source: null,
  possibly_sensitive: null,
  reply_settings: null,
  conversation_id: null,
  in_reply_to_user_id: null,
  metrics: {
    retweet_count: null,
    reply_count: null,
    like_count: null,
    quote_count: null,
    bookmark_count: null,
    impression_count: null,
  },
  entities: { urls: [], hashtags: [], mentions: [] },
  referenced_tweets: [],
  url: "https://x.com/i/web/status/t",
  media: [],
};

function slot(rank: number, status: SlotStatus, origin: SlotOrigin = "amplified", community = 1): Slot {
  return {
    community,
    group: 1,
    rank,
    k: 100,
    origin,
    lift: null,
    tweet_id: `${origin}-${rank}`,
    rt_cluster: 100 - rank,
    rt_graph: 200,
    rt_event: 300,
    purity: 0.5,
    also_in: [],
    status,
    error: null,
    tweet: status === "hydrated" ? tweet : null,
    author_id: null,
    author: null,
    author_status: null,
  };
}

describe("slotLabel", () => {
  it("usa o ranking para os mais retuitados e C + ranking para os característicos", () => {
    expect(slotLabel(slot(7, "hydrated"))).toBe("7");
    expect(slotLabel(slot(2, "hydrated", "characteristic"))).toBe("C2");
  });
});

describe("gapText", () => {
  it("fala de uma posição no singular", () => {
    expect(gapText(["2"])).toBe("A posição 2 foi apagada ou vem de conta suspensa.");
  });
  it("junta duas posições com 'e'", () => {
    expect(gapText(["3", "4"])).toBe("As posições 3 e 4 foram apagadas ou vêm de contas suspensas.");
  });
  it("resume três ou mais como intervalo", () => {
    expect(gapText(["C3", "C4", "C5"])).toBe("As posições C3 a C5 foram apagadas ou vêm de contas suspensas.");
  });
});

describe("buildThread", () => {
  const slots = [
    slot(4, "not_found"),
    slot(1, "hydrated"),
    slot(3, "not_authorized"),
    slot(2, "hydrated"),
    slot(5, "hydrated"),
    slot(1, "hydrated", "characteristic"),
    slot(1, "hydrated", "amplified", 2),
  ];

  it("ordena pelo ranking, só da origem e do grupo pedidos", () => {
    const items = buildThread(slots, 1, "amplified");
    expect(items.map((i) => (i.kind === "tweet" ? i.label : i.labels.join("+")))).toEqual(["1", "2", "3+4", "5"]);
  });

  it("agrupa posições indisponíveis seguidas num único aviso", () => {
    const items = buildThread(slots, 1, "amplified");
    expect(items[2]).toEqual({ kind: "gap", labels: ["3", "4"] });
  });

  it("separa os característicos", () => {
    const items = buildThread(slots, 1, "characteristic");
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ kind: "tweet", label: "C1" });
  });
});
