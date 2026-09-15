import { useEffect, useMemo, useState } from "react";
import type { ClusterMeta, Slot, Tweet } from "../types";
import { applyToolbar, DEFAULT_TOOLBAR, type ToolbarState } from "../lib/filter";
import { useDebounce } from "../lib/useDebounce";
import { GhostCard } from "./GhostCard";
import { Toolbar } from "./Toolbar";
import { TweetCard } from "./TweetCard";

interface Props {
  cluster: ClusterMeta;
  slots: Slot[]; // só os do cluster, na ordem do ranking
  toolbar: ToolbarState;
  onToolbarChange: (next: ToolbarState) => void;
}

/** Cards montados no primeiro commit e por bloco a cada frame depois. Medido em 2026-09-15 (Chrome 153, GTX 1070 Ti):
 *  montar 100 cards de uma vez custava ~200 ms em produção e ~700–1000 ms em dev; com 12 + blocos de 10 a troca
 *  de cluster pinta em ~250 ms em dev e o resto preenche sem bloquear a interação. */
const INITIAL_CARDS = 12;
const CARDS_PER_FRAME = 10;

function isHydrated(s: Slot): s is Slot & { tweet: Tweet } {
  return s.status === "hydrated" && s.tweet !== null;
}

/** RF4 + RF9: cabeçalho, barra de ferramentas e um card por slot visível (hidratado ou fantasma). */
export function CardList({ cluster, slots, toolbar, onToolbarChange }: Props) {
  // A busca entra com debounce; ordenação e filtros, imediatos. Cards são memoizados, então
  // uma tecla digitada só reconcilia os <li> — não re-renderiza 100 cards.
  const query = useDebounce(toolbar.query, 200);
  const { sort, status, exclusivity } = toolbar;
  const visible = useMemo(
    () => applyToolbar(slots, { sort, status, exclusivity, query }),
    [slots, sort, status, exclusivity, query],
  );
  const ghosts = cluster.n_selected - cluster.n_hydrated;

  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-center gap-x-2 text-[15px]">
        <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: cluster.color }} />
        <h2 className="font-bold">
          {cluster.label} <span className="font-normal text-muted">(c{cluster.community})</span>
        </h2>
        <span className="text-muted">
          · {cluster.n_selected} slots · {cluster.n_hydrated} hidratados · {ghosts} não devolvidos
        </span>
      </header>
      <Toolbar state={toolbar} onChange={onToolbarChange} shown={visible.length} total={cluster.n_selected} />
      {visible.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-muted">
          nenhum tweet com esses filtros
          <div className="mt-3">
            <button type="button" className="chip" onClick={() => onToolbarChange(DEFAULT_TOOLBAR)}>
              limpar
            </button>
          </div>
        </div>
      ) : (
        // key: qualquer mudança de cluster/ordem/filtro/busca recomeça a lista progressiva do zero
        <ProgressiveList
          key={`${cluster.community}|${sort}|${status}|${exclusivity}|${query}`}
          items={visible}
          color={cluster.color}
        />
      )}
    </div>
  );
}

/** Renderiza `items` em blocos: os primeiros no commit da mudança, os demais um bloco por frame. */
function ProgressiveList({ items, color }: { items: Slot[]; color: string }) {
  const [shown, setShown] = useState(INITIAL_CARDS);
  useEffect(() => {
    if (shown >= items.length) return;
    const id = window.requestAnimationFrame(() => setShown((n) => Math.min(n + CARDS_PER_FRAME, items.length)));
    return () => window.cancelAnimationFrame(id);
  }, [shown, items.length]);

  return (
    <ol className="space-y-3">
      {items.slice(0, shown).map((s) => (
        <li key={`${s.community}-${s.rank}`}>
          {isHydrated(s) ? <TweetCard slot={s} color={color} /> : <GhostCard slot={s} color={color} />}
        </li>
      ))}
    </ol>
  );
}
