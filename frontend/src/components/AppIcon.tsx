import React from 'react'

export type IconCategory = 'navigation' | 'status' | 'devices' | 'process' | 'diagnostic'

const ICON_BASE = '/assets/icons'

const NAV_MAP: Record<string, string> = {
  dashboard: 'icon_dashboard.svg',
  installation: 'icon_installation.svg',
  wizard: 'icon_installation.svg',
  network: 'icon_network.svg',
  storage: 'icon_storage.svg',
  backup: 'icon_storage.svg',
  modules: 'icon_modules.svg',
  'app-store': 'icon_modules.svg',
  settings: 'icon_settings.svg',
  advanced: 'icon_advanced.svg',
  'control-center': 'icon_advanced.svg',
  diagnose: 'icon_diagnose.svg',
  'periphery-scan': 'icon_diagnose.svg',
  monitoring: 'icon_diagnose.svg',
  help: 'icon_help.svg',
  documentation: 'icon_help.svg',
}

const STATUS_MAP: Record<string, string> = {
  ok: 'status_ok.svg',
  warning: 'status_warning.svg',
  error: 'status_error.svg',
  loading: 'status_loading.svg',
  active: 'status_active.svg',
  complete: 'status_complete.svg',
  running: 'status_running.svg',
}

const DEVICE_MAP: Record<string, string> = {
  raspberrypi: 'device_raspberrypi.svg',
  sdcard: 'device_sdcard.svg',
  nvme: 'device_nvme.svg',
  usb: 'device_usb.svg',
  wifi: 'device_wifi.svg',
  ethernet: 'device_ethernet.svg',
  display: 'device_display.svg',
  audio: 'device_audio.svg',
}

const PROCESS_MAP: Record<string, string> = {
  search: 'process_search.svg',
  connect: 'process_connect.svg',
  prepare: 'process_prepare.svg',
  write: 'process_write.svg',
  verify: 'process_verify.svg',
  restart: 'process_restart.svg',
  complete: 'process_complete.svg',
}

const DIAG_MAP: Record<string, string> = {
  error: 'diagnose_error.svg',
  logs: 'diagnose_logs.svg',
  systemcheck: 'diagnose_systemcheck.svg',
  debug: 'diagnose_debug.svg',
  test: 'diagnose_test.svg',
}

/** CSS-Filter für Statusfarben (SVG als img, stroke erscheint schwarz). */
const STATUS_FILTERS: Record<string, string> = {
  ok: 'invert(58%) sepia(98%) saturate(456%) hue-rotate(101deg) brightness(95%) contrast(101%)',
  warning: 'invert(78%) sepia(89%) saturate(823%) hue-rotate(359deg) brightness(102%) contrast(96%)',
  error: 'invert(35%) sepia(98%) saturate(2342%) hue-rotate(337deg) brightness(98%) contrast(96%)',
  info: 'invert(50%) sepia(98%) saturate(1234%) hue-rotate(197deg) brightness(98%) contrast(96%)',
  muted: 'invert(55%) sepia(10%) saturate(100%) hue-rotate(200deg) brightness(90%) contrast(85%)',
}

interface AppIconProps {
  name: string
  category: IconCategory
  size?: 16 | 24 | 32 | 48 | 64
  className?: string
  alt?: string
  /** Nur für category="status": Farbzuordnung. */
  statusColor?: 'ok' | 'warning' | 'error' | 'info' | 'muted'
}

export function AppIcon({ name, category, size = 24, className = '', alt = '', statusColor }: AppIconProps) {
  const maps: Record<IconCategory, Record<string, string>> = {
    navigation: NAV_MAP,
    status: STATUS_MAP,
    devices: DEVICE_MAP,
    process: PROCESS_MAP,
    diagnostic: DIAG_MAP,
  }
  const fileName = maps[category][name] || ''
  const subdir = category === 'navigation' ? 'navigation' : category === 'status' ? 'status' : category === 'devices' ? 'devices' : category === 'process' ? 'process' : 'diagnostic'
  const src = fileName ? `${ICON_BASE}/${subdir}/${fileName}` : ''

  if (!src) return null

  const filterStyle = statusColor && STATUS_FILTERS[statusColor] ? { filter: STATUS_FILTERS[statusColor] } : undefined

  return (
    <img
      src={src}
      alt={alt || name}
      width={size}
      height={size}
      className={`inline-block shrink-0 ${className}`}
      style={{ width: size, height: size, ...filterStyle }}
    />
  )
}

export default AppIcon
