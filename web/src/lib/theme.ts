import { createContext, useContext } from "react";

/** Tema do app (spec 2026-10-14 §2.4): escuro por padrão; a escolha fica no localStorage do visitante. */
export type Theme = "dark" | "light";

export const THEME_KEY = "leitor:theme";
export const DEFAULT_THEME: Theme = "dark";

/** Lê o tema salvo; qualquer falha de armazenamento (modo privado, bloqueio) cai no padrão. */
export function readTheme(getStorage: () => Pick<Storage, "getItem"> | undefined): Theme {
  try {
    const v = getStorage()?.getItem(THEME_KEY);
    return v === "light" || v === "dark" ? v : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

export function writeTheme(getStorage: () => Pick<Storage, "setItem"> | undefined, theme: Theme): void {
  try {
    getStorage()?.setItem(THEME_KEY, theme);
  } catch {
    /* sem armazenamento: vale só nesta visita */
  }
}

export const browserStorage = () => (typeof window === "undefined" ? undefined : window.localStorage);

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
}

export const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({
  theme: DEFAULT_THEME,
  toggle: () => {},
});

export const useTheme = () => useContext(ThemeContext);
