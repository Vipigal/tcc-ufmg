import type { ClusterMeta } from "../types";
import { useGroupMap } from "../data/hooks";
import { pairNote } from "../lib/groupMap";
import { GraphStage } from "./GraphStage";
import { Skeleton } from "./States";

interface Props {
  slug: string;
  clusters: ClusterMeta[];
  selected: number;
  onSelect: (community: number) => void;
  labelOf: (community: number) => string;
}

/** Coluna do grafo na página do evento: imagem clicável e legenda de leitura. */
export function EventGraph({ slug, clusters, selected, onSelect, labelOf }: Props) {
  const map = useGroupMap(slug);
  return (
    <div className="max-w-[660px] min-w-0 flex-[3_1_420px]">
      {map.status === "loading" && <Skeleton className="aspect-square w-full rounded-[36px]" />}
      {map.status === "error" && (
        <p className="m-0 rounded-[24px] bg-soft p-5 text-[14px] text-muted">
          O grafo deste evento ainda não foi gerado (célula M12 do pipeline).
        </p>
      )}
      {map.status === "ready" && (
        <GraphStage slug={slug} map={map.data} clusters={clusters} selected={selected} onSelect={onSelect} />
      )}
      <p className="m-0 mx-1 mt-2.5 text-[13px] leading-normal text-muted">
        Toque num grupo para abri-lo: ele fica colorido e os demais, em cinza. Cada ponto é uma pessoa; quanto maior, mais
        ligações ela tem. A cor só identifica o grupo. As linhas são uma amostra das ligações mais fortes entre grupos.
        {map.status === "ready" && pairNote(map.data.dominant_pairs, labelOf) && (
          <> {pairNote(map.data.dominant_pairs, labelOf)}</>
        )}
      </p>
    </div>
  );
}
