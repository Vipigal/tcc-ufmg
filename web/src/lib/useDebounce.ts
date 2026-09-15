import { useEffect, useState } from "react";

/** Devolve `value` com atraso de `ms` após a última mudança (busca: 200 ms, spec §7.7). */
export function useDebounce<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}
