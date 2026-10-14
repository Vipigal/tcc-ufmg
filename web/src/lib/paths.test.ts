import { describe, expect, it } from "vitest";
import type { EventMeta } from "../types";
import { pathForMode } from "./paths";

const meta = { slug: "ev", clusters: [{ community: 1 }, { community: 0 }, { community: 2 }] } as unknown as EventMeta;

describe("pathForMode", () => {
  it("visão geral é a entrada do evento", () => {
    expect(pathForMode("overview", meta)).toBe("/ev");
  });
  it("leitor mantém o grupo se existir no evento, senão o grupo 1", () => {
    expect(pathForMode("reader", meta, 2)).toBe("/ev/2");
    expect(pathForMode("reader", meta, 9)).toBe("/ev/1");
  });
  it("comparação mantém o par válido e completa com os primeiros grupos", () => {
    expect(pathForMode("compare", meta, 2, 0)).toBe("/ev/comparar/2/0");
    expect(pathForMode("compare", meta)).toBe("/ev/comparar/1/0");
    expect(pathForMode("compare", meta, 1, 1)).toBe("/ev/comparar/1/0");
    expect(pathForMode("compare", meta, 0, 7)).toBe("/ev/comparar/0/1");
  });
});
