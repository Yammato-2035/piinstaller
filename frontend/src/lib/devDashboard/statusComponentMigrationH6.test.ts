import { describe, expect, it } from 'vitest'
import {
  governanceTrafficTransitionKind,
  isGreenTrafficLightLamp,
  isYellowTrafficLightLamp,
  lampAreaBorderClass,
  lampDotBackgroundClass,
  standaloneAmpelFromInput,
  standaloneMatrixCategoryFromAmpel,
  svgTrafficLightLampBackground,
  worstStandaloneAmpelOverall,
} from '../../viewmodels/statusViewModel'

/** H.6 slice: presentation and standalone outputs preserved. */
describe('statusComponentMigrationH6', () => {
  it('lamp dot presentation classes', () => {
    expect(lampDotBackgroundClass('green')).toContain('bg-emerald-400')
    expect(lampDotBackgroundClass('yellow', true)).toContain('bg-amber-400')
    expect(lampDotBackgroundClass('red')).toContain('bg-red-500')
    expect(lampAreaBorderClass('green')).toBe('border-emerald-500/90')
    expect(isYellowTrafficLightLamp('yellow')).toBe(true)
    expect(isGreenTrafficLightLamp('green')).toBe(true)
  })

  it('svg traffic light lamp colors', () => {
    expect(svgTrafficLightLampBackground('red', 'red', '#on', '#dim')).toBe('#on')
    expect(svgTrafficLightLampBackground('green', 'red', '#on', '#dim')).toBe('#dim')
  })

  it('governance transition kinds', () => {
    expect(governanceTrafficTransitionKind('red', 'green')).toBe('recovered')
    expect(governanceTrafficTransitionKind('green', 'red')).toBe('regressed')
    expect(governanceTrafficTransitionKind('green', 'yellow')).toBe('regressed')
    expect(governanceTrafficTransitionKind(undefined, 'green')).toBe(null)
  })

  it('standalone ampel normalization', () => {
    expect(standaloneAmpelFromInput('grün')).toBe('green')
    expect(standaloneAmpelFromInput('blocked')).toBe('red')
    expect(standaloneMatrixCategoryFromAmpel('green')).toBe('created')
    expect(standaloneMatrixCategoryFromAmpel('unknown')).toBe('blocked')
    expect(standaloneMatrixCategoryFromAmpel('gray')).toBe('planned')
    expect(worstStandaloneAmpelOverall('green', 'red')).toBe('red')
    expect(worstStandaloneAmpelOverall('green', 'yellow')).toBe('yellow')
    expect(worstStandaloneAmpelOverall('red', 'yellow')).toBe('red')
  })
})
