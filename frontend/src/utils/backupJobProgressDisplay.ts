/** Reines Display- und Hilfslogik fuer Backup progress_optional (ohne React). */

export type StructuredProgressOptional = {
  phase?: string
  bytes_current?: number
  bytes_total_estimate?: number | null
  elapsed_seconds?: number
  throughput_mib_s?: number | null
  eta_seconds?: number | null
  compression_method?: string
  current_operation?: string
  target_mount?: string | null
  target_free_bytes?: number | null
  last_update_at?: string
  warning_codes?: string[]
  health_flags?: Record<string, unknown>
}

export function isStructuredProgressOptional(po: unknown): po is StructuredProgressOptional {
  return po !== null && typeof po === 'object' && !Array.isArray(po)
}

export function formatBytesBinary(n: number | null | undefined): string | null {
  if (n == null || !Number.isFinite(n) || n < 0) return null
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  let v = n
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i += 1
  }
  const digits = i === 0 ? 0 : v < 10 ? 2 : v < 100 ? 1 : 0
  return `${v.toFixed(digits)} ${units[i]}`
}

export function hasReliableBytesTotal(po: unknown): boolean {
  if (!isStructuredProgressOptional(po)) return false
  const t = po.bytes_total_estimate
  return typeof t === 'number' && Number.isFinite(t) && t > 0
}

/** ETA nur anzeigen, wenn Backend eine belastbare Schätzung liefert (kein Raten). */
export function formatEtaForDisplay(po: unknown): { kind: 'unknown' } | { kind: 'seconds'; sec: number } {
  if (!hasReliableBytesTotal(po)) return { kind: 'unknown' }
  if (!isStructuredProgressOptional(po)) return { kind: 'unknown' }
  const e = po.eta_seconds
  if (typeof e !== 'number' || !Number.isFinite(e) || e < 0) return { kind: 'unknown' }
  return { kind: 'seconds', sec: Math.round(e) }
}

/** Keine Prozentanzeige ohne belastbare Gesamtgröße. */
export function archivePercent(po: unknown): number | null {
  if (!hasReliableBytesTotal(po) || !isStructuredProgressOptional(po)) return null
  const cur = po.bytes_current
  const tot = po.bytes_total_estimate
  if (typeof cur !== 'number' || !Number.isFinite(cur) || cur < 0) return null
  if (typeof tot !== 'number' || !Number.isFinite(tot) || tot <= 0) return null
  return Math.min(100, Math.max(0, Math.round((cur / tot) * 100)))
}

export function shouldShowSlowButActiveHint(po: unknown, jobStatus: string | undefined): boolean {
  if (!isStructuredProgressOptional(po)) return false
  const st = String(jobStatus ?? '').toLowerCase()
  const runningLike = st === '' || st === 'queued' || st === 'running' || st === 'cancel_requested'
  if (!runningLike) return false
  if (hasReliableBytesTotal(po)) return false
  const ph = String(po.phase || '').toLowerCase()
  return ['preflight', 'estimating', 'archiving', 'compressing', 'writing', 'hashing', 'finalizing'].includes(ph)
}

export function shouldShowCompressionBottleneckHint(po: unknown): boolean {
  if (!isStructuredProgressOptional(po)) return false
  const codes = po.warning_codes || []
  return codes.some((c) => String(c).toLowerCase().includes('compression'))
}

export function shouldShowTargetIoHint(jobCode: string | undefined, po: unknown): boolean {
  const jc = String(jobCode || '')
  if (jc === 'backup.write_io_error') return true
  if (!isStructuredProgressOptional(po)) return false
  return (po.warning_codes || []).some((c) => String(c).toLowerCase().includes('io') || String(c).includes('TARGET'))
}
