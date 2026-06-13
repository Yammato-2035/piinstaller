import { describe, expect, it } from 'vitest'
import {
  deriveMonitoringOverallTrafficLight,
  trafficLightStateToLamp,
  worstTrafficLightLamp,
} from './trafficLightModel'

describe('trafficLightModel H.2', () => {
  it('worstTrafficLightLamp keeps legacy outputs', () => {
    expect(worstTrafficLightLamp([])).toBe('yellow')
    expect(worstTrafficLightLamp(['green', 'red', 'yellow'])).toBe('red')
    expect(worstTrafficLightLamp(['green', 'yellow'])).toBe('yellow')
  })

  it('trafficLightStateToLamp maps unknown to yellow', () => {
    expect(trafficLightStateToLamp('unknown')).toBe('yellow')
    expect(trafficLightStateToLamp('green')).toBe('green')
    expect(trafficLightStateToLamp('red')).toBe('red')
  })

  it('deriveMonitoringOverallTrafficLight unchanged shape', () => {
    const out = deriveMonitoringOverallTrafficLight(null)
    expect(out.lamp).toBe('yellow')
    expect(out.copyKey).toBe('stack_partial')
  })
})
