import gateStatus from '../../../../docs/evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json'

export type RescueIsoUsbGateStatus = typeof gateStatus

export function loadRescueIsoUsbGateStatus(): RescueIsoUsbGateStatus {
  return gateStatus as RescueIsoUsbGateStatus
}

export type RescueStickGateViewModel = {
  isoStatus: string
  isoVerified: boolean
  uefiBootReady: boolean
  isoBootProven: string
  usbWritten: string
  targetBooted: boolean
  windowsInspectExecutable: boolean
  blockers: string[]
  nextOperatorStep: string
  rawJson: string
}

export function buildRescueStickGateViewModel(
  status: RescueIsoUsbGateStatus = loadRescueIsoUsbGateStatus(),
): RescueStickGateViewModel {
  return {
    isoStatus: status.iso_status,
    isoVerified: status.iso_verified === true,
    uefiBootReady: status.uefi_boot_ready === true,
    isoBootProven: status.target_laptop_booted_from_stick
      ? 'target_yes'
      : status.iso_boot_proven_vm === 'partial'
        ? 'vm_partial'
        : 'no',
    usbWritten: String(status.usb_stick_written ?? 'unknown'),
    targetBooted: status.target_laptop_booted_from_stick === true,
    windowsInspectExecutable: status.windows_inspect_executable === true,
    blockers: (status.blockers ?? []).map((b) => b.id),
    nextOperatorStep: status.next_operator_step_de ?? status.next_operator_step_en ?? '—',
    rawJson: JSON.stringify(status, null, 2),
  }
}
