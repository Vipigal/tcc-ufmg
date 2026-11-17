import { describe, expect, it } from "vitest";
import { groupAt, labelPlacement, pairNote } from "./groupMap";

const grid = { n: 2, cells: [3, -1, 3, 7] };

describe("groupAt", () => {
  it("devolve o grupo da célula sob o ponto (coordenadas 0–1, y de cima para baixo)", () => {
    expect(groupAt(grid, 0.1, 0.1)).toBe(3);
    expect(groupAt(grid, 0.9, 0.9)).toBe(7);
  });

  it("devolve null onde não há grupo", () => {
    expect(groupAt(grid, 0.9, 0.1)).toBeNull();
  });

  it("trata a borda direita e a de baixo como a última célula", () => {
    expect(groupAt(grid, 1, 1)).toBe(7);
  });
});

describe("pairNote", () => {
  const label = (c: number) => `Grupo ${c + 1}`;

  it("explica os pares desenhados juntos", () => {
    expect(pairNote([{ a: 0, b: 2, share: 0.501 }], label)).toBe(
      "Grupo 1 e Grupo 3 aparecem juntos: 50% do que um retuíta circula no outro.",
    );
  });

  it("não diz nada sem par dominante", () => {
    expect(pairNote([], label)).toBeNull();
  });
});

describe("labelPlacement", () => {
  it("mantém o rótulo dentro do quadro", () => {
    expect(labelPlacement({ label_x: 0.01, label_y: 0.5, anchor: "bottom" })).toMatchObject({ x: 0.12 });
    expect(labelPlacement({ label_x: 0.99, label_y: 0.5, anchor: "bottom" })).toMatchObject({ x: 0.88 });
  });

  it("vira o rótulo para baixo do ponto quando não cabe acima", () => {
    expect(labelPlacement({ label_x: 0.5, label_y: 0.03, anchor: "bottom" })).toEqual({ x: 0.5, y: 0.03, anchor: "top" });
  });

  it("vira o rótulo para cima do ponto quando não cabe abaixo", () => {
    expect(labelPlacement({ label_x: 0.5, label_y: 0.97, anchor: "top" })).toEqual({ x: 0.5, y: 0.97, anchor: "bottom" });
  });
});
