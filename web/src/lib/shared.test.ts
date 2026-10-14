import { describe, expect, it } from "vitest";
import { sharedPhrase } from "./shared";

const label = (c: number) => (c === 2 ? "Grupo 3" : `c${c}`);

describe("sharedPhrase", () => {
  it("isolado abaixo de 10%", () => {
    expect(sharedPhrase({ shared: 0.02, shared_with: { "0": 0.01 } }, label)).toEqual({
      text: "quase nada em comum com os outros grupos",
      partner: null,
    });
  });
  it("aponta o grupo com que mais compartilha", () => {
    expect(sharedPhrase({ shared: 0.51, shared_with: { "0": 0.01, "2": 0.5 } }, label)).toEqual({
      text: "mais em comum com o Grupo 3 (50% do que retuíta)",
      partner: 2,
    });
  });
  it("sem métrica, sem frase", () => {
    expect(sharedPhrase({ shared: null, shared_with: null }, label)).toBeNull();
  });
});
