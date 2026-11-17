import type { MouseEvent } from "react";
import { useEffect, useState } from "react";
import type { ClusterMeta, GroupMap } from "../types";
import { formatPct } from "../lib/format";
import { groupAt, labelPlacement } from "../lib/groupMap";
import { groupColor } from "../lib/palette";
import { useTheme } from "../lib/theme";

interface Props {
  slug: string;
  map: GroupMap;
  clusters: ClusterMeta[];
  selected: number;
  onSelect: (community: number) => void;
}

function pointIn(e: MouseEvent<HTMLElement>): [number, number] {
  const r = e.currentTarget.getBoundingClientRect();
  return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height];
}

/** O grafo do evento (imagem do M12) com os grupos clicáveis: pela região da imagem ou pelo rótulo. */
export function GraphStage({ slug, map, clusters, selected, onSelect }: Props) {
  const { theme } = useTheme();
  const [hover, setHover] = useState<number | null>(null);
  const known = new Map(clusters.map((c) => [c.community, c]));
  const at = (e: MouseEvent<HTMLElement>) => {
    const c = groupAt(map.grid, ...pointIn(e));
    return c !== null && known.has(c) ? c : null;
  };
  const file = theme === "dark" ? "escuro" : "claro";
  const [plain, setPlain] = useState(false);
  // Uma imagem por grupo em destaque (o grupo colorido, os demais em cinza); sem ela, cai na imagem colorida.
  const src = plain ? `/${slug}/grafo-${file}.webp` : `/${slug}/grafo-${file}-g${selected}.webp`;
  useEffect(() => {
    for (const g of map.groups) new Image().src = `/${slug}/grafo-${file}-g${g.community}.webp`;
  }, [slug, file, map.groups]);

  return (
    <div className="relative aspect-square w-full overflow-hidden rounded-[36px] bg-[var(--bg)] shadow-[0_0_0_1.5px_var(--line)]">
      <img
        src={src}
        onError={() => setPlain(true)}
        alt="Grafo do evento: cada ponto é uma pessoa; o grupo aberto aparece colorido e os demais em cinza."
        className={`block h-full w-full select-none ${hover !== null ? "cursor-pointer" : ""}`}
        draggable={false}
        onClick={(e) => {
          const c = at(e);
          if (c !== null) onSelect(c);
        }}
        onMouseMove={(e) => setHover(at(e))}
        onMouseLeave={() => setHover(null)}
      />
      {map.groups.map((g) => {
        const c = known.get(g.community);
        if (!c) return null;
        const on = g.community === selected;
        const place = labelPlacement(g);
        const lit = on || g.community === hover;
        return (
          <button
            key={g.community}
            type="button"
            onClick={() => onSelect(g.community)}
            aria-pressed={on}
            className="absolute cursor-pointer rounded-full border-2 px-2.5 py-0.5 text-[13px] font-extrabold whitespace-nowrap"
            style={{
              left: `${place.x * 100}%`,
              top: `${place.y * 100}%`,
              // Desloca o rótulo na proporção da posição: perto da borda esquerda ele cresce para a direita e vice-versa.
              transform: `translate(-${place.x * 100}%, ${place.anchor === "bottom" ? "-100%" : "0"})`,
              borderColor: lit ? groupColor(g.group) : "var(--line-strong)",
              background: lit ? groupColor(g.group) : "var(--bg)",
              color: lit ? "#FFFFFF" : "var(--muted)",
            }}
          >
            {c.label} · {formatPct(c.frac_nodes)}
          </button>
        );
      })}
    </div>
  );
}
