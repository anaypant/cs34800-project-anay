export function StatList({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; value: string; rank: string | null }[];
}) {
  if (rows.length === 0) return null;
  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <h3 className="text-sm font-medium text-zinc-200">{title}</h3>
      <dl className="mt-3 space-y-2">
        {rows.map((row) => (
          <div key={row.label} className="flex items-baseline justify-between gap-4 text-sm">
            <dt className="text-zinc-400">{row.label}</dt>
            <dd className="text-right text-zinc-100 tabular-nums">
              {row.value}
              {row.rank ? <span className="ml-2 text-xs text-zinc-500">{row.rank}</span> : null}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
