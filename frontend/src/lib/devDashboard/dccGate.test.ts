import { describe, expect, it } from 'vitest'
import { decideDccVisibility, DCC_BUNDLE_FIX_MARKER } from './dccGate'

describe('dccGate decideDccVisibility', () => {
  it('exports bundle marker for production dist grep', () => {
    expect(DCC_BUNDLE_FIX_MARKER).toBe('DCC_BOOT_DIAGNOSTICS_V1')
  })

  it('allows DCC when /api/dev-dashboard/status is 200 even if /api/version is stale release', () => {
    const version = { dev_control_enabled: false, install_profile: 'release' }
    const status = { httpStatus: 200 as const, code: null }
    expect(decideDccVisibility(version, status)).toEqual({ kind: 'allowed' })
  })

  it('disables on 404 PROFILE_ROUTE_BLOCKED', () => {
    const version = { dev_control_enabled: true, install_profile: 'local_lab' }
    const status = { httpStatus: 404 as const, code: 'PROFILE_ROUTE_BLOCKED' }
    expect(decideDccVisibility(version, status)).toEqual({
      kind: 'disabled',
      disabledReason: 'profile_route_blocked',
    })
  })

  it('disables when dev_control_enabled=false and status is blocked (non-200)', () => {
    const version = { dev_control_enabled: false, install_profile: 'release' }
    const status = { httpStatus: 403 as const, code: 'SOME_OTHER' }
    expect(decideDccVisibility(version, status)).toEqual({
      kind: 'disabled',
      disabledReason: 'dev_control_disabled_and_status_blocked',
    })
  })

  it('returns error for inconsistent state: status non-200 but dev_control_enabled=true', () => {
    const version = { dev_control_enabled: true, install_profile: 'local_lab' }
    const status = { httpStatus: 500 as const, code: 'INTERNAL_ERROR' }
    expect(decideDccVisibility(version, status)).toEqual({
      kind: 'error',
      errorReason: 'inconsistent_or_unknown',
    })
  })
})

