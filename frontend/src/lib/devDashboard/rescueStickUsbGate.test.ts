import { describe, expect, it } from 'vitest'
import { buildRescueStickGateViewModel, loadRescueIsoUsbGateStatus } from './rescueStickUsbGate'

describe('rescueStickUsbGate', () => {
  it('loads gate status with UEFI ready but USB not written', () => {
    const status = loadRescueIsoUsbGateStatus()
    expect(status.iso_verified).toBe(true)
    expect(status.uefi_boot_ready).toBe(true)
    expect(status.usb_stick_written).toBe('no')
    expect(status.windows_inspect_executable).toBe(false)
  })

  it('blocks windows inspect until USB boot with stick blockers', () => {
    const vm = buildRescueStickGateViewModel()
    expect(vm.windowsInspectExecutable).toBe(false)
    expect(vm.uefiBootReady).toBe(true)
    expect(vm.blockers).toContain('RESCUE_STICK_NOT_WRITTEN')
    expect(vm.blockers).toContain('RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET')
    expect(vm.blockers).toContain('WINDOWS_INSPECT_BLOCKED_UNTIL_USB_BOOT')
  })
})
