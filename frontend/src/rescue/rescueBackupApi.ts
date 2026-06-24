import type { RescueBootStatus } from './rescueTypes';

export interface RescueStorageDevice {
  path: string;
  type?: string;
  group_kind?: string;
  size?: number;
  size_bytes?: number;
  fstype?: string;
  label?: string;
  mountpoint?: string | null;
  parent_path?: string;
  tran?: string;
  rm?: boolean;
  role: string;
  tags?: string[];
  auto_select_score?: number;
  recommended?: boolean;
  partitions?: Array<{ path?: string; fstype?: string; label?: string; kind?: string }>;
}

export interface RescueStorageDiscovery {
  source_candidates: RescueStorageDevice[];
  system_source_candidates?: RescueStorageDevice[];
  target_candidates: RescueStorageDevice[];
  devices?: RescueStorageDevice[];
  blocked_devices: string[];
  cloud_target_available?: boolean;
}

export interface RescueCapabilities {
  booted_from_rescue?: boolean;
  cloud_target?: {
    local_unlock_test?: boolean;
    status?: { status?: string; enabled?: boolean };
  };
  endpoints?: {
    backup_execute?: boolean;
    restore_execute?: boolean;
    restore_preview?: boolean;
  };
}

export interface BackupPlanResult {
  plan_status?: 'ready' | 'review_required' | 'blocked';
  plan_id?: string;
  execute_allowed?: boolean;
  backup_mode?: string;
  full_backup?: boolean;
  next_safe_step?: string;
  encryption?: { key_status?: string; blocks_execute?: boolean };
  verify?: { verify_required?: boolean; verify_status?: string };
  cloud?: { pro_only?: boolean; plan_only?: boolean };
  errors?: Array<{ code?: string; message?: string }>;
  warnings?: Array<{ code?: string; message?: string }>;
  wifi?: { required?: boolean; available?: boolean; blocks_plan?: boolean };
  source?: { device?: string; scope?: string };
  source_scope?: string;
  target?: { device?: string; mount?: string; partition?: string };
  preflight?: { ok?: boolean; reason?: string };
  capacity?: { required_bytes?: number; free_bytes?: number; source_size_bytes?: number };
  telemetry?: { local_evidence_path?: string; persistent?: boolean };
}

export interface RescueSystemSummary {
  identity?: { vendor?: string; model?: string; boot_mode?: string };
  source_candidates?: RescueStorageDevice[];
  target_candidates?: RescueStorageDevice[];
  execute_allowed?: boolean;
}

const jsonHeaders = { 'Content-Type': 'application/json' };

export async function fetchRescueCapabilities(): Promise<RescueCapabilities> {
  const res = await fetch('/api/rescue/capabilities', { cache: 'no-store' });
  if (!res.ok) throw new Error('capabilities_failed');
  return res.json();
}

export async function fetchStorageDiscovery(): Promise<RescueStorageDiscovery> {
  const res = await fetch('/api/rescue/storage/discovery', { cache: 'no-store' });
  if (!res.ok) throw new Error('discovery_failed');
  return res.json();
}

export async function saveCloudTargetLocal(body: {
  endpoint: string;
  username?: string;
  password?: string;
  bucket?: string;
  enabled?: boolean;
}): Promise<unknown> {
  const res = await fetch('/api/rescue/cloud-target/local-config', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('cloud_config_failed');
  return res.json();
}

export async function runFullBackupPlan(body: Record<string, unknown>): Promise<BackupPlanResult> {
  const res = await fetch('/api/rescue/backup/full-plan', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('full_plan_failed');
  return res.json();
}

export async function fetchSystemSummary(): Promise<RescueSystemSummary> {
  const res = await fetch('/api/rescue/system/summary', { cache: 'no-store' });
  if (!res.ok) throw new Error('system_summary_failed');
  return res.json();
}

export async function runBackupPlan(body: Record<string, unknown>): Promise<BackupPlanResult> {
  const res = await fetch('/api/rescue/backup/plan', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('plan_failed');
  return res.json();
}

export async function writeEvidenceEvent(body: Record<string, unknown>): Promise<unknown> {
  const res = await fetch('/api/rescue/evidence/write-event', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('evidence_write_failed');
  return res.json();
}

export async function runBackupPreflight(body: Record<string, unknown>): Promise<{ preflight?: Record<string, unknown> }> {
  const res = await fetch('/api/rescue/backup/preflight', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('preflight_failed');
  return res.json();
}

export async function fetchCloudTargetStatus(): Promise<{ status?: string; enabled?: boolean }> {
  const res = await fetch('/api/rescue/cloud-target/status', { cache: 'no-store' });
  if (!res.ok) return { status: 'unknown' };
  return res.json();
}

export async function fetchTelemetryRuntimeStatus(): Promise<Record<string, unknown>> {
  const res = await fetch('/api/rescue/telemetry/status', { cache: 'no-store' });
  if (!res.ok) return {};
  return res.json() as Promise<Record<string, unknown>>;
}

export async function runTelemetryFunctionalTest(): Promise<{ ok: boolean }> {
  const res = await fetch('/api/rescue/telemetry/test', { method: 'POST', headers: jsonHeaders });
  if (!res.ok) return { ok: false };
  const data = (await res.json()) as { ok?: boolean; success?: boolean };
  return { ok: Boolean(data.ok ?? data.success) };
}

export type { RescueBootStatus };
