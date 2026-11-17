import { useState } from "react";
import { Link } from "react-router-dom";
import type { EventMeta, Index } from "../types";
import { PageFrame, WithIndex } from "../App";
import { storyFor } from "../content/events";
import { formatInt } from "../lib/format";
import { useKeptSearch } from "../lib/nav";
import { useTheme } from "../lib/theme";
import { eventPath } from "../lib/paths";
import { Timeline } from "../components/Timeline";

export function Home() {
  return <WithIndex wide>{(index) => <HomeBody index={index} />}</WithIndex>;
}

const countText = (e: EventMeta) => `${formatInt(e.n_nodes)} pessoas, ${e.clusters.length} bolhas`;

function HomeBody({ index }: { index: Index }) {
  const [selected, setSelected] = useState(index.events.length - 1);
  const { theme } = useTheme();
  const current = index.events[selected];
  if (!current)
    return (
      <PageFrame wide>
        <p className="pt-8 text-muted">Nenhum evento no export.</p>
      </PageFrame>
    );
  return (
    <PageFrame wide>
      <header className="max-w-[900px] pt-10">
        <h1 className="m-0 text-[clamp(40px,6vw,80px)] leading-[0.95] font-extrabold tracking-[-0.04em]">
          Um mesmo fato, duas realidades
        </h1>
        <p className="m-0 mt-5 max-w-[34em] text-[clamp(19px,1.8vw,23px)] leading-[1.45] text-muted">
          Como lados opostos do Twitter brasileiro viveram os mesmos acontecimentos, da campanha de 2022 ao 8 de janeiro.
        </p>
      </header>

      <ResearchIntro />

      <Timeline events={index.events} selected={selected} onSelect={setSelected} />

      <div className="mt-5 grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
        {index.events.map((e, i) => (
          <button
            key={e.slug}
            type="button"
            onClick={() => setSelected(i)}
            aria-pressed={i === selected}
            className={`lift block cursor-pointer rounded-[28px] border-2 bg-bg px-[18px] pt-[18px] pb-4 text-left text-ink ${
              i === selected ? "border-ink" : "border-line"
            }`}
          >
            <span className="block text-[22px] font-extrabold tracking-[-0.01em]">{storyFor(e).dateShort}</span>
            <span className="mt-0.5 block text-[15px] text-muted">{storyFor(e).short}</span>
            <img
              src={`/${e.slug}/grafo-${theme === "dark" ? "escuro" : "claro"}-mini.webp`}
              alt=""
              loading="lazy"
              className="mt-2 block aspect-square w-full rounded-[20px] object-cover"
            />
            <span className="mt-1 block text-[14px] text-muted">{countText(e)}</span>
          </button>
        ))}
      </div>

      <EventStoryCard event={current} />
    </PageFrame>
  );
}

const INTRO: { title: string; text: string }[] = [
  {
    title: "Por que olhar para isso",
    text: "Em 30 de outubro de 2022, Lula venceu Bolsonaro por uma margem estreita. Dois meses depois, em 8 de janeiro, apoiadores de Bolsonaro invadiram as sedes dos Três Poderes. Para uma parte do país, foi um ataque à democracia; para outra, um protesto legítimo. Que o Brasil está dividido, quase todo mundo sente. A pergunta aqui é outra: que forma tem essa divisão?",
  },
  {
    title: "O que a pesquisa faz",
    text: "Olhamos para quatro dias do ciclo eleitoral, do 7 de setembro ao 8 de janeiro, e para o que as pessoas retuitaram em cada um. Quem compartilhou as mesmas coisas fica no mesmo grupo. Ninguém é classificado de antemão: os grupos surgem só dos retweets, e só depois lemos o que circulou em cada um. A hipótese é que a separação foi sendo construída ao longo da campanha, e não de uma vez no 8 de janeiro.",
  },
];

/** Motivação e o que a pesquisa faz (paráfrase simples da introdução da proposta do TCC2). */
function ResearchIntro() {
  return (
    <section className="mt-12 grid max-w-[900px] gap-7">
      {INTRO.map((item) => (
        <div key={item.title} className="grid gap-x-10 gap-y-1.5 min-[760px]:grid-cols-[200px_1fr]">
          <h2 className="m-0 pt-1 text-[16px] font-extrabold">{item.title}</h2>
          <p className="m-0 text-[18px] leading-[1.65]">{item.text}</p>
        </div>
      ))}
    </section>
  );
}

function EventStoryCard({ event }: { event: EventMeta }) {
  const story = storyFor(event);
  const kept = useKeptSearch();
  return (
    <article aria-live="polite" className="mt-5 flex flex-wrap gap-x-14 gap-y-6 rounded-[32px] bg-soft p-[clamp(24px,4vw,44px)]">
      <div className="max-w-[700px] min-w-0 flex-[999_1_520px]">
        <p className="m-0 mb-1.5 text-[15px] text-faint">{story.full}</p>
        <h2 className="m-0 mb-4 text-[clamp(28px,3vw,38px)] leading-[1.06] font-extrabold tracking-[-0.025em]">
          {story.title}
        </h2>
        {story.text && <p className="m-0 text-[18px] leading-[1.65]">{story.text}</p>}
        {story.note && <p className="m-0 mt-3 text-[16px] leading-[1.55] text-muted">{story.note}</p>}
        {story.sources.length > 0 && (
          <p className="m-0 mt-[18px] text-[15px] text-muted">
            Fontes:{" "}
            {story.sources.map((s) => (
              <a key={s.url} href={s.url} target="_blank" rel="noopener noreferrer" className="mr-3 text-ink underline">
                {s.label}
              </a>
            ))}
          </p>
        )}
      </div>
      <div className="flex flex-[1_1_260px] flex-col justify-end gap-2.5">
        <p className="m-0 text-[16px]">
          {formatInt(event.n_nodes)} pessoas retuitaram sobre o dia e se dividiram em {event.clusters.length} bolhas.
        </p>
        <Link
          to={eventPath(event.slug) + kept}
          className="inline-flex min-h-[52px] items-center self-start rounded-full bg-ink px-[26px] text-[17px] font-bold text-bg no-underline"
        >
          Ver as bolhas deste dia
        </Link>
      </div>
    </article>
  );
}
