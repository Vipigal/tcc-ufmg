/** Erro padrão de dados ausentes (spec §8): sem retry automático. */
export class ExportNotFoundError extends Error {
  readonly path: string;

  constructor(path: string) {
    super(`não encontrei data/export${path}; rode a célula M10 do pipeline_tcc2.ipynb`);
    this.name = "ExportNotFoundError";
    this.path = path;
  }
}

/**
 * fetch de JSON estático servido pelo Vite a partir de data/export/.
 * O dev server devolve index.html (200, text/html) para caminhos desconhecidos — por isso
 * o content-type também é verificado.
 */
export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  const type = res.headers.get("content-type") ?? "";
  if (!res.ok || !type.includes("json")) throw new ExportNotFoundError(path);
  return (await res.json()) as T;
}
