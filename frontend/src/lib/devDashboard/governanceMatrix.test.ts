import { describe, expect, it } from 'vitest'
import { buildCockpitAlerts, buildGovernanceMatrix } from './governanceMatrix'

describe('governanceMatrix', () => {
  it('marks runtime red when API offline', () => {
    const areas = buildGovernanceMatrix({
      dashboard: { runtime_gate: { passed: false, status: 'red', blockers: [] } },
      modules: [],
      source: 'snapshot',
      apiReachable: false,
    })
    const runtime = areas.find((a) => a.id === 'runtime')
    expect(runtime?.status).toBe('red')
    const alerts = buildCockpitAlerts(areas, { apiReachable: false, source: 'snapshot' })
    expect(alerts.some((a) => a.code === 'backend_api_unreachable')).toBe(true)
  })

  it('does not fake green runtime gate without API', () => {
    const areas = buildGovernanceMatrix({
      dashboard: { runtime_gate: { passed: true, status: 'green', blockers: [] } },
      modules: [],
      source: 'snapshot',
      apiReachable: false,
    })
    expect(areas.find((a) => a.id === 'runtime')?.status).toBe('red')
  })
})
