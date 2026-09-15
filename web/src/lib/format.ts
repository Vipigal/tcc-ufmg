/** Formatação pt-BR (spec §7.8). Tudo aqui é apresentação; nada é cálculo de pesquisa. */

const EMPTY = "—";

const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat("pt-BR");
const dateTime = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Sao_Paulo",
});
const day = new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" });
const decimals = new Map<number, Intl.NumberFormat>();

function decimalFormatter(digits: number): Intl.NumberFormat {
  let f = decimals.get(digits);
  if (!f) {
    f = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    decimals.set(digits, f);
  }
  return f;
}

/** 28348 → "28,3 mil"; 1200000 → "1,2 mi"; null → "—". Troca o NBSP do Intl por espaço normal. */
export function formatCompact(n: number | null | undefined): string {
  return n == null ? EMPTY : compact.format(n).replace(/ /g, " ");
}

/** 3389 → "3.389"; null → "—". */
export function formatInt(n: number | null | undefined): string {
  return n == null ? EMPTY : integer.format(n);
}

/** 0.7538, 2 → "0,75"; null → "—". */
export function formatDec(x: number | null | undefined, digits: number): string {
  return x == null ? EMPTY : decimalFormatter(digits).format(x);
}

/** 0.4423 → "44%"; (0.358, 1) → "35,8%"; null → "—". */
export function formatPct(x: number | null | undefined, digits = 0): string {
  return x == null ? EMPTY : `${formatDec(x * 100, digits)}%`;
}

/** ISO-8601 → "8 de jan. de 2023, 15:54" (fuso de Brasília). */
export function formatDate(iso: string): string {
  return dateTime.format(new Date(iso));
}

/** "2023-01-08" → "8 de janeiro de 2023" (interpreta a data como UTC para não deslocar o dia). */
export function formatDay(isoDate: string): string {
  return day.format(new Date(`${isoDate}T00:00:00Z`));
}

/** Busca sem acento e sem caixa: NFD + remoção de marcas combinantes. */
export function normalize(s: string): string {
  return s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}
