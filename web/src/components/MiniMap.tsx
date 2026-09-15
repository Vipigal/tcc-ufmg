import { useEffect, useMemo, useRef } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import { LocateFixed } from "lucide-react";
import type { ClusterMeta, Layout } from "../types";
import { formatInt, formatPct } from "../lib/format";

/** Cinza da fase 1 para nós fora do cluster selecionado e comunidades < 1%. */
const GREY = "#c7ccd6";
const NODE_SIZE = 1.3;

interface Props {
  layout: Layout;
  clusters: ClusterMeta[];
  selected: number;
  onSelect: (community: number) => void;
}

/**
 * RF3 / spec §7.3: scatter das coordenadas DRL (componente gigante) em Sigma, nós apenas — nenhuma aresta.
 * O grafo é construído uma vez por `layout`; trocar a seleção só chama `refresh()` (o reducer lê um ref).
 * Rótulos "Grupo g · XX%" são HTML absoluto reposicionado em `afterRender` via `graphToViewport(centroid)`.
 * Orientação: o espaço `graph` do Sigma tem y para cima, igual ao matplotlib da figura da fase 1 — não inverter.
 */
export function MiniMap({ layout, clusters, selected, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const labelRefs = useRef(new Map<number, HTMLButtonElement>());

  // refs lidos pelo reducer e pelos handlers, para não reconstruir o Sigma a cada mudança
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const colorByCommunity = useMemo(() => new Map(clusters.map((c) => [c.community, c.color])), [clusters]);
  const colorRef = useRef(colorByCommunity);
  colorRef.current = colorByCommunity;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const graph = new Graph({ type: "undirected" });
    const n = layout.x.length;
    for (let i = 0; i < n; i++) {
      graph.addNode(String(i), {
        x: layout.x[i],
        y: layout.y[i],
        size: NODE_SIZE,
        color: GREY,
        community: layout.community[i],
      });
    }

    const sigma = new Sigma(graph, container, {
      renderLabels: false,
      enableEdgeEvents: false,
      allowInvalidContainer: true,
      nodeReducer: (_node, data) => {
        const community = data.community as number;
        const color = community === selectedRef.current ? (colorRef.current.get(community) ?? GREY) : GREY;
        return { ...data, color };
      },
    });

    sigma.on("clickNode", ({ node }) => {
      onSelectRef.current(graph.getNodeAttribute(node, "community") as number);
    });

    const placeLabels = () => {
      for (const [community, el] of labelRefs.current) {
        const centroid = layout.centroids[String(community)];
        if (!centroid) continue;
        const p = sigma.graphToViewport({ x: centroid[0], y: centroid[1] });
        el.style.transform = `translate(-50%, -50%) translate(${p.x}px, ${p.y}px)`;
      }
    };
    sigma.on("afterRender", placeLabels);
    placeLabels();

    sigmaRef.current = sigma;
    return () => {
      sigma.kill();
      sigmaRef.current = null;
    };
  }, [layout]);

  // seleção mudou → recolorir sem reconstruir (o reducer lê selectedRef)
  useEffect(() => {
    if (!sigmaRef.current) return;
    performance.mark("minimap:refresh:start");
    sigmaRef.current.refresh({ skipIndexation: true });
    performance.measure("minimap:refresh", "minimap:refresh:start");
  }, [selected, colorByCommunity]);

  return (
    <div className="relative h-[360px] w-full overflow-hidden rounded-xl border border-line bg-white">
      <div ref={containerRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute inset-0">
        {clusters.map((c) => (
          <button
            key={c.community}
            type="button"
            ref={(el) => {
              if (el) labelRefs.current.set(c.community, el);
              else labelRefs.current.delete(c.community);
            }}
            onClick={() => onSelect(c.community)}
            title={`${c.label} (c${c.community}) — clique para selecionar`}
            className="label-halo pointer-events-auto absolute left-0 top-0 whitespace-nowrap text-[13px] font-bold"
            style={{ color: c.color, opacity: c.community === selected ? 1 : 0.8 }}
          >
            {c.label} · {formatPct(c.frac_nodes)}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => sigmaRef.current?.getCamera().animatedReset({ duration: 300 })}
        title="recentrar"
        className="absolute right-2 top-2 rounded-md border border-line bg-white/90 p-1 text-muted hover:text-ink"
      >
        <LocateFixed size={14} />
      </button>
      <div className="pointer-events-none absolute bottom-1 left-2 text-[10.5px] text-muted">
        {formatInt(layout.n_plotted)} nós da componente gigante · layout DRL
      </div>
    </div>
  );
}
