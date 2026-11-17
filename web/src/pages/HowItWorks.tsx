import { useState } from "react";
import { Link } from "react-router-dom";
import type { EventMeta, Index } from "../types";
import { PageFrame, WithIndex } from "../App";
import { formatDec, formatInt } from "../lib/format";
import { useKeptSearch, useShowTags } from "../lib/nav";
import { eventPath } from "../lib/paths";
import { CrowdDemo, LinkDemo, PairDemo } from "../components/OverlapDemo";

const EXAMPLE_SLUG = "invasao-3-poderes";

interface Step {
  label: string;
  title: string;
  body: string;
  aside: string;
}

function steps(example: EventMeta): Step[] {
  const tau = example.run_config.tau;
  const cut = typeof tau === "number" ? ` Abaixo de ${formatDec(tau, 2)}, a ligação é descartada.` : "";
  return [
    {
      label: "1. Coleções",
      title: "Cada pessoa tem uma coleção de retweets",
      body: "Durante o evento, Ana retuitou os tweets T1 e T2. Bruno retuitou T1, T2 e T3.",
      aside: "Só usamos quem retuitou o quê. Não entram seguidores, curtidas nem o texto dos tweets.",
    },
    {
      label: "2. Sobreposição",
      title: "O que as coleções têm em comum vira ligação",
      body: "Ana e Bruno dividem 2 dos 3 tweets que retuitaram ao todo. A ligação entre eles vale 2 ÷ 3 = 0,67.",
      aside: `Quanto mais as coleções se sobrepõem, mais forte a ligação.${cut}`,
    },
    {
      label: "3. Ligações",
      title: "Cada pessoa vira um ponto, cada sobreposição vira uma linha",
      body: "Ana e Bruno viram dois pontos, e a ligação de 0,67 vira a linha entre eles. A mesma conta, feita para cada par, traz Carla, Davi, Edu e Fê para a rede: quanto mais grossa a linha, mais retweets os dois dividem.",
      aside: "Quem não divide nada não ganha linha. Com só seis pessoas já aparecem dois trios bem ligados por dentro e unidos por uma única linha fina.",
    },
    {
      label: "4. Milhares",
      title: "Com milhares de pessoas, as ligações formam uma rede",
      body: "É a mesma conta, repetida para cada par de pessoas. Cada ponto é uma pessoa e cada linha, uma sobreposição forte o bastante.",
      aside: `No 8 de janeiro foram ${formatInt(example.n_nodes)} pessoas e cerca de ${formatInt(Math.round(example.n_edges / 1e6))} milhões de ligações.`,
    },
    {
      label: "5. Bolhas",
      title: "Regiões densas viram bolhas",
      body: "O algoritmo Leiden encontra conjuntos com muitas ligações por dentro e poucas para fora. Cada conjunto vira uma bolha.",
      aside: "O algoritmo não sabe nada de política. A leitura do conteúdo só vem depois, quando lemos o que cada bolha retuitou.",
    },
  ];
}

export function HowItWorks() {
  return <WithIndex>{(index) => <HowBody index={index} />}</WithIndex>;
}

function HowBody({ index }: { index: Index }) {
  const [step, setStep] = useState(0);
  const kept = useKeptSearch();
  const example = index.events.find((e) => e.slug === EXAMPLE_SLUG) ?? index.events[index.events.length - 1];
  const texts = steps(example);
  const cur = texts[step];
  const last = step === texts.length - 1;
  return (
    <PageFrame>
      <h1 className="m-0 max-w-[14em] pt-12 text-[clamp(34px,4.4vw,58px)] leading-none font-extrabold tracking-[-0.03em]">
        Duas pessoas, uma sobreposição
      </h1>
      <p className="mt-5 mb-9 max-w-[34em] text-[19px] leading-normal text-muted">
        A mesma ideia de círculos que se sobrepõem explica cada ligação do grafo. Avance pelos cinco passos.
      </p>

      <div role="tablist" aria-label="Passos" className="mb-6 flex flex-wrap gap-2">
        {texts.map((t, i) => (
          <button
            key={t.label}
            type="button"
            role="tab"
            aria-selected={i === step}
            onClick={() => setStep(i)}
            className={`min-h-11 cursor-pointer rounded-full border-0 px-[18px] text-[15px] ${
              i === step ? "bg-ink font-bold text-bg" : "bg-chip text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-x-14 gap-y-8">
        <figure className="m-0 min-w-0 flex-[999_1_520px] rounded-[40px] bg-soft p-5">
          {step < 2 ? (
            <PairDemo overlap={step === 1} />
          ) : step === 2 ? (
            <LinkDemo />
          ) : (
            <CrowdDemo grouped={step === 4} />
          )}
        </figure>
        <div className="max-w-[440px] min-w-0 flex-[1_1_340px]" aria-live="polite">
          <h2 className="m-0 mb-3.5 text-[28px] leading-[1.1] font-extrabold tracking-[-0.02em]">{cur.title}</h2>
          <p className="m-0 mb-3.5 text-[18px] leading-[1.6]">{cur.body}</p>
          <p className="m-0 text-[16px] leading-[1.55] text-muted">{cur.aside}</p>
          <div className="mt-7 flex flex-wrap gap-2.5">
            {last ? (
              <Link
                to={eventPath(example.slug) + kept}
                className="inline-flex min-h-12 items-center rounded-full bg-ink px-[22px] font-bold text-bg no-underline"
              >
                Ver as bolhas do 8 de janeiro
              </Link>
            ) : (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="min-h-12 cursor-pointer rounded-full border-0 bg-ink px-[22px] font-bold text-bg"
              >
                Próximo passo
              </button>
            )}
          </div>
        </div>
      </div>

      <ReadingNotes />
    </PageFrame>
  );
}

function ReadingNotes() {
  const showTags = useShowTags();
  return (
    <section className="mt-[72px] grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
      <div className="rounded-[28px] bg-soft p-6">
        <h3 className="m-0 mb-1.5 text-[18px] font-extrabold">Tamanho e sobreposição</h3>
        <p className="m-0 text-[16px] leading-[1.55]">
          Cada ponto é uma pessoa e cada região, um grupo: quanto maior, mais pessoas. Grupos que fazem circular quase o mesmo conteúdo aparecem juntos; os demais ficam separados, e as linhas mostram o que eles dividem.
        </p>
      </div>
      <div className="rounded-[28px] bg-soft p-6">
        <h3 className="m-0 mb-1.5 text-[18px] font-extrabold">A cor</h3>
        <p className="m-0 text-[16px] leading-[1.55]">
          Cada grupo tem uma cor (roxo, verde, laranja, amarelo, marrom) que só o distingue dos outros, sem sugerir lado.
          {showTags && (
            <>
              {" "}
              Ao abrir um grupo, uma etiqueta descreve o conteúdo:{" "}
              <span className="font-bold text-[var(--right-ink)]">azul</span> para direita,{" "}
              <span className="font-bold text-[var(--left-ink)]">vermelho</span> para esquerda. Essa leitura vem depois que o
              algoritmo formou os grupos.
            </>
          )}
        </p>
      </div>
      <div className="rounded-[28px] bg-warn p-6">
        <h3 className="m-0 mb-1.5 text-[18px] font-extrabold">O que as bolhas não dizem</h3>
        <p className="m-0 text-[16px] leading-[1.55]">
          Que as pessoas se seguem, conversam ou concordam. Retweet também pode ser ironia ou denúncia.
        </p>
      </div>
    </section>
  );
}
