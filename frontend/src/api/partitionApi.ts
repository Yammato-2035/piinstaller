/**
 * partitionApi.ts – API-Client für den Partitionshelfer.
 * Kommuniziert mit dem Python-Backend über /api/partitions/*
 */

import { fetchApi } from '../api'

export interface PartitionInfo {
  name: string
  size_bytes: number
  size_human: string
  fstype: string | null
  mountpoint: string | null
  label: string | null
  uuid: string | null
  parttypename: string | null
  used_bytes: number
  free_bytes: number
  used_human: string
  free_human: string
  used_percent: number
  is_mounted: boolean
  is_system_critical: boolean
  display_name: string
  fs_info: FsInfo
  children: PartitionInfo[]
}

export interface FsInfo {
  name: string
  beschreibung: string
  empfehlung: string
  farbe: string
}

export type StorageRoleId =
  | 'linux_system_disk'
  | 'windows_system_disk'
  | 'mixed_system_disk'
  | 'backup_target'
  | 'backup_source'
  | 'rescue_stick'
  | 'external_data_disk'
  | 'internal_data_disk'
  | 'unknown_disk'

export interface StorageRoleInfo {
  device: string
  role: StorageRoleId
  confidence: 'high' | 'medium' | 'low'
  evidence: string[]
  write_allowed: boolean
  risk_level: 'green' | 'yellow' | 'red'
  ui_label_de: string
  ui_label_en: string
  transport?: string
  removable?: boolean
  filesystem_hints?: string[]
  classification_source?: string
}

export interface DiskInfo {
  name: string
  size_bytes: number
  size_human: string
  vendor: string | null
  model: string | null
  display_name: string
  tran?: string | null
  removable?: boolean
  partitions: PartitionInfo[]
  storage_role?: StorageRoleInfo
}

export interface DiskScanResult {
  disks: DiskInfo[]
  storage_roles?: StorageRoleInfo[]
  scanned_at: string
}

export interface SafetyWarning {
  stufe: 'info' | 'warnung' | 'gefahr' | 'kritisch'
  titel: string
  erklaerung: string
  empfehlung: string
  blockiert: boolean
  farbe: string
  icon: string
}

export interface SafetyCheckResult {
  partition_name: string
  warnungen: SafetyWarning[]
  hat_blockierende: boolean
}

export interface PlannedAction {
  id: string
  typ: string
  device_name: string
  beschreibung: string
  parameter: Record<string, unknown>
  status: 'geplant' | 'laufend' | 'erfolgreich' | 'fehler' | 'abgebrochen'
  execution_allowed: boolean
  user_message: string
}

export interface QueueApplyResult {
  erfolg: number
  fehler: number
  blockiert: number
  message?: string
}

export async function fetchDisks(): Promise<DiskScanResult> {
  const res = await fetchApi('/api/partitions/scan')
  if (!res.ok) throw new Error(`Scan fehlgeschlagen: ${res.status}`)
  return res.json()
}

export async function fetchSafetyCheck(
  partitionName: string,
  action: 'delete' | 'format' | 'resize'
): Promise<SafetyCheckResult> {
  const res = await fetchApi(
    `/api/partitions/safety-check?partition=${encodeURIComponent(partitionName)}&action=${action}`
  )
  if (!res.ok) throw new Error(`Safety-Check fehlgeschlagen: ${res.status}`)
  return res.json()
}

export async function fetchQueue(): Promise<PlannedAction[]> {
  const res = await fetchApi('/api/partitions/queue')
  if (!res.ok) throw new Error(`Queue laden fehlgeschlagen: ${res.status}`)
  const data = await res.json()
  return data.actions ?? []
}

export async function removeFromQueue(actionId: string): Promise<void> {
  await fetchApi(`/api/partitions/queue/${encodeURIComponent(actionId)}`, { method: 'DELETE' })
}

export async function clearQueue(): Promise<void> {
  await fetchApi('/api/partitions/queue', { method: 'DELETE' })
}

export async function applyQueue(confirmed: boolean): Promise<QueueApplyResult> {
  const res = await fetchApi('/api/partitions/queue/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmed }),
  })
  if (!res.ok) throw new Error(`Anwenden fehlgeschlagen: ${res.status}`)
  return res.json()
}

// ── Phase 2: Safety Contracts (read-only preview) ─────────────────────────

export type HardstopStatus = 'ok' | 'review_required' | 'blocked'
export type RiskLevel = 'green' | 'yellow' | 'red'

export interface HardstopMessage {
  code: string
  message: string
}

export interface HardstopEvaluation {
  status: HardstopStatus
  hardstops: HardstopMessage[]
  warnings: HardstopMessage[]
  risk_level: RiskLevel
  write_allowed: false
  codes: string[]
}

export interface HardstopPreviewResult {
  context: {
    target_device: string
    smart_status?: string
    same_as_backup_source?: boolean
    write_allowed: false
    [key: string]: unknown
  }
  evaluation: HardstopEvaluation
  storage_safety?: {
    status: string
    write_allowed: false
    hardstops?: HardstopMessage[]
    warnings?: HardstopMessage[]
  }
  write_allowed: false
}

export interface ManifestLayoutRow {
  device?: string | null
  size?: string | number | null
  fs_type?: string | null
  mountpoint?: string | null
  label?: string | null
  flags?: string[]
  source?: string
}

export interface ManifestLayoutPreviewResult {
  status: 'ok' | 'review_required' | 'unavailable' | 'blocked'
  source: string
  manifest_source?: 'inline' | 'null' | 'file_readonly'
  manifest_path?: string | null
  target_device: string | null
  original_layout: ManifestLayoutRow[]
  suggested_layout: ManifestLayoutRow[]
  layout?: Record<string, unknown>
  compatibility?: { target_device?: string | null; warnings?: HardstopMessage[]; errors?: HardstopMessage[] }
  warnings: HardstopMessage[]
  write_allowed: false
  generated_at?: string
}

export interface RestoreHandoffPreviewResult {
  status: 'ready' | 'review_required' | 'blocked'
  handoff_type: string
  target_device: string | null
  restore_execution_allowed: false
  write_allowed: false
  required_next_gates: string[]
  recommended_next_step?: string
  rescue_handoff_next?: string
  handoff_sources?: Record<string, unknown>
  codes: string[]
  evidence_refs?: string[]
}

export async function fetchPartitionHardstopPreview(
  targetDevice: string
): Promise<HardstopPreviewResult> {
  const q = new URLSearchParams({ target_device: targetDevice })
  const res = await fetchApi(`/api/partitions/hardstop-preview?${q}`)
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`Hardstop-Preview fehlgeschlagen: ${res.status} ${detail}`.trim())
  }
  return res.json()
}

export async function fetchManifestLayoutPreview(payload: {
  manifest: Record<string, unknown> | null
  target_device: string | null
  manifest_path?: string | null
}): Promise<ManifestLayoutPreviewResult> {
  const res = await fetchApi('/api/partitions/manifest-layout-preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`Manifest-Layout-Preview fehlgeschlagen: ${res.status} ${detail}`.trim())
  }
  return res.json()
}

export async function fetchRestoreHandoffPreview(payload: {
  target_device: string
  hardstop_result?: HardstopEvaluation | null
  manifest_layout_preview?: ManifestLayoutPreviewResult | null
  partition_plan_preview?: Record<string, unknown> | null
  backup_manifest_ref?: string | null
}): Promise<RestoreHandoffPreviewResult> {
  const res = await fetchApi('/api/partitions/restore-handoff-preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`Restore-Handoff-Preview fehlgeschlagen: ${res.status} ${detail}`.trim())
  }
  return res.json()
}

/** Zielgerät für Phase-2-Preview aus Partitionsname (z. B. sda1 → /dev/sda1). */
export function partitionNameToDevice(partitionName: string): string {
  const n = partitionName.trim()
  if (n.startsWith('/dev/')) return n
  return `/dev/${n}`
}

export const FS_FARBEN: Record<string, string> = {
  ext4: '#4CAF50',
  ext3: '#8BC34A',
  ntfs: '#2196F3',
  vfat: '#FF9800',
  exfat: '#FF5722',
  btrfs: '#9C27B0',
  xfs: '#00BCD4',
  swap: '#F44336',
}

export function getFarbe(fstype: string | null): string {
  return fstype ? (FS_FARBEN[fstype] ?? '#607D8B') : '#555E72'
}

export function getRiskLevel(stufe: SafetyWarning['stufe']): 'green' | 'yellow' | 'red' {
  if (stufe === 'info') return 'green'
  if (stufe === 'warnung') return 'yellow'
  return 'red'
}
