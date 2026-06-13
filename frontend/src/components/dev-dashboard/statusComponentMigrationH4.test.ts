import { describe, expect, it } from 'vitest'
import {
  dashboardToneFromInput,
  isDashboardGreenStatus,
  isGreenDashboardTone,
  riskWarningTitleKeyForLevel,
} from '../../viewmodels/statusViewModel'

/** H.4 slice: legacy helper outputs preserved after component migration. */
describe('statusComponentMigrationH4', () => {
  it('ready stable green detection outputs', () => {
    expect(isDashboardGreenStatus('green')).toBe(true)
    expect(isDashboardGreenStatus(true)).toBe(true)
    expect(isDashboardGreenStatus('GREEN')).toBe(true)
    expect(isDashboardGreenStatus('partial_green')).toBe(false)
    expect(isDashboardGreenStatus('yellow')).toBe(false)
    expect(isDashboardGreenStatus('')).toBe(false)
  })

  it('status card ok emphasis outputs', () => {
    expect(isGreenDashboardTone(dashboardToneFromInput('green'))).toBe(true)
    expect(isGreenDashboardTone(dashboardToneFromInput('GREEN'))).toBe(true)
    expect(isGreenDashboardTone(dashboardToneFromInput('yellow'))).toBe(false)
    expect(isGreenDashboardTone(dashboardToneFromInput('gray'))).toBe(false)
  })

  it('risk warning title key outputs', () => {
    expect(riskWarningTitleKeyForLevel('red')).toBe('risk.cardTitle.danger')
    expect(riskWarningTitleKeyForLevel('yellow')).toBe('risk.cardTitle.systemChange')
    expect(riskWarningTitleKeyForLevel('green')).toBe('risk.cardTitle.note')
    expect(riskWarningTitleKeyForLevel('unknown')).toBe('risk.cardTitle.note')
  })
})
