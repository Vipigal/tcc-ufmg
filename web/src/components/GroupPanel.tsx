import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import type { ClusterMeta } from "../types";
import { formatInt } from "../lib/format";
import { AXIS_TEXT, CONFIDENCE_TEXT } from "../lib/glossary";
import { axisColors, groupColor, shownAxis } from "../lib/palette";
import { bubbleSentence } from "../lib/shared";
import { CitedText } from "./CitedText";

interface SideProps {
  cluster: ClusterMeta;
  clusters: ClusterMeta[];
  compareWith: number | null;
  showTags: boolean;
  labels: Map<string, string>;
  labelOf: (community: number) => string;
  onCompare: (community: number | null) => void;
  onCite: (tweetId: string) => void;
}

/** Quadro recolhível da coluna lateral. */
function Fold({ title, open, tint, children }: { title: string; open?: boolean; tint?: string; children: ReactNode }) {
  return (
    <details open={open} className="group rounded-3xl bg-soft" style={tint ? { background: tint } : undefined}>
      <summary className="flex min-h-12 cursor-pointer list-none items-center gap-3 px-5 py-3 text-[16px] font-extrabold [&::-webkit-details-marker]:hidden">
        <span className="mr-auto">{title}</span>
        <ChevronDown size={18} aria-hidden className="shrink-0 transition-transform group-open:rotate-180" />
      </summary>
      <div className="px-5 pb-[18px]">{children}</div>
    </details>
  );
}

/** Coluna ao lado do grafo: o grupo aberto, a comparação e os quadros de leitura, empilhados e recolhíveis. */
export function GroupSide({ cluster, clusters, compareWith, showTags, labels, labelOf, onCompare, onCite }: SideProps) {
  const eixo = shownAxis(cluster, showTags);
  const colors = axisColors(eixo);
  const s = cluster.summary;
  return (
    <section aria-live="polite" className="grid min-w-0 flex-[2_1_340px] content-start gap-3">
      <div className="rounded-[32px] p-[clamp(20px,3vw,28px)]" style={{ background: colors.tint }}>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <h2 className="m-0 flex items-center gap-3 text-[clamp(30px,3.4vw,44px)] leading-none font-extrabold tracking-[-0.035em]" style={{ color: colors.ink }}>
            <span aria-hidden className="inline-block size-[0.55em] shrink-0 rounded-full" style={{ background: groupColor(cluster.group) }} />
            {cluster.label}
          </h2>
          {eixo && (
            <span className="inline-flex min-h-9 items-center rounded-full px-4 text-[16px] font-extrabold text-bg" style={{ background: colors.ink }}>
              {AXIS_TEXT[eixo]}
            </span>
          )}
        </div>
        <p className="m-0 mt-3 text-[17px] leading-normal">{bubbleSentence(cluster, labelOf)}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-[15px]">Comparar com</span>
          {clusters
            .filter((c) => c.community !== cluster.community)
            .map((c) => {
              const on = compareWith === c.community;
              const other = axisColors(shownAxis(c, showTags));
              return (
                <button
                  key={c.community}
                  type="button"
                  aria-pressed={on}
                  onClick={() => onCompare(on ? null : c.community)}
                  className="min-h-10 cursor-pointer rounded-full border-2 px-4 text-[15px] font-bold"
                  style={
                    on
                      ? { background: other.ink, color: "var(--bg)", borderColor: other.ink }
                      : { background: "var(--bg)", color: other.ink, borderColor: other.line }
                  }
                >
                  {c.label}
                </button>
              );
            })}
        </div>
      </div>

      {showTags && s && (
        <Fold title={eixo ? `Por que "${AXIS_TEXT[eixo]}"` : "Inclinação provável, segundo o modelo"} open tint={colors.tint}>
          <p className="m-0 text-[15px] leading-[1.55]">
            <CitedText text={s.inclinacao_politica.texto} labels={labels} onCite={onCite} />
          </p>
          <p className="m-0 mt-2 text-[13px] text-muted">
            Palpite do modelo sobre o conteúdo, não sobre as pessoas. Confiança declarada:{" "}
            {CONFIDENCE_TEXT[s.inclinacao_politica.confianca]}.
          </p>
        </Fold>
      )}
      {cluster.top_accounts.length > 0 && (
        <Fold title="Contas mais retuitadas">
          <ol className="m-0 grid gap-1.5 pl-5 text-[15px]">
            {cluster.top_accounts.slice(0, 5).map((a) => (
              <li key={a.author_id}>
                {a.username ? `@${a.username}` : (a.name ?? "conta indisponível")}{" "}
                <span className="text-faint">{formatInt(a.rt_cluster)}</span>
              </li>
            ))}
          </ol>
        </Fold>
      )}
      {s && (
        <Fold title="O que não dá para afirmar">
          <p className="m-0 text-[15px] leading-[1.55]">
            <CitedText text={s.limites} labels={labels} onCite={onCite} />
          </p>
        </Fold>
      )}
    </section>
  );
}

/** A síntese do modelo em largura cheia, abaixo do grafo e da coluna lateral. */
export function GroupSynthesis({
  cluster,
  labels,
  onCite,
}: Pick<SideProps, "cluster" | "labels" | "onCite">) {
  const s = cluster.summary;
  return (
    <article className="mt-8 rounded-[32px] bg-bg p-[clamp(20px,3vw,36px)] shadow-[0_0_0_1.5px_var(--line)]">
      <h3 className="m-0 mb-1 text-[24px] font-extrabold tracking-[-0.02em]">O que circulou nesta bolha</h3>
      {s ? (
        <>
          <p className="m-0 mb-4 text-[14px] text-muted">
            Síntese de um modelo de linguagem a partir dos tweets recuperados. Os números levam aos tweets abaixo.
          </p>
          <div className="gap-x-12 min-[1000px]:columns-2">
            {s.sintese.split(/\n\s*\n/).map((p, i) => (
              <p key={i} className="m-0 mb-3.5 text-[18px] leading-[1.65]">
                <CitedText text={p} labels={labels} onCite={onCite} />
              </p>
            ))}
          </div>
        </>
      ) : (
        <p className="m-0 text-[16px] text-muted">A síntese desta bolha ainda não foi gerada.</p>
      )}
    </article>
  );
}
