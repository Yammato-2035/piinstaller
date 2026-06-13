import { describe, expect, it } from 'vitest'
import {
  governanceDocsTrafficFromTone,
  governanceEvidenceTrafficFromTone,
  governanceTrafficFromInput,
  isGreenGovernanceTraffic,
  isRedGovernanceTraffic,
  isYellowGovernanceTraffic,
  roadmapFilterBucketFromStatus,
  worstGovernanceTrafficFromInputs,
} from '../../viewmodels/statusViewModel'

/** H.5 slice: utility migration outputs preserved. */
describe('statusComponentMigrationH5', () => {
  it('governanceTrafficFromInput preserves normTraffic outputs', () => {
    expect(governanceTrafficFromInput('green')).toBe('green')
    expect(governanceTrafficFromInput('YELLOW')).toBe('yellow')
    expect(governanceTrafficFromInput('red')).toBe('red')
    expect(governanceTrafficFromInput('blocked')).toBe('gray')
    expect(governanceTrafficFromInput(null)).toBe('gray')
    expect(governanceTrafficFromInput('')).toBe('gray')
  })

  it('worstGovernanceTrafficFromInputs preserves moduleTraffic outputs', () => {
    expect(worstGovernanceTrafficFromInputs(['green', 'red'])).toBe('red')
    expect(worstGovernanceTrafficFromInputs(['green', 'yellow'])).toBe('yellow')
    expect(worstGovernanceTrafficFromInputs(['green', 'green'])).toBe('green')
    expect(worstGovernanceTrafficFromInputs(['green', 'gray'])).toBe('yellow')
    expect(worstGovernanceTrafficFromInputs([])).toBe('gray')
  })

  it('governance area traffic helpers preserve matrix outputs', () => {
    expect(governanceEvidenceTrafficFromTone('green')).toBe('green')
    expect(governanceEvidenceTrafficFromTone('red')).toBe('red')
    expect(governanceEvidenceTrafficFromTone('yellow')).toBe('yellow')
    expect(governanceEvidenceTrafficFromTone('gray')).toBe('yellow')
    expect(governanceDocsTrafficFromTone('green')).toBe('green')
    expect(governanceDocsTrafficFromTone('yellow')).toBe('yellow')
  })

  it('roadmapFilterBucketFromStatus preserves statusBucket outputs', () => {
    expect(roadmapFilterBucketFromStatus('green')).toBe('green')
    expect(roadmapFilterBucketFromStatus('partial_green')).toBe('green')
    expect(roadmapFilterBucketFromStatus('planned')).toBe('yellow')
    expect(roadmapFilterBucketFromStatus('blocked')).toBe('red')
    expect(roadmapFilterBucketFromStatus('unknown')).toBe(null)
  })

  it('governance traffic predicates preserve prompt filters', () => {
    expect(isGreenGovernanceTraffic('green')).toBe(true)
    expect(isRedGovernanceTraffic('red')).toBe(true)
    expect(isYellowGovernanceTraffic('yellow')).toBe(true)
    expect(isYellowGovernanceTraffic('gray')).toBe(false)
  })
})
