import { LayoutGrid, Moon, Rows3, Sun, GitCompareArrows } from "lucide-react";
import type { Mode } from "../lib/paths";
import { useTheme } from "../lib/theme";

const MODES: { mode: Mode; label: string; icon: typeof LayoutGrid }[] = [
  { mode: "overview", label: "Visão geral", icon: LayoutGrid },
  { mode: "reader", label: "Ler grupo", icon: Rows3 },
  { mode: "compare", label: "Comparar", icon: GitCompareArrows },
];

/** Seletor fixo de tela (spec 2026-10-14 §2). */
export function ModeSwitch({ mode, onSelect }: { mode: Mode; onSelect: (m: Mode) => void }) {
  return (
    <nav aria-label="Tela" className="flex rounded-full border border-line p-0.5 text-[13px]">
      {MODES.map(({ mode: m, label, icon: Icon }) => (
        <button
          key={m}
          type="button"
          onClick={() => onSelect(m)}
          aria-current={m === mode ? "page" : undefined}
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-semibold ${
            m === mode ? "bg-ink text-bg" : "text-muted hover:text-ink"
          }`}
        >
          <Icon size={14} /> {label}
        </button>
      ))}
    </nav>
  );
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const dark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      title={dark ? "usar tema claro" : "usar tema escuro"}
      aria-label={dark ? "usar tema claro" : "usar tema escuro"}
      className="rounded-full border border-line p-1.5 text-muted hover:bg-hover hover:text-ink"
    >
      {dark ? <Sun size={15} /> : <Moon size={15} />}
    </button>
  );
}
