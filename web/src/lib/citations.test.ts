import { describe, expect, it } from "vitest";
import { splitCitations } from "./citations";

describe("splitCitations", () => {
  it("separa o texto das citações entre colchetes", () => {
    expect(splitCitations('marcha "de 5km" [161213] e mais')).toEqual([
      { kind: "text", text: 'marcha "de 5km" ' },
      { kind: "cite", ids: ["161213"] },
      { kind: "text", text: " e mais" },
    ]);
  });

  it("abre citações com vários ids separados por vírgula", () => {
    expect(splitCitations("x [11, 22; 33]")).toEqual([
      { kind: "text", text: "x " },
      { kind: "cite", ids: ["11", "22", "33"] },
    ]);
  });

  it("devolve só texto quando não há citação", () => {
    expect(splitCitations("sem nada")).toEqual([{ kind: "text", text: "sem nada" }]);
  });

  it("ignora colchetes que não trazem ids", () => {
    expect(splitCitations("o [sic] texto")).toEqual([{ kind: "text", text: "o [sic] texto" }]);
  });
});
