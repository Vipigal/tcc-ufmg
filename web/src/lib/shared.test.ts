import { describe, expect, it } from "vitest";
import { bubbleSentence, pairSummary, sharePct } from "./shared";

const label = (c: number) => `Grupo ${c + 1}`;

describe("sharePct", () => {
  it("diz 'menos de 1%' abaixo de 1%", () => {
    expect(sharePct(0.004)).toBe("menos de 1%");
  });
  it("usa uma casa decimal abaixo de 10%", () => {
    expect(sharePct(0.012)).toBe("1,2%");
  });
  it("arredonda para inteiro a partir de 10%", () => {
    expect(sharePct(0.208)).toBe("21%");
  });
});

describe("bubbleSentence", () => {
  const base = { n_nodes: 14732, frac_nodes: 0.442 };

  it("descreve um grupo isolado", () => {
    expect(bubbleSentence({ ...base, shared: 0.016, shared_with: { "0": 0.012 } }, label)).toBe(
      "14.732 pessoas, 44% do evento. Só 2% do que esta bolha retuíta aparece nas outras.",
    );
  });

  it("aponta o grupo que concentra quase todo o compartilhamento", () => {
    expect(bubbleSentence({ ...base, shared: 0.224, shared_with: { "1": 0.015, "2": 0.208 } }, label)).toBe(
      "14.732 pessoas, 44% do evento. 22% do que esta bolha retuíta aparece nas outras, quase tudo no Grupo 3.",
    );
  });

  it("aponta o grupo com que mais compartilha quando o compartilhamento é espalhado", () => {
    expect(
      bubbleSentence({ ...base, shared: 0.517, shared_with: { "0": 0.204, "2": 0.165, "4": 0.147 } }, label),
    ).toBe("14.732 pessoas, 44% do evento. 52% do que esta bolha retuíta aparece nas outras, mais no Grupo 1.");
  });

  it("omite o compartilhamento quando a métrica não existe", () => {
    expect(bubbleSentence({ ...base, shared: null, shared_with: null }, label)).toBe("14.732 pessoas, 44% do evento.");
  });
});

describe("pairSummary", () => {
  const a = { community: 1, label: "Grupo 1", shared_with: { "0": 0.012 } };
  const b = { community: 0, label: "Grupo 2", shared_with: { "1": 0.015, "2": 0.208 } };
  const c = { community: 2, label: "Grupo 3", shared_with: { "0": 0.501 } };

  it("marca pares que quase não compartilham", () => {
    expect(pairSummary(a, b)).toEqual({
      title: "Grupo 1 e Grupo 2: quase nada em comum",
      lede: "1,2% do que o Grupo 1 retuíta circula no Grupo 2, e 1,5% no sentido contrário.",
    });
  });

  it("descreve os dois sentidos de pares que compartilham", () => {
    expect(pairSummary(b, c)).toEqual({
      title: "Grupo 2 e Grupo 3",
      lede: "21% do que o Grupo 2 retuíta circula no Grupo 3, e 50% no sentido contrário.",
    });
  });
});
