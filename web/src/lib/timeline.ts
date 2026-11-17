const DAY_MS = 86_400_000;

function toTime(isoDate: string): number {
  return Date.parse(`${isoDate}T00:00:00Z`);
}

/** Escala proporcional ao tempo entre o primeiro e o último evento (0 → 1). */
export function timelineScale(dates: string[]): { days: number; at: (isoDate: string) => number } {
  const times = dates.map(toTime);
  const first = Math.min(...times);
  const last = Math.max(...times);
  const span = last - first;
  return {
    days: Math.round(span / DAY_MS),
    at: (isoDate) => (span === 0 ? 0 : (toTime(isoDate) - first) / span),
  };
}

/** "2023-01-08" → "8/1". */
export function dayMonth(isoDate: string): string {
  const [, m, d] = isoDate.split("-").map(Number);
  return `${d}/${m}`;
}
