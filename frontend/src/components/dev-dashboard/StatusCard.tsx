import { toneClass } from '../../pages/devDashboardFilters'

type StatusCardProps = {
  label: string
  value: string
  tone?: string
  testId?: string
}

export function StatusCard({ label, value, tone = 'gray', testId }: StatusCardProps) {
  return (
    <div className={`rounded-xl border p-4 ${toneClass(tone)}`} data-testid={testId}>
      <div className="text-xs font-semibold uppercase tracking-wide opacity-80">{label}</div>
      <div className="text-lg font-bold mt-1">{value}</div>
    </div>
  )
}
