/**
 * Rollen-Mapping für Partitionshelfer – Backend-Klassifikation hat Vorrang.
 */

import type { DiskInfo, PartitionInfo, StorageRoleInfo } from '../../api/partitionApi'

export type DiskRole = 'system' | 'backup' | 'rescue' | 'other' | 'windows_system'

export type DiskRoleBadge = 'ok' | 'warning' | 'blocked' | 'readonly'

function flattenPartitions(parts: PartitionInfo[]): PartitionInfo[] {
  return parts.flatMap((p) => [p, ...flattenPartitions(p.children ?? [])])
}

export function getBackendStorageRole(disk: DiskInfo): StorageRoleInfo | null {
  return disk.storage_role ?? null
}

export function isFallbackClassification(disk: DiskInfo): boolean {
  return !disk.storage_role
}

export function classifyDiskRole(disk: DiskInfo): DiskRole {
  const backend = getBackendStorageRole(disk)
  if (backend) {
    switch (backend.role) {
      case 'linux_system_disk':
      case 'mixed_system_disk':
        return 'system'
      case 'windows_system_disk':
        return 'windows_system'
      case 'rescue_stick':
        return 'rescue'
      case 'backup_target':
      case 'backup_source':
        return 'backup'
      default:
        return 'other'
    }
  }

  const parts = flattenPartitions(disk.partitions)
  if (parts.some((p) => p.is_system_critical || p.mountpoint === '/' || p.mountpoint === '/boot')) {
    return 'system'
  }
  const haystack = [disk.display_name, disk.model, disk.vendor, disk.name].filter(Boolean).join(' ').toLowerCase()
  if (haystack.includes('setuphelfer') || haystack.includes('rescue') || haystack.includes('rettungsstick')) {
    return 'rescue'
  }
  const hasEfi = parts.some((p) => (p.parttypename ?? '').toLowerCase().includes('efi') || p.fstype === 'vfat')
  const hasNtfs = parts.some((p) => p.fstype === 'ntfs')
  if (hasEfi && hasNtfs) return 'windows_system'
  return 'other'
}

export function roleBadgeForDisk(role: DiskRole, disk: DiskInfo): DiskRoleBadge {
  const backend = getBackendStorageRole(disk)
  if (backend) {
    if (backend.risk_level === 'red' || !backend.write_allowed) {
      if (backend.role === 'rescue_stick') return 'readonly'
      return 'blocked'
    }
    if (backend.risk_level === 'yellow' || backend.confidence === 'low') return 'warning'
    if (backend.role === 'backup_target' && backend.confidence === 'high') return 'ok'
    return 'warning'
  }
  if (role === 'system' || role === 'windows_system') return 'blocked'
  if (role === 'rescue') return 'readonly'
  if (role === 'backup') return 'warning'
  const parts = flattenPartitions(disk.partitions)
  if (parts.some((p) => p.is_system_critical)) return 'warning'
  return 'warning'
}

export function diskRoleLabel(disk: DiskInfo, lang: 'de' | 'en'): string {
  const backend = getBackendStorageRole(disk)
  if (backend) {
    return lang === 'de' ? backend.ui_label_de : backend.ui_label_en
  }
  return ''
}

export function detectOsHint(disk: DiskInfo): string | null {
  const backend = getBackendStorageRole(disk)
  if (backend?.role === 'windows_system_disk') return 'windows'
  if (backend?.role === 'linux_system_disk') {
    const parts = flattenPartitions(disk.partitions)
    if (parts.some((p) => (p.label ?? '').toLowerCase().includes('mint'))) return 'linux_mint'
    return 'linux'
  }
  const parts = flattenPartitions(disk.partitions)
  const hasLinux = parts.some((p) => ['ext4', 'ext3', 'btrfs', 'xfs'].includes(p.fstype ?? ''))
  const hasMint = parts.some((p) => (p.label ?? '').toLowerCase().includes('mint'))
  if (hasMint || (hasLinux && parts.some((p) => p.mountpoint === '/'))) return 'linux_mint'
  if (hasLinux) return 'linux'
  if (parts.some((p) => p.fstype === 'ntfs')) return 'windows'
  return null
}

export function diskToTargetDevice(disk: DiskInfo): string {
  const n = disk.name.trim()
  return n.startsWith('/dev/') ? n : `/dev/${n}`
}

export type PartitionVisualRole = 'efi' | 'root' | 'home' | 'swap' | 'other'

export function classifyPartitionVisualRole(part: PartitionInfo): PartitionVisualRole {
  const mp = (part.mountpoint ?? '').toLowerCase()
  const pt = (part.parttypename ?? '').toLowerCase()
  const label = (part.label ?? '').toLowerCase()
  if (part.fstype === 'swap') return 'swap'
  if (mp === '/boot/efi' || mp === '/efi' || pt.includes('efi') || label.includes('efi')) return 'efi'
  if (mp === '/' || label.includes('root')) return 'root'
  if (mp.startsWith('/home') || label.includes('home')) return 'home'
  return 'other'
}

export const PARTITION_ROLE_COLORS: Record<PartitionVisualRole, string> = {
  efi: '#22c55e',
  root: '#3b82f6',
  home: '#a855f7',
  swap: '#6b7280',
  other: '#607D8B',
}
