import type { EventMeta } from "../types";
import { TIMELINE_MARKS, storyFor } from "../content/events";
import { dayMonth, timelineScale } from "../lib/timeline";

interface Props {
  events: EventMeta[];
  selected: number;
  onSelect: (i: number) => void;
}

const left = (at: number) => `calc(12% + 76% * ${at})`;
const CROWDED = 0.12;

/** Linha do tempo com distâncias proporcionais aos dias entre os eventos. */
export function Timeline({ events, selected, onSelect }: Props) {
  const dated = events.flatMap((e) => (e.event_date ? [e.event_date] : []));
  if (dated.length === 0) return null;
  const scale = timelineScale(dated);
  const ats = events.map((e) => (e.event_date ? scale.at(e.event_date) : null));
  const lowered: boolean[] = [];
  ats.forEach((at, i) => {
    const prev = ats[i - 1];
    lowered.push(at !== null && prev != null && !lowered[i - 1] && at - prev < CROWDED);
  });
  return (
    <section aria-label="Linha do tempo" className="mt-12">
      <div className={`relative h-[72px] ${lowered.some(Boolean) ? "max-sm:h-[92px]" : ""}`}>
        <div aria-hidden className="absolute top-[27px] right-[12%] left-[12%] h-0.5 bg-line-strong" />
        {TIMELINE_MARKS.map((m) => (
          <div key={m.date}>
            <span
              className="absolute top-0 -translate-x-1/2 text-[12px] whitespace-nowrap text-faint"
              style={{ left: left(scale.at(m.date)) }}
            >
              {m.label}
            </span>
            <span aria-hidden className="absolute top-[22px] h-3 w-0.5 bg-rule" style={{ left: left(scale.at(m.date)) }} />
          </div>
        ))}
        {events.map((e, i) =>
          e.event_date ? (
            <button
              key={e.slug}
              type="button"
              onClick={() => onSelect(i)}
              aria-label={storyFor(e).full}
              aria-pressed={i === selected}
              className={`absolute top-[14px] size-7 -translate-x-1/2 cursor-pointer rounded-full border-[3px] border-ink p-0 ${
                i === selected ? "bg-ink" : "bg-bg"
              }`}
              style={{ left: left(scale.at(e.event_date)) }}
            >
              <span
                aria-hidden
                className={`absolute left-1/2 -translate-x-1/2 text-[13px] whitespace-nowrap text-ink top-7 ${lowered[i] ? "max-sm:top-12" : ""} ${
                  i === selected ? "font-extrabold" : "font-medium"
                }`}
              >
                {dayMonth(e.event_date)}
              </span>
            </button>
          ) : null,
        )}
      </div>
      <p className="m-0 text-center text-[13px] text-faint">
        Distâncias proporcionais ao tempo: {scale.days} dias do primeiro ao último evento.
      </p>
    </section>
  );
}
