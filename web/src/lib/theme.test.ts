import { describe, expect, it } from "vitest";
import { lighten } from "./color";
import { readTheme, writeTheme } from "./theme";

describe("tema", () => {
  it("padrão escuro sem armazenamento, com valor inválido ou se o acesso lançar", () => {
    expect(readTheme(() => undefined)).toBe("dark");
    expect(readTheme(() => ({ getItem: () => "sepia" }))).toBe("dark");
    expect(
      readTheme(() => {
        throw new Error("SecurityError");
      }),
    ).toBe("dark");
  });
  it("respeita a escolha salva e não quebra ao gravar sem armazenamento", () => {
    expect(readTheme(() => ({ getItem: () => "light" }))).toBe("light");
    expect(() =>
      writeTheme(() => {
        throw new Error("SecurityError");
      }, "light"),
    ).not.toThrow();
  });
});

describe("lighten", () => {
  it("mistura com branco na proporção dada e preserva entradas inválidas", () => {
    expect(lighten("#000000", 0.5)).toBe("#808080");
    expect(lighten("#5E4FA2", 0)).toBe("#5e4fa2");
    expect(lighten("nada", 0.3)).toBe("nada");
  });
});
