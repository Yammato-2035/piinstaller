import { describe, expect, it } from 'vitest'
import { buildCardViewModelFromSample, loadOperatorReadonlySample } from './windowsRescueInspectReport'

describe('windowsRescueInspectReport', () => {
  it('loads operator readonly sample with dual nvme', () => {
    const sample = loadOperatorReadonlySample()
    expect(sample.hardware.nvme_devices?.length).toBe(2)
    expect(sample.bitlocker.access_allowed).toBe(false)
  })

  it('maps sample to yellow completion without ack', () => {
    const vm = buildCardViewModelFromSample()
    expect(vm.inspectReportCreated).toBe(true)
    expect(vm.completion.ampel).toBe('yellow')
    expect(vm.repartitionBlocked).toBe(true)
    expect(vm.dualbootPlanningOnly).toBe(true)
  })

  it('sample raw json has no secrets', () => {
    const vm = buildCardViewModelFromSample()
    expect(vm.rawJson.toLowerCase()).not.toContain('password')
    expect(vm.rawJson.toLowerCase()).not.toContain('file_content')
  })
})
