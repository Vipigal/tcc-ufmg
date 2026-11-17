import { useCallback, useMemo, useState } from "react";
import { Link, Navigate, useParams, useSearchParams } from "react-router-dom";
import type { ClusterMeta, EventData, EventMeta, SlotOrigin } from "../types";
import { PageFrame, WithIndex } from "../App";
import { storyFor } from "../content/events";
import { useEvent } from "../data/hooks";
import { formatDay, formatInt } from "../lib/format";
import { useKeptSearch, useNav, useShowTags } from "../lib/nav";
import { axisColors, shownAxis } from "../lib/palette";
import { COMPARE_PARAM, HOME_PATH, bubblePath, pickBubble, pickCompare } from "../lib/paths";
import { slotLabel } from "../lib/thread";
import { Comparison } from "../components/Comparison";
import { EventGraph } from "../components/EventGraph";
import { GroupSide, GroupSynthesis } from "../components/GroupPanel";
import { ErrorBox, Skeleton } from "../components/States";
import { TweetThread } from "../components/TweetThread";

export function EventPage() {
  const { evento } = useParams();
  const kept = useKeptSearch();
  return (
    <WithIndex>
      {(index) => {
        const meta = index.events.find((e) => e.slug === evento);
        return meta ? <EventLoader meta={meta} /> : <Navigate to={HOME_PATH + kept} replace />;
      }}
    </WithIndex>
  );
}

function EventLoader({ meta }: { meta: EventMeta }) {
  const event = useEvent(meta);
  const story = storyFor(meta);
  const kept = useKeptSearch();
  return (
    <PageFrame>
      <Link to={HOME_PATH + kept} className="text-[15px] text-ink underline">
        Os quatro eventos
      </Link>
      <h1 className="m-0 mt-3 mb-2.5 text-[clamp(36px,4.6vw,60px)] leading-none font-extrabold tracking-[-0.035em]">
        {meta.event_date ? formatDay(meta.event_date) : meta.name}
      </h1>
      <p className="m-0 max-w-[40em] text-[18px] leading-normal text-muted">
        {formatInt(meta.n_nodes)} pessoas retuitaram sobre {story.about}. Toque num grupo para abri-lo.
      </p>
      {story.text && (
        <details className="mt-3 max-w-[760px]">
          <summary className="min-h-8 cursor-pointer text-[16px] font-bold">O que aconteceu neste dia</summary>
          <p className="m-0 mt-2.5 mb-1.5 text-[17px] leading-[1.65]">{story.text}</p>
          <p className="m-0 text-[15px]">
            Fontes:{" "}
            {story.sources.map((s, i) => (
              <span key={s.url}>
                {i > 0 && ", "}
                <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-ink underline">
                  {s.label}
                </a>
              </span>
            ))}
          </p>
        </details>
      )}
      {event.status === "loading" && <Skeleton className="mt-7 h-[420px]" />}
      {event.status === "error" && <ErrorBox error={event.error} />}
      {event.status === "ready" && <EventBody meta={meta} data={event.data} />}
    </PageFrame>
  );
}

function EventBody({ meta, data }: { meta: EventMeta; data: EventData }) {
  const { community } = useParams();
  const [search] = useSearchParams();
  const nav = useNav();
  const showTags = useShowTags();
  const cluster = pickBubble(meta.clusters, community);
  const compareWith = cluster ? pickCompare(meta.clusters, cluster.community, search.get(COMPARE_PARAM)) : undefined;
  const [origin, setOrigin] = useState<SlotOrigin>("amplified");
  const [focus, setFocus] = useState<{ tweetId: string; seq: number } | null>(null);
  const eixo = cluster ? shownAxis(cluster, showTags) : null;
  const colors = useMemo(() => axisColors(eixo), [eixo]);

  const mine = useMemo(() => data.slots.filter((s) => s.community === cluster?.community), [data, cluster?.community]);
  const labels = useMemo(
    () => new Map(mine.filter((s) => s.status === "hydrated" && s.tweet !== null).map((s) => [s.tweet_id, slotLabel(s)])),
    [mine],
  );
  const labelOf = useCallback(
    (c: number) => meta.clusters.find((x) => x.community === c)?.label ?? "grupos menores",
    [meta.clusters],
  );
  const onCite = useCallback(
    (tweetId: string) => {
      const target = mine.find((s) => s.tweet_id === tweetId && s.status === "hydrated");
      if (!target) return;
      setOrigin(target.origin);
      setFocus((f) => ({ tweetId, seq: (f?.seq ?? 0) + 1 }));
    },
    [mine],
  );

  if (!cluster) return <p className="mt-7 text-muted">Este evento não tem bolhas selecionadas.</p>;
  const open = (c: ClusterMeta["community"]) => {
    setOrigin("amplified");
    setFocus(null);
    nav(bubblePath(meta.slug, c));
  };
  const compare = (c: number | null) =>
    nav(bubblePath(meta.slug, cluster.community), c === null ? undefined : { [COMPARE_PARAM]: String(c) });

  return (
    <>
      <div className="mt-7 flex flex-wrap items-start gap-x-9 gap-y-7">
        <EventGraph slug={meta.slug} clusters={meta.clusters} selected={cluster.community} onSelect={open} labelOf={labelOf} />
        <GroupSide
          cluster={cluster}
          clusters={meta.clusters}
          compareWith={compareWith?.community ?? null}
          showTags={showTags}
          labels={labels}
          labelOf={labelOf}
          onCompare={compare}
          onCite={onCite}
        />
      </div>
      <GroupSynthesis cluster={cluster} labels={labels} onCite={onCite} />
      {compareWith && <Comparison slots={data.slots} a={cluster} b={compareWith} showTags={showTags} />}
      <TweetThread
        slots={data.slots}
        community={cluster.community}
        origin={origin}
        onOrigin={setOrigin}
        colors={colors}
        focus={focus}
      />
    </>
  );
}
