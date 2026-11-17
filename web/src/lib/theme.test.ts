import { describe, expect, it } from "vitest";
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
