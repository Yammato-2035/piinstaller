/**
 * Heuristische Rollenklassifikation für Datenträgerkarten (Phase 2 read-only).
 */

import type { DiskInfo, PartitionInfo } from '../../api/partitionApi'

export type DiskRole = 'system' | 'backup' | 'rescue' | 'other'

export type DiskRoleBadge = 'ok' | 'warning' | 'blocked' | 'readonly'

function flattenPartitions(parts: PartitionInfo[]): PartitionInfo[] {
  return parts.flatMap((p) => [p, ...flattenPartitions(p.children ?? [])])
}

export function classifyDiskRole(disk: DiskInfo): DiskRole {
  const parts = flattenPartitions(disk.partitions)
  const haystack = [disk.display_name, disk.model, disk.vendor, disk.name]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  if (parts.some((p) => p.is_system_critical || p.mountpoint === '/' || p.mountpoint === '/boot')) {
    return 'system'
  }
  if (haystack.includes('setuphelfer') || haystack.includes('rescue') || haystack.includes('rettungsstick')) {
    return 'rescue'
  }
  const mountedExternal = parts.some(
    (p) =>
      p.mountpoint &&
      (p.mountpoint.startsWith('/media/') ||
        p.mountpoint.startsWith('/run/media/') ||
        p.mountpoint.startsWith('/mnt/')),
  )
  if (mountedExternal && !parts.some((p) => p.is_system_critical)) {
    return 'backup'
  }
  if (disk.size_bytes >= 500 * 1024 ** 3 && !parts.some((p) => p.is_system_critical)) {
    return 'backup'
  }
  return 'other'
}

export function roleBadgeForDisk(role: DiskRole, disk: DiskInfo): DiskRoleBadge {
  if (role === 'system') return 'blocked'
  if (role === 'rescue') return 'readonly'
  if (role === 'backup') return 'ok'
  const parts = flattenPartitions(disk.partitions)
  if (parts.some((p) => p.is_system_critical)) return 'warning'
  return 'ok'
}

export function detectOsHint(disk: DiskInfo): string | null {
  const parts = flattenPartitions(disk.partitions)
  const hasLinux = parts.some((p) => ['ext4', 'ext3', 'btrfs', 'xfs'].includes(p.fstype ?? ''))
  const hasMint = parts.some((p) => (p.label ?? '').toLowerCase().includes('mint'))
  if (hasMint || (hasLinux && parts.some((p) => p.mountpoint === '/'))) {
    return 'linux_mint'
  }
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
