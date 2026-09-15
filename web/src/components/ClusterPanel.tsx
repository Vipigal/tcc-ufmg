import type { EventMeta } from "../types";
import { withAlpha } from "../lib/color";
import { formatCompact, formatInt, formatPct } from "../lib/format";
import { GLOSSARY } from "../lib/glossary";

interface Props {
  event: EventMeta;
  selected: number;
  onSelect: (community: number) => void;
}

/** RF2 / spec §7.2: um item por ClusterMeta na ordem `group`; rodapé com os parâmetros da fase 1. */
export function ClusterPanel({ event, selected, onSelect }: Props) {
  const rc = event.run_config;
  return (
    <section className="rounded-xl border border-line bg-white">
      <h2 className="px-4 pt-3 text-[11px] font-semibold uppercase tracking-wider text-muted">Clusters</h2>
      <ul className="mt-1">
        {event.clusters.map((c) => {
          const active = c.community === selected;
          return (
            <li key={c.community}>
              <button
                type="button"
                onClick={() => onSelect(c.community)}
                aria-pressed={active}
                className="w-full border-l-4 px-4 py-2 text-left hover:bg-gray-50"
                style={{
                  borderLeftColor: active ? c.color : "transparent",
                  backgroundColor: active ? withAlpha(c.color, 0.1) : undefined,
                }}
              >
                <div className="flex items-center gap-2 text-[14px]">
                  <span className="inline-block h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: c.color }} />
                  <span className="font-semibold">{c.label}</span>
                  <span className="text-muted">(c{c.community})</span>
                  <span className="ml-auto cursor-help" title={GLOSSARY.frac_nodes}>
                    {formatPct(c.frac_nodes)}
                  </span>
                  <span className="text-muted">K={c.k}</span>
                </div>
                <div className="mt-0.5 pl-5 text-[12px] text-muted">
                  <span className="cursor-help" title={GLOSSARY.intra_weight_frac}>
                    peso interno {formatPct(c.intra_weight_frac, 1)}
                  </span>
                  {" · "}
                  <span className="cursor-help" title={GLOSSARY.hydrated}>
                    {c.n_hydrated}/{c.n_selected} hidratados
                  </span>
                  {" · "}
                  <span className="cursor-help" title={GLOSSARY.attrition}>
                    atrição {formatPct(c.attrition)}
                  </span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
      <footer className="border-t border-line px-4 py-2 text-[12px] leading-5 text-muted">
        {formatInt(event.n_nodes)} nós · {formatCompact(event.n_edges)} arestas · {event.n_communities} comunidades
        <br />
        N={String(rc.min_user_retweets ?? "?")} τ={String(rc.tau ?? "?")} · K={event.selection.k}/{event.selection.k_small}
      </footer>
    </section>
  );
}
