import { describe, expect, it } from 'vitest'
import {
  buildCardViewModelFromOperatorStatus,
  loadOperatorHardwareRunStatus,
  loadOperatorReadonlySample,
  operatorHardwareRunDisplay,
} from './windowsRescueInspectReport'

describe('windowsRescueInspectReport operator hardware run', () => {
  it('awaiting status shows missing operator run', () => {
    const status = loadOperatorHardwareRunStatus()
    expect(status.status).toBe('awaiting_operator_hardware_run')
    expect(status.sample_used_as_evidence).toBe(false)
    expect(operatorHardwareRunDisplay(status)).toBe('missing')
  })

  it('card stays yellow without real ingest', () => {
    const vm = buildCardViewModelFromOperatorStatus()
    expect(vm.operatorRun).toBe('missing')
    expect(vm.completion.ampel).toBe('yellow')
    expect(vm.repartitionBlocked).toBe(true)
    expect(vm.dualbootPlanningOnly).toBe(true)
  })

  it('sample is marked planning only not operator evidence', () => {
    const sample = loadOperatorReadonlySample()
    expect(sample.backup_selection.dry_run_only).toBe(true)
    const vm = buildCardViewModelFromOperatorStatus()
    expect(vm.rawJson).not.toContain('file_content')
  })
})
