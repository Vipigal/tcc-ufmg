import { describe, expect, it } from "vitest";
import { formatCompact, formatDate, formatDay, formatDec, formatInt, formatPct, normalize } from "./format";

describe("formatCompact", () => {
  it("abrevia em pt-BR com uma casa", () => {
    expect(formatCompact(28348)).toBe("28,3 mil");
    expect(formatCompact(1_200_000)).toBe("1,2 mi");
    expect(formatCompact(890)).toBe("890");
  });
  it("devolve travessão para null/undefined", () => {
    expect(formatCompact(null)).toBe("—");
    expect(formatCompact(undefined)).toBe("—");
  });
});

describe("formatInt", () => {
  it("usa ponto de milhar", () => {
    expect(formatInt(3389)).toBe("3.389");
    expect(formatInt(12_023_243)).toBe("12.023.243");
  });
  it("devolve travessão para null", () => {
    expect(formatInt(null)).toBe("—");
  });
});

describe("formatDec / formatPct", () => {
  it("formatDec usa vírgula decimal e casas fixas", () => {
    expect(formatDec(0.7538, 2)).toBe("0,75");
    expect(formatDec(1.00229, 1)).toBe("1,0");
    expect(formatDec(null, 2)).toBe("—");
  });
  it("formatPct multiplica por 100", () => {
    expect(formatPct(0.4423)).toBe("44%");
    expect(formatPct(0.358, 1)).toBe("35,8%");
    expect(formatPct(null)).toBe("—");
  });
});

describe("datas", () => {
  it("formatDate em horário de Brasília", () => {
    expect(formatDate("2023-01-08T18:54:38.000Z")).toBe("8 de jan. de 2023, 15:54");
  });
  it("formatDay não desloca o dia pelo fuso", () => {
    expect(formatDay("2023-01-08")).toBe("8 de janeiro de 2023");
    expect(formatDay("2022-09-07")).toBe("7 de setembro de 2022");
  });
});

describe("normalize", () => {
  it("remove acentos e caixa", () => {
    expect(normalize("Ação")).toBe("acao");
    expect(normalize("BRASÍLIA")).toBe("brasilia");
    expect(normalize("já")).toBe("ja");
  });
});
