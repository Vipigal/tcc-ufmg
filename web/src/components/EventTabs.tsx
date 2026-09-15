import type { EventMeta } from "../types";
import { formatDay } from "../lib/format";
import { EVENT_SHORT_NAMES } from "../lib/glossary";

interface Props {
  events: EventMeta[];
  activeSlug: string;
  onSelect: (meta: EventMeta) => void;
}

/** RF1: uma aba por evento do índice, com nome curto e data; a ativa fica sublinhada. */
export function EventTabs({ events, activeSlug, onSelect }: Props) {
  return (
    <nav aria-label="Eventos" className="flex gap-1 overflow-x-auto">
      {events.map((e) => {
        const active = e.slug === activeSlug;
        return (
          <button
            key={e.slug}
            type="button"
            onClick={() => onSelect(e)}
            title={e.name}
            aria-current={active ? "page" : undefined}
            className={`flex flex-col items-start rounded-lg px-3 py-1.5 text-left leading-tight hover:bg-gray-100 ${
              active ? "text-ink" : "text-muted"
            }`}
          >
            <span className={`text-[14px] font-semibold ${active ? "underline decoration-2 underline-offset-4" : ""}`}>
              {EVENT_SHORT_NAMES[e.slug] ?? e.name}
            </span>
            <span className="text-[11.5px]">{e.event_date ? formatDay(e.event_date) : "—"}</span>
          </button>
        );
      })}
    </nav>
  );
}
