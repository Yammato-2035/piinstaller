import type { RescueBootStatus } from './rescueTypes';

export interface RescueStorageDevice {
  path: string;
  type?: string;
  size?: number;
  fstype?: string;
  label?: string;
  mountpoint?: string | null;
  tran?: string;
  rm?: boolean;
  role: string;
}

export interface RescueStorageDiscovery {
  source_candidates: RescueStorageDevice[];
  target_candidates: RescueStorageDevice[];
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
  errors?: Array<{ code?: string; message?: string }>;
  warnings?: Array<{ code?: string; message?: string }>;
  wifi?: { required?: boolean; available?: boolean; blocks_plan?: boolean };
  capacity?: { required_bytes?: number; free_bytes?: number };
  telemetry?: { local_evidence_path?: string; persistent?: boolean };
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

export async function runBackupPreflight(body: Record<string, unknown>): Promise<BackupPreflightResult> {
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

export type { RescueBootStatus };
