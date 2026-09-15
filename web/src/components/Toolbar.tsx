import { Search, X } from "lucide-react";
import type { ExclusivityFilter, SortKey, StatusFilter, ToolbarState } from "../lib/filter";
import { DEFAULT_TOOLBAR } from "../lib/filter";

interface Props {
  state: ToolbarState;
  onChange: (next: ToolbarState) => void;
  shown: number;
  total: number;
}

const SORT_LABELS: Record<SortKey, string> = {
  rank: "ranking (padrão)",
  purity: "pureza",
  rt_graph: "RTs no grafo",
  api_retweets: "reposts na API",
  date: "mais antigo primeiro",
};
const STATUS_LABELS: Record<StatusFilter, string> = {
  all: "todos",
  hydrated: "só hidratados",
  ghost: "só não devolvidos",
};
const EXCLUSIVITY_LABELS: Record<ExclusivityFilter, string> = {
  all: "todos",
  exclusive: "exclusivos (pureza ≥ 0,90)",
  shared: "compartilhados (pureza < 0,50)",
};

function keys<K extends string>(labels: Record<K, string>): K[] {
  return Object.keys(labels) as K[];
}

/** RF9 / spec §7.7. O debounce da busca fica em quem consome `state.query` (CardList). */
export function Toolbar({ state, onChange, shown, total }: Props) {
  const set = <K extends keyof ToolbarState>(key: K, value: ToolbarState[K]) => onChange({ ...state, [key]: value });
  const dirty =
    state.sort !== DEFAULT_TOOLBAR.sort ||
    state.status !== DEFAULT_TOOLBAR.status ||
    state.exclusivity !== DEFAULT_TOOLBAR.exclusivity ||
    state.query !== DEFAULT_TOOLBAR.query;

  return (
    <div className="flex flex-wrap items-center gap-2 text-[13px]">
      <label className="flex items-center gap-1 text-muted">
        ordenar
        <select className="select" value={state.sort} onChange={(e) => set("sort", e.target.value as SortKey)}>
          {keys(SORT_LABELS).map((k) => (
            <option key={k} value={k}>
              {SORT_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1 text-muted">
        status
        <select className="select" value={state.status} onChange={(e) => set("status", e.target.value as StatusFilter)}>
          {keys(STATUS_LABELS).map((k) => (
            <option key={k} value={k}>
              {STATUS_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1 text-muted">
        exclusividade
        <select
          className="select"
          value={state.exclusivity}
          onChange={(e) => set("exclusivity", e.target.value as ExclusivityFilter)}
        >
          {keys(EXCLUSIVITY_LABELS).map((k) => (
            <option key={k} value={k}>
              {EXCLUSIVITY_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      <label className="relative flex items-center">
        <Search size={14} className="pointer-events-none absolute left-2 text-muted" />
        <input
          type="search"
          value={state.query}
          onChange={(e) => set("query", e.target.value)}
          placeholder="buscar no texto, nome ou @handle"
          aria-label="buscar"
          className="select w-64 pl-7"
        />
      </label>
      <span className="ml-auto text-muted">
        mostrando {shown} de {total}
      </span>
      {dirty && (
        <button type="button" onClick={() => onChange(DEFAULT_TOOLBAR)} className="chip">
          <X size={12} /> limpar
        </button>
      )}
    </div>
  );
}
