import { describe, expect, it } from 'vitest'
import { appendGovernanceSnapshot } from './governanceHistory'
import type { GovernanceAreaStatus } from './governanceTypes'

function area(id: GovernanceAreaStatus['id'], status: GovernanceAreaStatus['status']): GovernanceAreaStatus {
  return {
    id,
    status,
    labelKey: `devDashboard.governance.area.${id}`,
    blockers: [],
    lastCheckedAt: new Date().toISOString(),
  }
}

describe('governanceHistory', () => {
  it('records green transition when status changes', () => {
    const s0 = { version: 1 as const, snapshots: [], timeline: [] }
    const r1 = appendGovernanceSnapshot(s0, {
      source: 'runtime_api',
      apiReachable: true,
      areas: [area('runtime', 'red')],
      runtimeGatePassed: false,
    })
    const r2 = appendGovernanceSnapshot(r1.store, {
      source: 'runtime_api',
      apiReachable: true,
      areas: [area('runtime', 'green')],
      runtimeGatePassed: true,
    })
    expect(r2.changedToGreen.some((a) => a.id === 'runtime')).toBe(true)
    expect(r2.newEvents.some((e) => e.kind === 'recovered' || e.kind === 'became_green')).toBe(true)
  })

  it('records api offline event', () => {
    const s0 = { version: 1 as const, snapshots: [], timeline: [] }
    const online = appendGovernanceSnapshot(s0, {
      source: 'runtime_api',
      apiReachable: true,
      areas: [area('runtime', 'green')],
      runtimeGatePassed: true,
    })
    const offline = appendGovernanceSnapshot(online.store, {
      source: 'unavailable',
      apiReachable: false,
      areas: [area('runtime', 'red')],
      runtimeGatePassed: null,
    })
    expect(offline.newEvents.some((e) => e.kind === 'api_offline')).toBe(true)
  })
})
