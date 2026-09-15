/**
 * Contrato de `data/export/` (spec §5). Fonte da verdade: `modules/export.py` (WebExporter, M10).
 * O front não deriva nada daqui — só exibe.
 */

export interface Index {
  generated_at: string; // ISO-8601 UTC — único carimbo de tempo do export
  palette: string[]; // 10 cores hex; cor do Grupo g = palette[(g-1) % palette.length]
  events: EventMeta[]; // na ordem da pipeline (mobilizacao, roberto, eleicoes, invasao)
}

export interface EventMeta {
  slug: string; // = nome da pasta; usado na URL
  name: string; // "Ataques de 8 de janeiro de 2023"
  event_date: string | null; // "2023-01-08"
  n_nodes: number; // nós do grafo (usuários)
  n_edges: number; // arestas do backbone
  n_communities: number; // comunidades Leiden, incluindo as < 1%
  run_config: Record<string, unknown>; // parâmetros da fase 1 (N, τ, resolução…)
  selection: { k: number; k_small: number; min_frac: number; small_weight_frac: number };
  clusters: ClusterMeta[]; // só os selecionados (≥ min_frac), ordenados por group
  files: { tweets: string; layout: string }; // caminhos relativos a data/export/
}

export interface ClusterMeta {
  community: number; // id Leiden (estável nos dados; usar na URL)
  group: number; // 1..n por tamanho (numeração das figuras da fase 1)
  label: string; // "Grupo 1"
  color: string; // hex, da paleta
  n_nodes: number;
  frac_nodes: number; // 0–1
  intra_weight_frac: number; // peso interno / peso total do grafo (0–1); ≤ 0.05 ⇒ k = k_small
  k: number; // 100 ou 20
  n_selected: number; // = k, salvo cluster com menos candidatos
  n_hydrated: number;
  n_not_found: number;
  n_not_authorized: number;
  n_other_errors: number;
  n_pending: number;
  attrition: number; // (n_selected − n_hydrated) / n_selected
}

export type SlotStatus = "hydrated" | "not_found" | "not_authorized" | "error" | "pending";
export type AuthorStatus = "hydrated" | "not_found" | "not_authorized" | "error" | "pending" | null;

export interface Slot {
  community: number;
  group: number;
  rank: number;
  k: number;
  tweet_id: string;
  rt_cluster: number; // membros do cluster que retuitaram (critério do ranking)
  rt_graph: number; // nós do grafo (qualquer cluster) que retuitaram
  rt_event: number; // usuários do evento, inclusive periferia filtrada
  purity: number | null; // rt_cluster / rt_graph, 4 casas
  also_in: { community: number; group: number; rank: number }[]; // outros clusters do MESMO evento
  status: SlotStatus;
  error: { title: string; detail: string } | null; // só quando status ∉ {hydrated, pending}
  tweet: Tweet | null; // null se não hidratado
  author_id: string | null; // null se não hidratado
  author: Author | null; // null se autor não hidratado/negado
  author_status: AuthorStatus; // null quando o tweet não foi hidratado
}

export interface TweetUrlEntity {
  start: number;
  end: number;
  url: string;
  expanded_url?: string;
  display_url?: string;
  media_key?: string;
}

export interface TweetEntities {
  urls: TweetUrlEntity[];
  hashtags: { start: number; end: number; tag: string }[];
  mentions: { start: number; end: number; username: string; id?: string }[];
}

export type ReferencedTweetType = "quoted" | "replied_to" | "retweeted";

export interface Tweet {
  id: string;
  text: string;
  created_at: string;
  lang: string | null;
  source: string | null;
  possibly_sensitive: boolean | null;
  reply_settings: string | null;
  conversation_id: string | null;
  in_reply_to_user_id: string | null;
  metrics: {
    retweet_count: number | null;
    reply_count: number | null;
    like_count: number | null;
    quote_count: number | null;
    bookmark_count: number | null;
    impression_count: number | null;
  };
  entities: TweetEntities; // offsets em code points Unicode (Array.from), não UTF-16
  referenced_tweets: { type: ReferencedTweetType; id: string }[];
  url: string; // https://x.com/i/web/status/<id>
}

export interface Author {
  id: string;
  username: string | null;
  name: string | null;
  description: string | null;
  location: string | null;
  url: string | null;
  profile_image_url: string | null;
  protected: boolean | null;
  verified: boolean | null;
  verified_type: string | null; // "blue" | "business" | "government" | "none"
  created_at: string | null;
  metrics: {
    followers_count: number | null;
    following_count: number | null;
    tweet_count: number | null;
    listed_count: number | null;
  };
}

export interface Layout {
  n_nodes: number; // nós do grafo
  n_plotted: number; // nós da componente gigante (= x.length)
  top_k: number;
  seed: number; // parâmetros do DRL (reprodutibilidade)
  x: number[];
  y: number[]; // coordenadas (2 casas), mesma ordem que `community`
  community: number[]; // comunidade de cada nó plotado
  centroids: Record<string, [number, number]>; // mediana (x, y) por comunidade — onde pôr o rótulo
  groups: Record<string, number>; // community → group (todas as comunidades, inclusive < 1%)
}

/** Tudo que o front carrega para um evento (tweets.json + layout.json), em memória por slug. */
export interface EventData {
  meta: EventMeta;
  slots: Slot[];
  layout: Layout;
}
