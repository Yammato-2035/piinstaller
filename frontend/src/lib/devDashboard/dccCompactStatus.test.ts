import { describe, expect, it } from 'vitest'
import { deployDriftTone } from './dccCompactStatus'

describe('dccCompactStatus', () => {
  it('maps deploy drift colors', () => {
    expect(deployDriftTone('green')).toBe('green')
    expect(deployDriftTone('red')).toBe('red')
    expect(deployDriftTone('unknown')).toBe('gray')
  })
})
