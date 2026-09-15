import type { ReferencedTweetType, SlotStatus } from "../types";

/** Tooltips da faixa de pesquisa e do painel (spec §7.6). Dizem o que o número É — nunca um juízo. */
export const GLOSSARY = {
  rank: "Posição no ranking do cluster pelo nº de membros que retuitaram.",
  rt_cluster: "Usuários deste cluster (nós do grafo) que retuitaram. Critério de seleção (D6).",
  purity: "Fração dos retweets de nós do grafo que vieram deste cluster. 1,00 = só este cluster.",
  rt_graph: "Nós do grafo (qualquer cluster) que retuitaram.",
  rt_event: "Usuários do evento que retuitaram, inclusive os filtrados por atividade (N).",
  api: "Reposts totais segundo a API hoje, e a razão para o alcance dentro do evento. Só se hidratado.",
  also_in: "O mesmo tweet está no top-K de outro cluster deste evento.",
  frac_nodes: "Fração dos nós (usuários) do grafo que pertencem a este cluster.",
  intra_weight_frac: "Peso das arestas internas ao cluster sobre o peso total do grafo. ≤ 5% ⇒ K = 20.",
  hydrated: "Slots selecionados que a API devolveu / slots selecionados.",
  attrition: "Fração dos slots selecionados que a API não devolveu (removidos, suspensos ou protegidos).",
} as const;

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
