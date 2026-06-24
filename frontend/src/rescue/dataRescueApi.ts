export interface DataRescueFolderStats {
  folder_id: string;
  label?: string;
  exists?: boolean;
  readable?: boolean;
  size_bytes: number;
  file_count: number;
}

export interface DataRescueProfile {
  profile_hash: string;
  display_label: string;
  folders: Record<string, DataRescueFolderStats>;
}

export interface DataRescueSource {
  mountpoint: string;
  device: string;
  filesystem: string;
  profiles: DataRescueProfile[];
  profile_count: number;
}

export interface DataRescueDiscovery {
  schema_version: number;
  read_only: boolean;
  write_allowed: boolean;
  execute_allowed: boolean;
  plan_status: string;
  sources: DataRescueSource[];
  source_count: number;
  windows_mount?: {
    status?: string;
    code?: string;
    detail?: string;
    mountpoint?: string;
    action?: string;
    users_path_missing?: boolean;
  } | null;
  diagnostics?: {
    situation?: string;
    ntfs_partition_count?: number;
    profiles_found?: number;
    hints?: string[];
  };
  teacher_mode?: {
    hints: Record<string, { title: string; body: string }>;
    topics: string[];
  };
}

export interface DataRescueEstimate {
  status: string;
  execute_allowed: boolean;
  write_allowed: boolean;
  estimation?: {
    breakdown: Record<string, { size_human: string; file_count: number }>;
    total_human: string;
    total_file_count: number;
    recommended_target_human: string;
  };
  errors?: Array<{ code: string; message: string }>;
}

export interface DataRescuePlan {
  plan_id?: string;
  plan_status?: string;
  execute_allowed?: boolean;
  write_allowed?: boolean;
  target_suitable?: boolean;
  recommendation?: string;
  source?: { display_label?: string; folder_ids?: string[] };
  target?: { mount?: string; free_human?: string };
  estimation?: DataRescueEstimate['estimation'];
  target_validation?: {
    free_human?: string;
    target_type?: string;
    risks?: string[];
  };
  errors?: Array<{ code: string; message: string }>;
  warnings?: Array<{ code: string; message: string }>;
}

export interface DataRescueExecuteResult {
  execute_started: boolean;
  job_id?: string;
  status?: string;
  target_path?: string;
  write_allowed?: boolean;
  source_readonly?: boolean;
  files_copied?: number;
  bytes_copied?: number;
  verify_status?: string;
  errors?: Array<{ code: string; message: string }>;
}

export interface DataRescueJob {
  job_id: string;
  status: string;
  target_path?: string;
  files_copied?: number;
  bytes_copied?: number;
  errors?: Array<{ code: string; message: string }>;
  verify?: { VERIFY_SUCCESS?: boolean; verify_status?: string };
}

export interface RescueStorageDevice {
  path: string;
  mountpoint?: string | null;
  label?: string;
  size_bytes?: number;
  role: string;
  tran?: string;
}

const base = () => (typeof window !== 'undefined' ? window.location.origin : '');

export async function fetchDataRescueDiscovery(locale = 'de'): Promise<DataRescueDiscovery> {
  const res = await fetch(`${base()}/api/rescue/data-rescue/discovery?locale=${encodeURIComponent(locale)}`);
  if (!res.ok) throw new Error('discovery_failed');
  return res.json();
}

export async function postDataRescueEstimate(body: {
  profile_hash: string;
  folder_ids: string[];
}): Promise<DataRescueEstimate> {
  const res = await fetch(`${base()}/api/rescue/data-rescue/estimate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('estimate_failed');
  return res.json();
}

export async function postDataRescuePlan(body: {
  profile_hash: string;
  folder_ids: string[];
  target_device: string;
  target_mount: string;
  target_mode?: string;
  locale?: string;
  operator_confirm?: boolean;
}): Promise<DataRescuePlan> {
  const res = await fetch(`${base()}/api/rescue/data-rescue/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('plan_failed');
  return res.json();
}

export async function postDataRescueExecute(body: {
  plan_id: string;
  operator_confirm: boolean;
}): Promise<DataRescueExecuteResult> {
  const res = await fetch(`${base()}/api/rescue/data-rescue/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('execute_failed');
  return res.json();
}

export async function fetchDataRescueJob(jobId: string): Promise<{ status: string; job?: DataRescueJob }> {
  const res = await fetch(`${base()}/api/rescue/data-rescue/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error('job_failed');
  return res.json();
}

export async function fetchDataRescueVerify(jobId: string): Promise<{ VERIFY_SUCCESS?: boolean; verify_status?: string }> {
  const res = await fetch(`${base()}/api/rescue/data-rescue/jobs/${encodeURIComponent(jobId)}/verify`);
  if (!res.ok) throw new Error('verify_failed');
  return res.json();
}

export async function fetchStorageDiscoveryForRescue(): Promise<{
  target_candidates: RescueStorageDevice[];
}> {
  const res = await fetch(`${base()}/api/rescue/storage/discovery`);
  if (!res.ok) throw new Error('storage_discovery_failed');
  return res.json();
}

export const DATA_RESCUE_FOLDER_IDS = [
  'documents',
  'pictures',
  'videos',
  'music',
  'downloads',
  'desktop',
  'onedrive',
] as const;
