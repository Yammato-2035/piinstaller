export const RESCUE_USB_CONFIRMATION_PHRASE = 'WRITE SETUPHELFER RESCUE USB'

export const RESCUE_USB_REQUIRED_CONFIRMATIONS = [
  'confirm_correct_usb',
  'confirm_data_destruction',
  'confirm_not_system_or_backup',
  'confirm_old_stick_replace',
  'confirm_iso_sha256_and_device',
] as const

export type RescueUsbConfirmationKey = (typeof RESCUE_USB_REQUIRED_CONFIRMATIONS)[number]

export type RescueUsbCandidate = {
  device: string
  name: string
  size?: string | null
  model?: string | null
  serial?: string | null
  transport?: string | null
  removable?: boolean
  partitions?: Array<{
    device?: string
    fstype?: string | null
    label?: string | null
    mountpoints?: string[]
  }>
  mountpoints?: string[]
  fstypes?: string[]
  setuphelfer_rescue_detected?: boolean
  setuphelfer_rescue_warning?: string | null
  previous_setuphelfer_version?: string | null
  selectable?: boolean
  blocked_reason?: string | null
  read_only?: boolean
}

export type RescueUsbCandidatesResponse = {
  status?: string
  read_only?: boolean
  dd_execution_allowed?: boolean
  auto_selection_forbidden?: boolean
  iso_path?: string | null
  iso_sha256?: string | null
  devices?: RescueUsbCandidate[]
}

export type RescueUsbSelectionRecord = {
  selected_device?: string | null
  write_allowed?: boolean
  generated_dd_command?: string | null
  blockers?: string[]
  confirmation_phrase_matched?: boolean
  operator_confirmations?: Partial<Record<RescueUsbConfirmationKey, boolean>>
  iso_sha256?: string | null
}

export function isRescueUsbDeviceBlocked(device: string): boolean {
  const d = device.trim()
  if (d === '/dev/sda') return true
  if (d.startsWith('/dev/nvme')) return true
  return false
}

export function canSubmitRescueUsbSelection(input: {
  selectedDevice: string
  confirmations: Partial<Record<RescueUsbConfirmationKey, boolean>>
  confirmationPhrase: string
  candidate?: RescueUsbCandidate | null
}): boolean {
  const { selectedDevice, confirmations, confirmationPhrase, candidate } = input
  if (!selectedDevice.trim()) return false
  if (isRescueUsbDeviceBlocked(selectedDevice)) return false
  if (candidate && candidate.selectable === false) return false
  if (candidate && candidate.transport && candidate.transport !== 'usb') return false
  for (const key of RESCUE_USB_REQUIRED_CONFIRMATIONS) {
    if (!confirmations[key]) return false
  }
  return confirmationPhrase.trim() === RESCUE_USB_CONFIRMATION_PHRASE
}

export function rescueUsbToolboxVisible(input: {
  developerCapabilityValid?: boolean
  dccVisible?: boolean
}): boolean {
  return Boolean(input.developerCapabilityValid && input.dccVisible)
}
