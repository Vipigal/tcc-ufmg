import { Fragment } from "react";
import { ExternalLink } from "lucide-react";
import type { Slot } from "../types";
import { withAlpha } from "../lib/color";
import { EXCLUSIVE_MIN_PURITY, SHARED_MAX_PURITY } from "../lib/filter";
import { formatDec, formatInt } from "../lib/format";
import { GLOSSARY } from "../lib/glossary";

interface Props {
  slot: Slot;
  color: string;
}

interface Item {
  key: string;
  text: string;
  title: string;
  className?: string;
}

/**
 * RF6 / spec §7.6: faixa de metadados da pesquisa, presente em todo card (hidratado ou fantasma).
 * Fecha com o link para o tweet original no X, pedido pelo autor em 2026-09-15 para valer em todos os cards.
 * Todos os números vêm do slot; a única conta é a razão API/evento pedida pelo spec.
 */
export function ResearchStrip({ slot, color }: Props) {
  const apiRetweets = slot.tweet?.metrics.retweet_count ?? null;
  const items: Item[] = [
    { key: "rank", text: `#${slot.rank} de ${slot.k}`, title: GLOSSARY.rank, className: "font-semibold text-ink" },
    { key: "rt_cluster", text: `${formatInt(slot.rt_cluster)} RTs de membros`, title: GLOSSARY.rt_cluster },
    { key: "purity", text: `pureza ${formatDec(slot.purity, 2)}`, title: GLOSSARY.purity, className: purityClass(slot.purity) },
    { key: "rt_graph", text: `${formatInt(slot.rt_graph)} no grafo`, title: GLOSSARY.rt_graph },
    { key: "rt_event", text: `${formatInt(slot.rt_event)} no evento`, title: GLOSSARY.rt_event },
  ];
  if (apiRetweets != null) {
    const ratio = slot.rt_event > 0 ? `${formatDec(apiRetweets / slot.rt_event, 1)}×` : "—";
    items.push({ key: "api", text: `API ${formatInt(apiRetweets)} (${ratio})`, title: GLOSSARY.api });
  }
  for (const a of slot.also_in) {
    items.push({ key: `also-${a.community}`, text: `também em Grupo ${a.group} (#${a.rank})`, title: GLOSSARY.also_in });
  }

  return (
    <div
      className="flex flex-wrap items-center gap-x-1.5 gap-y-1 border-t border-line px-4 py-2 text-[12.5px] text-muted"
      style={{ backgroundColor: withAlpha(color, 0.06) }}
    >
      {items.map((it, i) => (
        <Fragment key={it.key}>
          {i > 0 && <span aria-hidden>·</span>}
          <span title={it.title} className={`cursor-help ${it.className ?? ""}`}>
            {it.text}
          </span>
        </Fragment>
      ))}
      <a
        href={`https://x.com/i/web/status/${slot.tweet_id}`}
        target="_blank"
        rel="noopener noreferrer"
        title="abrir o tweet original no X (nova aba)"
        className="ml-auto inline-flex items-center gap-1 whitespace-nowrap text-x-blue hover:underline"
      >
        abrir no X <ExternalLink size={12} />
      </a>
    </div>
  );
}

/** Sinalização de leitura (spec §7.6): ≥ 0,90 verde-escuro discreto; < 0,50 laranja discreto; entre, neutro. */
function purityClass(purity: number | null): string {
  if (purity == null) return "";
  if (purity >= EXCLUSIVE_MIN_PURITY) return "text-emerald-800";
  if (purity < SHARED_MAX_PURITY) return "text-orange-700";
  return "";
}
