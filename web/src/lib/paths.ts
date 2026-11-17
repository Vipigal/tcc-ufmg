export const HOME_PATH = "/";
export const HOW_PATH = "/como-funciona";
export const COMPARE_PARAM = "comparar";

export function eventPath(slug: string): string {
  return `/${slug}`;
}

export function bubblePath(slug: string, community: number): string {
  return `/${slug}/${community}`;
}

/** Bolha aberta na página do evento: a pedida na URL, ou a primeira (maior). */
export function pickBubble<T extends { community: number }>(clusters: T[], requested: string | undefined): T | undefined {
  return clusters.find((c) => String(c.community) === requested) ?? clusters[0];
}

/** Bolha de `?comparar=`: precisa existir e ser outra que a aberta. */
export function pickCompare<T extends { community: number }>(
  clusters: T[],
  current: number,
  requested: string | null,
): T | undefined {
  if (requested === null) return undefined;
  return clusters.find((c) => String(c.community) === requested && c.community !== current);
}
