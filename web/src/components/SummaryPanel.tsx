import type { ReactNode } from "react";
import { Fragment, useState } from "react";
import { BadgeCheck, ChevronDown, ChevronUp, Sparkles, TriangleAlert } from "lucide-react";
import type { ClusterMeta } from "../types";
import { withAlpha } from "../lib/color";
import { formatInt } from "../lib/format";
import { CONFIDENCE_TEXT, GLOSSARY } from "../lib/glossary";
import { useShowTags } from "../lib/nav";
import { InclinationTag } from "./InclinationTag";

interface Props {
  cluster: ClusterMeta;
}

/** Cabeça do id de um card na lista (CardList). A síntese leva a ele pelas citações. */
export const tweetAnchorId = (tweetId: string) => `tweet-${tweetId}`;

const CITATION = /\[([\d,;\s]+)\]/g;

/**
 * Síntese por LLM do cluster (M11, D8 revisado em 2026-10-13) + contas mais retuitadas (calculadas).
 * É ajuda de leitura para os rotuladores, não categorização. As citações `[id]` levam ao card do tweet;
 * as que o modelo citou fora do corpus do cluster aparecem riscadas.
 */
export function SummaryPanel({ cluster }: Props) {
  const s = cluster.summary;
  const showTags = useShowTags();
  const [open, setOpen] = useState(true);
  return (
    <section
      className="space-y-3 rounded-xl border border-line bg-surface px-4 py-3 text-[14px] leading-6"
      style={{ borderTop: `3px solid ${cluster.color}` }}
    >
      <header className="flex flex-wrap items-center gap-2 text-[12px] text-muted">
        <Sparkles size={14} />
        <span className="font-semibold uppercase tracking-wider">Síntese por LLM</span>
        {showTags && cluster.curation && (
          <InclinationTag eixo={cluster.curation.eixo} confianca={s?.inclinacao_politica.confianca} />
        )}
        {s && (
          <span title={GLOSSARY.summary} className="cursor-help">
            · {s.model} · prompt {s.prompt_version} · {s.generated_at.slice(0, 10)}
          </span>
        )}
        {s && s.invalid_ids.length > 0 && (
          <span className="inline-flex items-center gap-1 text-orange-700 dark:text-orange-400" title={GLOSSARY.invalid_ids}>
            <TriangleAlert size={13} /> {s.invalid_ids.length} citação(ões) fora do corpus
          </span>
        )}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="ml-auto inline-flex items-center gap-1 rounded px-1 hover:bg-hover hover:text-ink"
        >
          {open ? <>recolher <ChevronUp size={14} /></> : <>abrir <ChevronDown size={14} /></>}
        </button>
      </header>
      {open ? (
        <SummaryBody cluster={cluster} />
      ) : (
        cluster.curation && <p className="text-ink">“{cluster.curation.trecho.join(" … ")}”</p>
      )}
    </section>
  );
}

/** Corpo da síntese (blocos + contas), reutilizado na comparação. */
export function SummaryBody({ cluster }: Props) {
  const s = cluster.summary;
  const invalid = new Set(s?.invalid_ids ?? []);
  return (
    <div className="space-y-3 text-[14px] leading-6">
      {s ? (
        <>
          <Block title="O que circulou">{cite(s.sintese, invalid)}</Block>
          <Block title="Contas prevalentes">{cite(s.contas_prevalentes, invalid)}</Block>
          <Block
            title="Inclinação política provável"
            aside={
              <span
                className="rounded-full px-2 text-[12px] font-semibold"
                style={{ backgroundColor: withAlpha(cluster.color, 0.15) }}
                title={GLOSSARY.confidence}
              >
                confiança {CONFIDENCE_TEXT[s.inclinacao_politica.confianca]}
              </span>
            }
          >
            {cite(s.inclinacao_politica.texto, invalid)}
          </Block>
          <Block title="Limites">{cite(s.limites, invalid)}</Block>
        </>
      ) : (
        <p className="text-muted">Síntese por LLM ainda não gerada para este cluster.</p>
      )}
      <TopAccounts cluster={cluster} />
    </div>
  );
}

function Block({ title, aside, children }: { title: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <div>
      <h3 className="flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wider text-muted">
        {title} {aside}
      </h3>
      <p className="mt-0.5 whitespace-pre-line">{children}</p>
    </div>
  );
}

function TopAccounts({ cluster }: { cluster: ClusterMeta }) {
  if (cluster.top_accounts.length === 0) return null;
  return (
    <details>
      <summary className="cursor-pointer text-[12px] font-semibold uppercase tracking-wider text-muted">
        Contas mais retuitadas ({cluster.top_accounts.length})
      </summary>
      <ol className="mt-1 grid grid-cols-1 gap-x-6 text-[13px] sm:grid-cols-2" title={GLOSSARY.top_accounts}>
        {cluster.top_accounts.map((a, i) => (
          <li key={a.author_id} className="flex items-center gap-1.5 truncate">
            <span className="w-5 text-right text-muted">{i + 1}.</span>
            <span className="truncate font-semibold">{a.name ?? "—"}</span>
            {a.verified && <BadgeCheck size={13} className="shrink-0 text-x-blue" />}
            <span className="truncate text-muted">{a.username ? `@${a.username}` : `id ${a.author_id}`}</span>
            <span className="ml-auto shrink-0 text-muted">
              {formatInt(a.rt_cluster)} RTs · {a.n_tweets} tw
            </span>
          </li>
        ))}
      </ol>
    </details>
  );
}

/** Troca cada `[id, id]` por links para os cards; IDs fora do corpus ficam riscados. */
function cite(text: string, invalid: Set<string>): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(CITATION)) {
    out.push(text.slice(last, m.index));
    const ids = m[1].match(/\d+/g) ?? [];
    out.push(
      <sup key={m.index} className="text-[11px]">
        [
        {ids.map((id, i) => (
          <Fragment key={id}>
            {i > 0 && ", "}
            <CitationLink id={id} invalid={invalid.has(id)} />
          </Fragment>
        ))}
        ]
      </sup>,
    );
    last = m.index + m[0].length;
  }
  out.push(text.slice(last));
  return out;
}

function CitationLink({ id, invalid }: { id: string; invalid: boolean }) {
  if (invalid) {
    return (
      <span className="text-orange-700 dark:text-orange-400 line-through" title={GLOSSARY.invalid_ids}>
        {id.slice(-4)}
      </span>
    );
  }
  // Rola até o card; se ele estiver escondido por um filtro, abre o tweet no X.
  const onClick = (e: React.MouseEvent) => {
    const el = document.getElementById(tweetAnchorId(id));
    if (!el) return;
    e.preventDefault();
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("cite-flash");
    window.setTimeout(() => el.classList.remove("cite-flash"), 1600);
  };
  return (
    <a
      href={`https://x.com/i/web/status/${id}`}
      target="_blank"
      rel="noopener noreferrer"
      onClick={onClick}
      title={`tweet ${id}`}
      className="text-x-blue hover:underline"
    >
      {id.slice(-4)}
    </a>
  );
}
