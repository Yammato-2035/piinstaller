/**
 * Geräte- und Rollen-Icons für den Partitionshelfer (Lucide-basiert).
 */

import type { LucideIcon } from 'lucide-react'
import {
  HardDrive,
  Usb,
  Disc,
  Server,
  Monitor,
  LifeBuoy,
  Database,
  ShieldAlert,
  HelpCircle,
} from 'lucide-react'
import type { DiskInfo, StorageRoleInfo } from '../../api/partitionApi'

export type DeviceIconKind =
  | 'nvme'
  | 'sata_ssd'
  | 'hdd'
  | 'usb'
  | 'sd'
  | 'windows_system'
  | 'linux_system'
  | 'rescue'
  | 'backup'
  | 'unknown'

const ICON_MAP: Record<DeviceIconKind, LucideIcon> = {
  nvme: Server,
  sata_ssd: HardDrive,
  hdd: HardDrive,
  usb: Usb,
  sd: Disc,
  windows_system: Monitor,
  linux_system: ShieldAlert,
  rescue: LifeBuoy,
  backup: Database,
  unknown: HelpCircle,
}

export function inferDeviceIconKind(disk: DiskInfo, role?: StorageRoleInfo | null): DeviceIconKind {
  const storageRole = role?.role
  if (storageRole === 'windows_system_disk') return 'windows_system'
  if (storageRole === 'linux_system_disk' || storageRole === 'mixed_system_disk') return 'linux_system'
  if (storageRole === 'rescue_stick') return 'rescue'
  if (storageRole === 'backup_target' || storageRole === 'backup_source') return 'backup'

  const tran = (disk.tran ?? '').toLowerCase()
  const name = disk.name.toLowerCase()
  if (tran === 'usb' || disk.removable) return 'usb'
  if (tran === 'nvme' || name.startsWith('nvme')) return 'nvme'
  if (name.startsWith('mmcblk')) return 'sd'
  if (tran === 'sata' || name.startsWith('sd')) return 'sata_ssd'
  return 'unknown'
}

export function deviceIconForKind(kind: DeviceIconKind): LucideIcon {
  return ICON_MAP[kind] ?? HelpCircle
}

export function transportLabel(disk: DiskInfo): string {
  const tran = (disk.tran ?? '').toUpperCase()
  if (tran) return tran
  const name = disk.name.toLowerCase()
  if (name.startsWith('nvme')) return 'NVMe'
  if (name.startsWith('mmcblk')) return 'SD/MMC'
  if (name.startsWith('sd')) return 'SATA/USB'
  return '—'
}

export function filesystemSummary(disk: DiskInfo): string {
  const fsts = new Set<string>()
  const walk = (parts: DiskInfo['partitions']) => {
    for (const p of parts) {
      if (p.fstype) fsts.add(p.fstype)
      if (p.children?.length) walk(p.children)
    }
  }
  walk(disk.partitions)
  return [...fsts].slice(0, 4).join(' · ') || '—'
}
