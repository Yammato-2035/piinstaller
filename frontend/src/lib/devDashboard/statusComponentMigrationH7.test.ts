import { describe, expect, it } from 'vitest'
import {
  allTrafficLightLampsGreen,
  dashboardToneBorderClass,
  isDashboardTrafficFilterKey,
  riskLevelLabelKeyForLevel,
  roadmapDrawerRowToneClass,
  toolStatusToneFromRisk,
} from '../../viewmodels/statusViewModel'

/** H.7 final slice: presentation helper outputs preserved. */
describe('statusComponentMigrationH7', () => {
  it('risk level label keys', () => {
    expect(riskLevelLabelKeyForLevel('green')).toBe('risk.label.safe')
    expect(riskLevelLabelKeyForLevel('yellow')).toBe('risk.label.systemChange')
    expect(riskLevelLabelKeyForLevel('red')).toBe('risk.label.danger')
  })

  it('dashboard tone border classes', () => {
    expect(dashboardToneBorderClass('green')).toContain('emerald')
    expect(dashboardToneBorderClass('yellow')).toContain('amber')
    expect(dashboardToneBorderClass('gray')).toContain('slate')
    expect(isDashboardTrafficFilterKey('green')).toBe(true)
    expect(isDashboardTrafficFilterKey('backup')).toBe(false)
  })

  it('traffic light all-green check', () => {
    expect(allTrafficLightLampsGreen(['green', 'green'])).toBe(true)
    expect(allTrafficLightLampsGreen(['green', 'yellow'])).toBe(false)
  })

  it('roadmap drawer row tone classes', () => {
    expect(roadmapDrawerRowToneClass('green')).toContain('emerald')
    expect(roadmapDrawerRowToneClass('partial_green')).toContain('teal')
    expect(roadmapDrawerRowToneClass('deferred')).toContain('slate-600')
    expect(roadmapDrawerRowToneClass('blocked')).toContain('red')
  })

  it('tool status tone from risk', () => {
    expect(toolStatusToneFromRisk('green')).toBe('safe')
    expect(toolStatusToneFromRisk('red')).toBe('blocked')
    expect(toolStatusToneFromRisk('yellow')).toBe('review')
    expect(toolStatusToneFromRisk(undefined)).toBe('unknown')
  })
})
