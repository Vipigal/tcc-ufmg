export interface EventSource {
  label: string;
  url: string;
}

export interface EventStory {
  dateShort: string;
  short: string;
  full: string;
  title: string;
  about: string;
  text: string;
  note: string | null;
  sources: EventSource[];
}

export interface TimelineMark {
  date: string;
  label: string;
}

export const TIMELINE_MARKS: TimelineMark[] = [
  { date: "2022-10-02", label: "1º turno" },
  { date: "2023-01-01", label: "posse" },
];

export const OMITTED_MEDIA: Record<string, string> = {
  "1612226342019338240": "Imagem omitida: reúne rostos de pessoas para identificá-las.",
};

/** Contexto factual de cada evento, com fontes. Chave = slug do export. */
export const EVENT_STORIES: Record<string, EventStory> = {
  "mobilizacao-0709": {
    dateShort: "7 set 2022",
    short: "Bicentenário da Independência",
    full: "Quarta-feira, 7 de setembro de 2022",
    title: "Bicentenário da Independência",
    about: "o Bicentenário da Independência",
    text: "A 25 dias do primeiro turno, o presidente Jair Bolsonaro, candidato à reeleição, acompanhou o desfile cívico-militar na Esplanada dos Ministérios ao lado do presidente de Portugal e discursou a apoiadores. À tarde, discursou em um ato na orla de Copacabana, no Rio. Adversários e parte da imprensa apontaram uso eleitoral da data; apoiadores trataram os atos como celebração patriótica.",
    note: null,
    sources: [
      {
        label: "Agência Brasil",
        url: "https://agenciabrasil.ebc.com.br/en/politica/noticia/2022-09/independence-day-parade-brasilia-attracts-large-crowd",
      },
      {
        label: "Bloomberg Línea",
        url: "https://www.bloomberglinea.com.br/2022/09/07/ao-vivo-acompanhe-as-principais-movimentacoes-do-7-de-setembro/",
      },
    ],
  },
  "roberto-jefferson": {
    dateShort: "23 out 2022",
    short: "A prisão de Roberto Jefferson",
    full: "Domingo, 23 de outubro de 2022",
    title: "A prisão de Roberto Jefferson",
    about: "a prisão de Roberto Jefferson",
    text: "A uma semana do segundo turno, o ministro Alexandre de Moraes, do STF, revogou a prisão domiciliar do ex-deputado Roberto Jefferson (PTB), aliado de Bolsonaro, por descumprimento de medidas cautelares. Quando a Polícia Federal chegou à sua casa, em Comendador Levy Gasparian (RJ), ele atirou contra os agentes com um fuzil e lançou granadas; segundo a PF, cerca de 50 tiros e 3 granadas. Policiais ficaram feridos, e ele se entregou à noite.",
    note: null,
    sources: [
      {
        label: "STF",
        url: "https://noticias.stf.jus.br/postsnoticias/ministro-alexandre-de-moraes-revoga-domiciliar-e-determina-nova-prisao-de-roberto-jefferson/",
      },
      { label: "Associated Press", url: "https://globalnews.ca/news/9220995/brazil-politician-bolsonaro-ally-refuses-arrest" },
      { label: "Poder360", url: "https://www.poder360.com.br/justica/jefferson-deu-50-tiros-de-fuzil-e-jogou-3-granadas-diz-pf/" },
    ],
  },
  eleicoes: {
    dateShort: "30 out 2022",
    short: "Segundo turno",
    full: "Domingo, 30 de outubro de 2022",
    title: "Segundo turno da eleição presidencial",
    about: "o segundo turno, em tweets que mencionam democracia",
    text: "O TSE totalizou 50,90% dos votos válidos para Luiz Inácio Lula da Silva (PT) e 49,10% para Jair Bolsonaro (PL), uma diferença de cerca de 2,1 milhões de votos, a disputa presidencial mais apertada da história. Bolsonaro foi o primeiro presidente a não se reeleger desde que a reeleição foi permitida, em 1997.",
    note: "Neste dia entram só os tweets que mencionam democracia.",
    sources: [
      {
        label: "TSE",
        url: "https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/100-das-secoes-totalizadas-confira-como-ficou-o-quadro-eleitoral-apos-o-2o-turno",
      },
      {
        label: "CNN Brasil",
        url: "https://www.cnnbrasil.com.br/politica/disputa-entre-lula-e-bolsonaro-e-a-eleicao-para-presidente-mais-acirrada-da-historia/",
      },
    ],
  },
  "invasao-3-poderes": {
    dateShort: "8 jan 2023",
    short: "Invasão dos Três Poderes",
    full: "Domingo, 8 de janeiro de 2023",
    title: "Invasão das sedes dos Três Poderes",
    about: "a invasão das sedes dos Três Poderes",
    text: "Uma semana após a posse de Lula, apoiadores de Bolsonaro acampados em frente ao Quartel-General do Exército, em Brasília, marcharam até a Praça dos Três Poderes. No meio da tarde, romperam o bloqueio policial e invadiram e depredaram o Congresso Nacional, o Palácio do Planalto e o Supremo Tribunal Federal, contestando o resultado da eleição. Até janeiro de 2026, o STF havia condenado mais de 800 réus pelos atos.",
    note: null,
    sources: [
      { label: "Bastos e Recuero (2023)", url: "https://doi.org/10.1177/20563051231211881" },
      { label: "IstoÉ, com Agência Brasil", url: "https://istoe.com.br/relembre-o-passo-a-passo-da-tentativa-de-golpe-no-8-1" },
      {
        label: "O Povo",
        url: "https://www.opovo.com.br/noticias/politica/2026/01/08/stf-ja-condenou-mais-de-800-reus-pela-trama-golpista.html",
      },
    ],
  },
};

/** História do evento; evento novo sem texto curado cai no nome e na data do export. */
export function storyFor(meta: { slug: string; name: string; event_date: string | null }): EventStory {
  return (
    EVENT_STORIES[meta.slug] ?? {
      dateShort: meta.event_date ?? "",
      short: meta.name,
      full: meta.event_date ?? "",
      title: meta.name,
      about: meta.name,
      text: "",
      note: null,
      sources: [],
    }
  );
}
