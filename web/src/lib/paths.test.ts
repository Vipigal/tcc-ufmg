import { describe, expect, it } from "vitest";
import { bubblePath, pickBubble, pickCompare } from "./paths";

const clusters = [{ community: 1 }, { community: 0 }, { community: 2 }];

describe("bubblePath", () => {
  it("aponta para a bolha dentro da página do evento", () => {
    expect(bubblePath("ev", 2)).toBe("/ev/2");
  });
});

describe("pickBubble", () => {
  it("abre a bolha pedida quando ela existe no evento", () => {
    expect(pickBubble(clusters, "2")).toEqual({ community: 2 });
  });
  it("abre a primeira bolha sem pedido ou com pedido inválido", () => {
    expect(pickBubble(clusters, undefined)).toEqual({ community: 1 });
    expect(pickBubble(clusters, "9")).toEqual({ community: 1 });
  });
});

describe("pickCompare", () => {
  it("aceita outra bolha do evento", () => {
    expect(pickCompare(clusters, 1, "0")).toEqual({ community: 0 });
  });
  it("ignora a própria bolha, bolhas inexistentes e ausência de pedido", () => {
    expect(pickCompare(clusters, 1, "1")).toBeUndefined();
    expect(pickCompare(clusters, 1, "7")).toBeUndefined();
    expect(pickCompare(clusters, 1, null)).toBeUndefined();
  });
});
