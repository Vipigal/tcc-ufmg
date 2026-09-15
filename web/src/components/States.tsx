/** Estados de carregamento e erro (spec §8): esqueleto simples; erro sem retry automático. */

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`animate-pulse rounded-xl bg-gray-100 ${className}`} />;
}

export function ErrorBox({ error }: { error: Error }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-[14px] text-red-900">
      <strong>Não consegui carregar os dados.</strong>
      <pre className="mt-1 whitespace-pre-wrap font-mono text-[12.5px]">{error.message}</pre>
    </div>
  );
}
