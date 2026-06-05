import { describe, expect, it } from 'vitest'
import { buildRescueStickGateViewModel, loadRescueIsoUsbGateStatus } from './rescueStickUsbGate'

describe('rescueStickUsbGate', () => {
  it('loads gate status with ISO verified but USB not written', () => {
    const status = loadRescueIsoUsbGateStatus()
    expect(status.iso_verified).toBe(true)
    expect(status.usb_stick_written).toBe('no')
    expect(status.windows_inspect_executable).toBe(false)
  })

  it('blocks windows inspect with UEFI and patch blockers', () => {
    const vm = buildRescueStickGateViewModel()
    expect(vm.windowsInspectExecutable).toBe(false)
    expect(vm.uefiBootReady).toBe(false)
    expect(vm.blockers).toContain('RESCUE_ISO_UEFI_X64_NOT_READY')
    expect(vm.blockers).toContain('RESCUE_UEFI_PATCH_MKFS_FAILURE')
    expect(vm.blockers).toContain('WINDOWS_INSPECT_BLOCKED_BY_RESCUE_UEFI_BOOT')
  })
})
