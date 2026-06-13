import { describe, expect, it } from 'vitest'
import {
  buildDashboardStatusViewModel,
  buildStatusViewModel,
  buildTrafficLightViewModel,
  dashboardToneFromInput,
  normalizeStatusKind,
  statusViewModelDiagnostics,
  trafficLightLampFromInput,
  worstStatusViewModel,
  worstTrafficLightLampFromInputs,
} from './statusViewModel'

describe('statusViewModel', () => {
  it('maps green to ok/success', () => {
    const vm = buildTrafficLightViewModel('green')
    expect(vm.kind).toBe('ok')
    expect(vm.severity).toBe('success')
    expect(vm.isBlocking).toBe(false)
    expect(vm.isAvailable).toBe(true)
  })

  it('maps yellow to warning', () => {
    const vm = buildTrafficLightViewModel('yellow')
    expect(vm.kind).toBe('warning')
    expect(vm.severity).toBe('warning')
    expect(vm.isBlocking).toBe(false)
  })

  it('maps red to blocked/danger', () => {
    const vm = buildTrafficLightViewModel('red')
    expect(vm.kind).toBe('blocked')
    expect(vm.severity).toBe('danger')
    expect(vm.isBlocking).toBe(true)
    expect(vm.isAvailable).toBe(false)
  })

  it('maps gray to unavailable/neutral', () => {
    const vm = buildDashboardStatusViewModel('gray')
    expect(vm.kind).toBe('unavailable')
    expect(vm.severity).toBe('neutral')
    expect(vm.isAvailable).toBe(false)
    expect(vm.isBlocking).toBe(false)
  })

  it('maps unknown input to unknown', () => {
    expect(normalizeStatusKind('not-a-status')).toBe('unknown')
    expect(buildStatusViewModel(null).kind).toBe('unknown')
  })

  it('keeps sortRank stable for worst selection', () => {
    const models = [
      buildTrafficLightViewModel('green'),
      buildTrafficLightViewModel('red'),
      buildTrafficLightViewModel('yellow'),
    ]
    const worst = worstStatusViewModel(models)
    expect(worst.kind).toBe('blocked')
    expect(worst.sortRank).toBeLessThan(buildTrafficLightViewModel('yellow').sortRank)
  })

  it('documents no api fetch in viewmodel contract', () => {
    const diag = statusViewModelDiagnostics()
    expect(diag.api_fetches).toBe(false)
    expect(diag.component_migration).toBe('utility_h2_partial')
  })

  it('dashboardToneFromInput preserves deploy drift outputs', () => {
    expect(dashboardToneFromInput('green')).toBe('green')
    expect(dashboardToneFromInput('yellow')).toBe('yellow')
    expect(dashboardToneFromInput('red')).toBe('red')
    expect(dashboardToneFromInput('unknown')).toBe('gray')
  })

  it('worstTrafficLightLampFromInputs preserves empty→yellow', () => {
    expect(worstTrafficLightLampFromInputs([])).toBe('yellow')
    expect(worstTrafficLightLampFromInputs(['green', 'red'])).toBe('red')
  })

  it('trafficLightLampFromInput maps lamps', () => {
    expect(trafficLightLampFromInput('green')).toBe('green')
    expect(trafficLightLampFromInput('red')).toBe('red')
    expect(trafficLightLampFromInput('unknown')).toBe('yellow')
  })
})
