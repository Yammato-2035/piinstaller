import { toneClass } from '../../pages/devDashboardFilters'

type StatusCardProps = {
  label: string
  value: string
  tone?: string
  testId?: string
  /** Hervorhebung nur bei echtem grünen Status (keine Logikänderung). */
  emphasizeOk?: boolean
}

export function StatusCard({ label, value, tone = 'gray', testId, emphasizeOk = false }: StatusCardProps) {
  const isOk = emphasizeOk && String(tone).toLowerCase() === 'green'
  return (
    <div
      className={`rounded-xl border p-4 ${toneClass(tone)}${isOk ? ' ring-2 ring-emerald-500/35 shadow-md shadow-emerald-950/40' : ''}`}
      data-testid={testId}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-wide opacity-80">{label}</div>
        {isOk ? (
          <span className="text-[10px] font-bold uppercase tracking-wide text-emerald-300 border border-emerald-600/50 rounded px-1.5 py-0.5">
            OK
          </span>
        ) : null}
      </div>
      <div className="text-lg font-bold mt-1">{value}</div>
    </div>
  )
}
