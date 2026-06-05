import { describe, expect, it } from 'vitest'
import {
  classifyDccBootState,
  hasDccBundleMarkers,
  type DccBootProbeResult,
} from './dccBootState'
import { DCC_BUNDLE_FIX_MARKER } from './dccGate'

function probe(overrides: Partial<DccBootProbeResult> = {}): DccBootProbeResult {
  return {
    versionHttp: 200,
    statusHttp: 200,
    statusCode: null,
    versionPayload: { install_profile: 'local_lab', dev_control_enabled: true },
    versionFetchFailed: false,
    statusFetchFailed: false,
    versionUrl: 'http://127.0.0.1:8000/api/version',
    statusUrl: 'http://127.0.0.1:8000/api/dev-dashboard/status',
    loadedUrl: 'http://127.0.0.1:3001/?window=cockpit',
    apiBaseUrl: 'http://127.0.0.1:8000',
    buildVersion: '1.0.0',
    buildId: 'test',
    frontendBuildProfile: 'release',
    ...overrides,
  }
}

describe('dccBootState', () => {
  it('exposes bundle fix marker for dist verification', () => {
    expect(DCC_BUNDLE_FIX_MARKER).toBe('DCC_BOOT_DIAGNOSTICS_V1')
    expect(hasDccBundleMarkers().ok).toBe(true)
  })

  it('classifies status 200 as dcc_active', () => {
    expect(classifyDccBootState(probe(), true)).toMatchObject({
      state: 'dcc_active',
      shouldShowDcc: true,
      dccExpectedVisible: true,
    })
  })

  it('classifies 404 PROFILE_ROUTE_BLOCKED as profile_blocked_release', () => {
    expect(
      classifyDccBootState(
        probe({ statusHttp: 404, statusCode: 'PROFILE_ROUTE_BLOCKED', versionPayload: { install_profile: 'release', dev_control_enabled: false } }),
        true,
      ),
    ).toMatchObject({ state: 'profile_blocked_release', shouldShowDcc: false })
  })

  it('allows DCC when version says release but status is 200', () => {
    expect(
      classifyDccBootState(
        probe({
          versionPayload: { install_profile: 'release', dev_control_enabled: false },
          statusHttp: 200,
        }),
        true,
      ),
    ).toMatchObject({ state: 'dcc_active', shouldShowDcc: true })
  })

  it('classifies unreachable API as api_unreachable', () => {
    expect(
      classifyDccBootState(
        probe({ versionHttp: 0, statusHttp: 0, versionFetchFailed: true, statusFetchFailed: true }),
        true,
      ),
    ).toMatchObject({ state: 'api_unreachable' })
  })

  it('classifies unexpected status code as api_error', () => {
    expect(
      classifyDccBootState(probe({ statusHttp: 500, statusCode: 'INTERNAL_ERROR' }), true),
    ).toMatchObject({ state: 'api_error' })
  })

  it('classifies missing bundle marker as stale_or_wrong_bundle', () => {
    expect(classifyDccBootState(probe(), false)).toMatchObject({ state: 'stale_or_wrong_bundle' })
  })

  it('classifies null probe as boot_loading when bundle ok', () => {
    expect(classifyDccBootState(null, true)).toMatchObject({ state: 'boot_loading' })
  })
})
