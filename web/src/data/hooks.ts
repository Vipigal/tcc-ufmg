import { useEffect, useState } from "react";
import type { EventData, EventMeta, Index } from "../types";
import { loadEvent } from "./loadEvent";
import { loadIndex } from "./loadIndex";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "ready"; data: T };

const LOADING: { status: "loading" } = { status: "loading" };

/**
 * Executa `start` quando `key` muda; ignora resultados de execuções antigas.
 * O estado guarda a chave a que pertence: se a chave pedida for outra, devolve `loading`
 * já no mesmo render — nunca entrega dados de um evento sob o rótulo de outro.
 */
function useAsync<T>(start: () => Promise<T>, key: string): AsyncState<T> {
  const [state, setState] = useState<{ key: string; value: AsyncState<T> }>({ key, value: LOADING });
  useEffect(() => {
    let alive = true;
    start().then(
      (data) => {
        if (alive) setState({ key, value: { status: "ready", data } });
      },
      (err: unknown) => {
        if (alive) setState({ key, value: { status: "error", error: err instanceof Error ? err : new Error(String(err)) } });
      },
    );
    return () => {
      alive = false;
    };
    // `start` é recriado a cada render; `key` é a identidade do que se carrega.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state.key === key ? state.value : LOADING;
}

export function useIndex(): AsyncState<Index> {
  return useAsync(loadIndex, "index");
}

export function useEvent(meta: EventMeta): AsyncState<EventData> {
  return useAsync(() => loadEvent(meta), meta.slug);
}
