import { describe, expect, it } from 'vitest'
import {
  archivePercent,
  formatBytesBinary,
  formatEtaForDisplay,
  hasReliableBytesTotal,
  isStructuredProgressOptional,
  shouldShowCompressionBottleneckHint,
  shouldShowSlowButActiveHint,
} from './backupJobProgressDisplay'

describe('backupJobProgressDisplay', () => {
  it('erkennt strukturiertes progress_optional', () => {
    expect(isStructuredProgressOptional({ phase: 'archiving' })).toBe(true)
    expect(isStructuredProgressOptional(42)).toBe(false)
    expect(isStructuredProgressOptional(null)).toBe(false)
  })

  it('formatBytesBinary', () => {
    expect(formatBytesBinary(0)).toBe('0 B')
    expect(formatBytesBinary(1024)).toContain('KiB')
    expect(formatBytesBinary(5 * 1024 * 1024)).toContain('MiB')
  })

  it('hasReliableBytesTotal nur bei positiver Schätzung', () => {
    expect(hasReliableBytesTotal({ bytes_total_estimate: null })).toBe(false)
    expect(hasReliableBytesTotal({ bytes_total_estimate: 0 })).toBe(false)
    expect(hasReliableBytesTotal({ bytes_total_estimate: 1_000_000 })).toBe(true)
  })

  it('formatEtaForDisplay ohne Gesamtgröße immer unknown', () => {
    expect(formatEtaForDisplay({ eta_seconds: 120 }).kind).toBe('unknown')
    expect(formatEtaForDisplay({ bytes_total_estimate: 1e9, eta_seconds: null }).kind).toBe('unknown')
    expect(formatEtaForDisplay({ bytes_total_estimate: 1e9, eta_seconds: 90 })).toEqual({ kind: 'seconds', sec: 90 })
  })

  it('archivePercent ohne Total null', () => {
    expect(archivePercent({ bytes_current: 50 })).toBeNull()
    expect(archivePercent({ bytes_current: 50, bytes_total_estimate: 100 })).toBe(50)
  })

  it('slow-but-active ohne belastbare Gesamtgröße bei Archiv-Phase', () => {
    expect(
      shouldShowSlowButActiveHint({ phase: 'archiving', bytes_total_estimate: null }, 'running'),
    ).toBe(true)
    expect(
      shouldShowSlowButActiveHint({ phase: 'archiving', bytes_total_estimate: 1e12 }, 'running'),
    ).toBe(false)
  })

  it('compression hint aus warning_codes', () => {
    expect(shouldShowCompressionBottleneckHint({ warning_codes: ['compression_bottleneck'] })).toBe(true)
    expect(shouldShowCompressionBottleneckHint({ warning_codes: [] })).toBe(false)
  })
})
