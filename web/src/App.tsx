import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Moon, Sun } from "lucide-react";
import type { Index } from "./types";
import { useIndex } from "./data/hooks";
import { useKeptSearch } from "./lib/nav";
import { HOME_PATH, HOW_PATH } from "./lib/paths";
import { ThemeContext, applyTheme, browserStorage, readTheme, useTheme, writeTheme, type Theme } from "./lib/theme";
import { ErrorBox, Skeleton } from "./components/States";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => readTheme(browserStorage));
  useEffect(() => {
    applyTheme(theme);
    writeTheme(browserStorage, theme);
  }, [theme]);
  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  const value = useMemo(() => ({ theme, toggle }), [theme, toggle]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const label = theme === "dark" ? "usar tema claro" : "usar tema escuro";
  return (
    <button
      type="button"
      onClick={toggle}
      title={label}
      aria-label={label}
      className="grid size-11 shrink-0 place-items-center rounded-full bg-chip text-ink"
    >
      {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export function PageFrame({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  const kept = useKeptSearch();
  const width = wide ? "max-w-[1240px]" : "max-w-[1200px]";
  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className={`mx-auto flex ${width} items-center gap-3 px-6 py-[22px]`}>
        <Link to={HOME_PATH + kept} className="mr-auto text-[20px] leading-tight font-extrabold text-ink no-underline">
          Polarização no Twitter brasileiro
        </Link>
        <Link to={HOW_PATH + kept} className="min-w-0 text-right text-[16px] text-ink underline">
          Como as bolhas se formam
        </Link>
        <ThemeToggle />
      </header>
      <main className={`mx-auto ${width} px-6 pb-[120px]`}>{children}</main>
    </div>
  );
}

/** Espera o index.json e entrega à tela; erro sem retry automático. */
export function WithIndex({ children, wide }: { children: (index: Index) => ReactNode; wide?: boolean }) {
  const index = useIndex();
  if (index.status === "loading")
    return (
      <PageFrame wide={wide}>
        <Skeleton className="mt-8 h-64" />
      </PageFrame>
    );
  if (index.status === "error")
    return (
      <PageFrame wide={wide}>
        <ErrorBox error={index.error} />
      </PageFrame>
    );
  return <>{children(index.data)}</>;
}
