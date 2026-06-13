import { describe, expect, it } from 'vitest'
import { dashboardLegacyToneFromInput } from '../../viewmodels/statusViewModel'

/** H.3 slice: legacy helper outputs preserved after component migration. */
describe('statusComponentMigrationH3', () => {
  it('rescue pipeline itemTone outputs', () => {
    expect(dashboardLegacyToneFromInput('green')).toBe('green')
    expect(dashboardLegacyToneFromInput('partial_green')).toBe('yellow')
    expect(dashboardLegacyToneFromInput('blocked')).toBe('red')
    expect(dashboardLegacyToneFromInput('pending')).toBe('gray')
    expect(dashboardLegacyToneFromInput('unknown_token')).toBe('gray')
  })

  it('control center gate tone outputs', () => {
    expect(dashboardLegacyToneFromInput(true)).toBe('green')
    expect(dashboardLegacyToneFromInput('rot')).toBe('red')
    expect(dashboardLegacyToneFromInput('yellow')).toBe('yellow')
  })

  it('manual command safety tone outputs', () => {
    expect(dashboardLegacyToneFromInput('forbidden')).toBe('red')
    expect(dashboardLegacyToneFromInput('operator_action')).toBe('yellow')
    expect(dashboardLegacyToneFromInput('read_only')).toBe('green')
  })
})
