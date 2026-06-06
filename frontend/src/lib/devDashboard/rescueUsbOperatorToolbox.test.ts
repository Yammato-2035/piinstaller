import { describe, expect, it } from 'vitest'
import {
  RESCUE_USB_CONFIRMATION_PHRASE,
  canSubmitRescueUsbSelection,
  isRescueUsbDeviceBlocked,
  rescueUsbToolboxVisible,
} from './rescueUsbOperatorToolbox'

describe('rescueUsbOperatorToolbox', () => {
  const allChecks = {
    confirm_correct_usb: true,
    confirm_data_destruction: true,
    confirm_not_system_or_backup: true,
    confirm_old_stick_replace: true,
    confirm_iso_sha256_and_device: true,
  }

  it('blocks submission without checkboxes', () => {
    expect(
      canSubmitRescueUsbSelection({
        selectedDevice: '/dev/sdb',
        confirmations: {},
        confirmationPhrase: RESCUE_USB_CONFIRMATION_PHRASE,
        candidate: { device: '/dev/sdb', name: 'sdb', transport: 'usb', selectable: true },
      }),
    ).toBe(false)
  })

  it('blocks nvme devices', () => {
    expect(isRescueUsbDeviceBlocked('/dev/nvme0n1')).toBe(true)
    expect(
      canSubmitRescueUsbSelection({
        selectedDevice: '/dev/nvme0n1',
        confirmations: allChecks,
        confirmationPhrase: RESCUE_USB_CONFIRMATION_PHRASE,
      }),
    ).toBe(false)
  })

  it('blocks sda backup device', () => {
    expect(isRescueUsbDeviceBlocked('/dev/sda')).toBe(true)
  })

  it('allows usb transport with explicit confirmation', () => {
    expect(
      canSubmitRescueUsbSelection({
        selectedDevice: '/dev/sdb',
        confirmations: allChecks,
        confirmationPhrase: RESCUE_USB_CONFIRMATION_PHRASE,
        candidate: { device: '/dev/sdb', name: 'sdb', transport: 'usb', selectable: true },
      }),
    ).toBe(true)
  })

  it('shows toolbox only with developer capability', () => {
    expect(rescueUsbToolboxVisible({ developerCapabilityValid: true, dccVisible: true })).toBe(true)
    expect(rescueUsbToolboxVisible({ developerCapabilityValid: false, dccVisible: true })).toBe(false)
  })
})
