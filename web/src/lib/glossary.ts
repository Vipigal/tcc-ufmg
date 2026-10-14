import type { ReferencedTweetType, SlotStatus } from "../types";

/** Tooltips da faixa de pesquisa e do painel (spec §7.6). Dizem o que o número É — nunca um juízo. */
export const GLOSSARY = {
  rank: "Posição no ranking do cluster pelo nº de membros que retuitaram.",
  rt_cluster: "Usuários deste cluster (nós do grafo) que retuitaram. Critério de seleção (D6).",
  purity: "Fração dos retweets de nós do grafo que vieram deste cluster. 1,00 = só este cluster.",
  rt_graph: "Nós do grafo (qualquer cluster) que retuitaram.",
  rt_event: "Usuários do evento que retuitaram, inclusive os filtrados por atividade (N).",
  api: "Reposts totais segundo a API hoje, e a razão para o alcance dentro do evento. Só se hidratado.",
  also_in: "O mesmo tweet também foi selecionado para outro cluster deste evento (top-K ou cauda).",
  characteristic:
    "Cauda característica (D16): fora do top-K, ranqueada por lift — quanto o cluster retuitou o tweet além da sua proporção no evento.",
  lift: "Fração dos RTs do grafo vinda deste cluster ÷ fração do cluster em todos os RTs. 1 = proporcional; o máximo é 100% exclusivo.",
  summary:
    "Gerada por LLM a partir do top-K e da cauda hidratados (M11). Ajuda de leitura, não categorização; revisar sempre contra os tweets.",
  invalid_ids: "IDs citados pelo modelo que não estão no corpus deste cluster — a afirmação correspondente não tem âncora.",
  confidence: "Confiança declarada pelo próprio modelo no palpite de inclinação, segundo os critérios do prompt.",
  axis_tag:
    "Eixo atribuído pelos pesquisadores a partir da inclinação descrita pelo LLM. É um palpite sobre o conteúdo amplificado, não sobre os usuários. Oculte com ?tags=0.",
  shared:
    "Dos retweets que este grupo dá, que fração vai a tweets que também circulam em outros grupos (1 − pureza média, ponderada). Assimétrica: o grupo menor tende a compartilhar mais com o maior.",
  top_accounts: "Calculado pela pipeline: soma dos RTs de membros do cluster aos tweets de cada conta (top-K ∪ cauda hidratados).",
  frac_nodes: "Fração dos nós (usuários) do grafo que pertencem a este cluster.",
  intra_weight_frac: "Peso das arestas internas ao cluster sobre o peso total do grafo. ≤ 5% ⇒ K = 20.",
  hydrated: "Slots selecionados que a API devolveu / slots selecionados.",
  attrition: "Fração dos slots selecionados que a API não devolveu (removidos, suspensos ou protegidos).",
} as const;

export const CONFIDENCE_TEXT: Record<"alta" | "media" | "baixa", string> = {
  alta: "alta",
  media: "média",
  baixa: "baixa",
};

/** RF7: título do card fantasma por status. `error` usa `error.title` quando existir. */
export const SLOT_STATUS_TEXT: Record<Exclude<SlotStatus, "hydrated">, string> = {
  not_found: "Tweet removido ou indisponível",
  not_authorized: "Conta suspensa ou protegida",
  error: "Erro na API",
  pending: "Ainda não hidratado",
};

/** RF8: motivo de autor indisponível em tweet hidratado. */
export const AUTHOR_STATUS_TEXT: Record<string, string> = {
  not_found: "conta removida",
  not_authorized: "conta suspensa ou protegida",
  pending: "não hidratado",
  error: "erro na API",
};

/** Rótulo curto das abas (spec §7.1). Chave = slug do export. */
export const EVENT_SHORT_NAMES: Record<string, string> = {
  "mobilizacao-0709": "Mobilização 7/9",
  "roberto-jefferson": "Roberto Jefferson",
  eleicoes: "Eleições 30/10",
  "invasao-3-poderes": "8 de janeiro",
};

/** Tooltip do selo de verificado por `verified_type`. */
export const VERIFIED_TYPE_TEXT: Record<string, string> = {
  blue: "verificado (assinante)",
  business: "verificado (organização)",
  government: "verificado (governo)",
  none: "verificado",
};

export const REFERENCE_TEXT: Record<ReferencedTweetType, string> = {
  quoted: "citando um tweet",
  replied_to: "em resposta a um tweet",
  retweeted: "repostando um tweet",
};
