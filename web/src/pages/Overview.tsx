import { useState } from "react";
import { ArrowRight, GitCompareArrows } from "lucide-react";
import type { ClusterMeta, EventData, EventMeta } from "../types";
import { withAlpha } from "../lib/color";
import { formatPct } from "../lib/format";
import { clusterPath, comparePath } from "../lib/paths";
import { useNav, useShowTags } from "../lib/nav";
import { InclinationTag } from "../components/InclinationTag";
import { MethodExplainer } from "../components/MethodExplainer";
import { MiniMap } from "../components/MiniMap";
import { SharedBar } from "../components/SharedBar";

interface Props {
  meta: EventMeta;
  data: EventData;
  labelOf: (community: number) => string;
}

/**
 * Visão geral do evento (spec 2026-10-14 §2.1): mini-mapa com todos os grupos coloridos e um cartão por
 * grupo — trecho curado, contas, barra de conteúdo compartilhado e tag. Entrada padrão do evento.
 */
export function Overview({ meta, data, labelOf }: Props) {
  const nav = useNav();
  const [picked, setPicked] = useState<number[]>([]);
  const toggle = (c: number) =>
    setPicked((p) => (p.includes(c) ? p.filter((x) => x !== c) : [...p.slice(-1), c]));

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[440px_minmax(0,1fr)]">
      <aside className="space-y-3 xl:sticky xl:top-[61px] xl:self-start">
        <MiniMap
          layout={data.layout}
          clusters={meta.clusters}
          selected={null}
          onSelect={(c) => nav(clusterPath(meta.slug, c))}
          height={420}
        />
        <MethodExplainer />
      </aside>
      <section className="min-w-0 space-y-3">
        <header className="flex flex-wrap items-center gap-3">
          <h2 className="text-[17px] font-bold">{meta.name}</h2>
          <span className="text-[13px] text-muted">
            {meta.clusters.length} grupos · marque dois em "comparar" para vê-los lado a lado
          </span>
          {picked.length === 2 && (
            <button
              type="button"
              onClick={() => nav(comparePath(meta.slug, picked[0], picked[1]))}
              className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-ink px-3 py-1.5 text-[13px] font-semibold text-bg hover:opacity-90"
            >
              comparar {labelOf(picked[0])} × {labelOf(picked[1])} <ArrowRight size={14} />
            </button>
          )}
        </header>
        <ol className="space-y-3">
          {meta.clusters.map((c) => (
            <li key={c.community}>
              <ClusterCard
                cluster={c}
                labelOf={labelOf}
                picked={picked.includes(c.community)}
                onPick={() => toggle(c.community)}
                onRead={() => nav(clusterPath(meta.slug, c.community))}
              />
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

interface CardProps {
  cluster: ClusterMeta;
  labelOf: (community: number) => string;
  picked: boolean;
  onPick: () => void;
  onRead: () => void;
}

function ClusterCard({ cluster: c, labelOf, picked, onPick, onRead }: CardProps) {
  const showTags = useShowTags();
  const accounts = c.top_accounts.slice(0, 3);
  return (
    <article
      className="rounded-xl border border-line bg-surface px-4 py-3"
      style={{
        borderLeft: `4px solid ${c.color}`,
        outline: picked ? `2px solid ${c.color}` : undefined,
        backgroundColor: picked ? withAlpha(c.color, 0.08) : undefined,
      }}
    >
      <header className="flex flex-wrap items-center gap-2">
        <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: c.color }} />
        <h3 className="text-[16px] font-bold">{c.label}</h3>
        <span className="text-[13px] text-muted">{formatPct(c.frac_nodes)} dos usuários</span>
        {showTags && c.curation && <InclinationTag eixo={c.curation.eixo} />}
      </header>

      {c.curation ? (
        <blockquote className="mt-1.5 text-[15px] leading-6 text-ink">
          “{c.curation.trecho.join(" … ")}”
          {c.curation.stale && (
            <span className="ml-1 text-[12px] text-orange-700 dark:text-orange-400" title="há síntese mais nova que a curada">
              (curadoria desatualizada)
            </span>
          )}
        </blockquote>
      ) : (
        <p className="mt-1.5 text-[14px] text-muted">Síntese ainda não curada para este grupo.</p>
      )}

      {accounts.length > 0 && (
        <p className="mt-1.5 truncate text-[13px] text-muted">
          quem mais é retuitado:{" "}
          {accounts.map((a, i) => (
            <span key={a.author_id}>
              {i > 0 && " · "}
              <span className="text-ink">{a.username ? `@${a.username}` : (a.name ?? `id ${a.author_id}`)}</span>
            </span>
          ))}
        </p>
      )}

      <div className="mt-2">
        <SharedBar cluster={c} labelOf={labelOf} />
      </div>

      <footer className="mt-2 flex items-center gap-4 text-[13px]">
        <button type="button" onClick={onRead} className="inline-flex items-center gap-1 font-semibold text-x-blue hover:underline">
          ler o grupo <ArrowRight size={14} />
        </button>
        <label className="inline-flex cursor-pointer items-center gap-1.5 text-muted hover:text-ink">
          <input type="checkbox" checked={picked} onChange={onPick} className="accent-current" />
          <GitCompareArrows size={14} /> comparar
        </label>
      </footer>
    </article>
  );
}
