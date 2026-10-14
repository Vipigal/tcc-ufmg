import { useMemo, useState } from "react";
import { ArrowRight, ChevronDown, ChevronUp } from "lucide-react";
import type { ClusterMeta, EventData, EventMeta, Slot, Tweet } from "../types";
import { formatPct } from "../lib/format";
import { clusterPath, comparePath } from "../lib/paths";
import { useNav, useShowTags } from "../lib/nav";
import { InclinationTag } from "../components/InclinationTag";
import { SummaryBody } from "../components/SummaryPanel";
import { TweetPreview } from "../components/TweetPreview";

interface Props {
  meta: EventMeta;
  data: EventData;
  a: ClusterMeta;
  b: ClusterMeta;
  labelOf: (community: number) => string;
}

const N_PREVIEWS = 3;

function hydrated(s: Slot): s is Slot & { tweet: Tweet } {
  return s.status === "hydrated" && s.tweet !== null;
}

/** Comparação lado a lado de dois grupos do mesmo evento (spec 2026-10-14 §2.3). */
export function Compare({ meta, data, a, b, labelOf }: Props) {
  const nav = useNav();
  const common = useMemo(() => {
    const ids = (c: number) => new Set(data.slots.filter((s) => s.community === c).map((s) => s.tweet_id));
    const ia = ids(a.community);
    const tweets = [...ids(b.community)].filter((t) => ia.has(t)).length;
    const accB = new Set(b.top_accounts.map((x) => x.author_id));
    const accounts = a.top_accounts.filter((x) => accB.has(x.author_id));
    return { tweets, accounts };
  }, [data.slots, a, b]);

  const pick = (side: "a" | "b", community: number) => {
    const [x, y] = side === "a" ? [community, b.community] : [a.community, community];
    if (x !== y) nav(comparePath(meta.slug, x, y));
  };

  return (
    <div className="space-y-3">
      <section className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-line bg-surface px-4 py-2.5 text-[13.5px]">
        <GroupSelect meta={meta} value={a} onChange={(c) => pick("a", c)} />
        <span className="text-muted">×</span>
        <GroupSelect meta={meta} value={b} onChange={(c) => pick("b", c)} />
        <span className="ml-auto text-muted">
          em comum:{" "}
          <b className="text-ink">{formatPct(a.shared_with?.[String(b.community)] ?? null)}</b> do que o {a.label}{" "}
          retuíta circula no {b.label};{" "}
          <b className="text-ink">{formatPct(b.shared_with?.[String(a.community)] ?? null)}</b> no sentido inverso ·{" "}
          {common.tweets} tweets nas duas seleções
          {common.accounts.length > 0 && (
            <> · contas: {common.accounts.slice(0, 4).map((x) => (x.username ? `@${x.username}` : x.name)).join(", ")}</>
          )}
        </span>
      </section>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Column meta={meta} cluster={a} slots={data.slots} labelOf={labelOf} onRead={(o) => nav(clusterPath(meta.slug, a.community), o)} />
        <Column meta={meta} cluster={b} slots={data.slots} labelOf={labelOf} onRead={(o) => nav(clusterPath(meta.slug, b.community), o)} />
      </div>
    </div>
  );
}

function GroupSelect({ meta, value, onChange }: { meta: EventMeta; value: ClusterMeta; onChange: (c: number) => void }) {
  return (
    <label className="inline-flex items-center gap-2 font-semibold">
      <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: value.color }} />
      <select className="select font-semibold" value={value.community} onChange={(e) => onChange(Number(e.target.value))}>
        {meta.clusters.map((c) => (
          <option key={c.community} value={c.community}>
            {c.label} · {formatPct(c.frac_nodes)}
          </option>
        ))}
      </select>
    </label>
  );
}

interface ColumnProps {
  meta: EventMeta;
  cluster: ClusterMeta;
  slots: Slot[];
  labelOf: (community: number) => string;
  onRead: (extra?: Record<string, string>) => void;
}

function Column({ cluster: c, slots, onRead }: ColumnProps) {
  const showTags = useShowTags();
  const [open, setOpen] = useState(false);
  const mine = slots.filter((s) => s.community === c.community && hydrated(s)) as (Slot & { tweet: Tweet })[];
  const amplified = mine.filter((s) => s.origin === "amplified").sort((x, y) => x.rank - y.rank).slice(0, N_PREVIEWS);
  const characteristic = mine
    .filter((s) => s.origin === "characteristic")
    .sort((x, y) => x.rank - y.rank)
    .slice(0, N_PREVIEWS);
  const s = c.summary;

  return (
    <section className="min-w-0 space-y-3">
      <div className="rounded-xl border border-line bg-surface px-4 py-3" style={{ borderTop: `3px solid ${c.color}` }}>
        <header className="flex flex-wrap items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: c.color }} />
          <h3 className="text-[16px] font-bold">{c.label}</h3>
          <span className="text-[13px] text-muted">{formatPct(c.frac_nodes)}</span>
          {showTags && c.curation && <InclinationTag eixo={c.curation.eixo} confianca={s?.inclinacao_politica.confianca} />}
        </header>
        {open && s ? (
          <div className="mt-2">
            <SummaryBody cluster={c} />
          </div>
        ) : (
          <p className="mt-1.5 text-[14.5px] leading-6">
            {c.curation ? `“${c.curation.trecho.join(" … ")}”` : (s?.sintese.slice(0, 280) ?? "Sem síntese.")}
          </p>
        )}
        {s && (
          <button type="button" onClick={() => setOpen((o) => !o)} className="mt-1 inline-flex items-center gap-1 text-[13px] text-x-blue hover:underline">
            {open ? (
              <>
                recolher <ChevronUp size={14} />
              </>
            ) : (
              <>
                síntese completa <ChevronDown size={14} />
              </>
            )}
          </button>
        )}
        <p className="mt-2 text-[13px] text-muted">
          quem mais é retuitado:{" "}
          <span className="text-ink">
            {c.top_accounts
              .slice(0, 5)
              .map((x) => (x.username ? `@${x.username}` : x.name))
              .join(" · ")}
          </span>
        </p>
      </div>

      <Previews
        title="mais amplificados"
        hint="os mais retuitados pelo grupo; podem circular também em outros"
        items={amplified}
        color={c.color}
        onMore={() => onRead({ origem: "amplified" })}
      />
      <Previews
        title="característicos"
        hint="o que este grupo retuitou bem mais que o resto do evento"
        items={characteristic}
        color={c.color}
        onMore={() => onRead({ origem: "characteristic" })}
      />
    </section>
  );
}

function Previews({
  title,
  hint,
  items,
  color,
  onMore,
}: {
  title: string;
  hint: string;
  items: (Slot & { tweet: Tweet })[];
  color: string;
  onMore: () => void;
}) {
  return (
    <div className="space-y-2">
      <h4 className="flex items-baseline gap-2 text-[12px] font-semibold uppercase tracking-wider text-muted">
        {title} <span className="font-normal normal-case tracking-normal">· {hint}</span>
        <button type="button" onClick={onMore} className="ml-auto inline-flex items-center gap-1 font-semibold normal-case tracking-normal text-x-blue hover:underline">
          ver todos <ArrowRight size={12} />
        </button>
      </h4>
      {items.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line-strong px-3 py-4 text-center text-[13px] text-muted">nenhum tweet disponível</p>
      ) : (
        items.map((s) => <TweetPreview key={`${s.origin}-${s.rank}`} slot={s} color={color} />)
      )}
    </div>
  );
}
