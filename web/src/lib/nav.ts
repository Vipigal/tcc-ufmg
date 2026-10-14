import { useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";

/** `?tags=0` oculta as tags de inclinação (sessões do grupo focal, spec 2026-10-14 §3.2). */
export function useShowTags(): boolean {
  return new URLSearchParams(useLocation().search).get("tags") !== "0";
}

/** Sufixo de query que deve sobreviver à navegação (só `tags`). */
export function useKeptSearch(): string {
  const tags = new URLSearchParams(useLocation().search).get("tags");
  return tags === "0" ? "?tags=0" : "";
}

/** navigate() que preserva `?tags=0` e aceita parâmetros extras (ex.: origem). */
export function useNav() {
  const navigate = useNavigate();
  const kept = useKeptSearch();
  return useCallback(
    (path: string, extra?: Record<string, string>) => {
      const q = new URLSearchParams(kept.slice(1));
      for (const [k, v] of Object.entries(extra ?? {})) q.set(k, v);
      const s = q.toString();
      navigate(s ? `${path}?${s}` : path);
    },
    [navigate, kept],
  );
}
