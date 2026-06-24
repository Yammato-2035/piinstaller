export interface LinuxMigrationDisk {
  disk_index: number;
  path: string;
  model: string;
  media_type: string;
  media_label: string;
  size_human: string;
  smart_status: string;
  beginner_summary: {
    headline: string;
    size_line: string;
    speed_line: string;
    suitable_for: string[];
  };
}

export interface StorageAssessment {
  path: string;
  model: string;
  media_type: string;
  size_human: string;
  smart_status: string;
  health_rating: 'excellent' | 'good' | 'warning' | 'critical';
  recommendation: string;
  speed_label?: string;
}

export interface SystemIdentity {
  manufacturer: string;
  model: string;
  mainboard?: string;
  cpu: string;
  ram_gb: number;
  boot_mode: string;
  secure_boot: string;
  bios_uefi?: string;
  identity_confirmed: boolean;
  confirmation_required: boolean;
}

export interface ReadinessArea {
  ok: boolean;
  status: 'green' | 'yellow' | 'red';
  label: string;
}

export interface MigrationReadiness {
  overall: 'green' | 'yellow' | 'red';
  areas: Record<string, ReadinessArea>;
}

export interface PartitionPreview {
  partition_plan_preview_only: boolean;
  profile_id: string;
  partitions: Array<{ role: string; size: string; notes?: string }>;
  disk_layouts?: Array<{
    disk_path?: string;
    disk_label?: string;
    purpose?: string;
    partitions?: Array<{ role: string; size: string; notes?: string }>;
  }>;
  write_allowed: boolean;
}

export interface LinuxMigrationAnalysis {
  contract_version: number;
  status: string;
  migration_status: string;
  write_allowed: boolean;
  execute_allowed: boolean;
  plan_only_notice: string;
  linux_migration_system_identity: SystemIdentity;
  linux_migration_storage_assessment: StorageAssessment[];
  migration_profile: string | null;
  migration_profile_options: string[];
  hardware: SystemIdentity & { is_msi_hardware?: boolean; board?: string };
  disks: LinuxMigrationDisk[];
  linux_recommendations: Record<
    string,
    Array<{
      id: string;
      name: string;
      version_hint: string;
      description_key: string;
      recommended: boolean;
      audience?: string;
      pros_keys?: string[];
      cons_keys?: string[];
      hardware_fit_key?: string;
    }>
  >;
  partition_plan_preview: PartitionPreview;
  dual_disk_recommendation?: {
    dual_disk?: boolean;
    system_disk?: { model?: string; speed_label?: string; recommendation?: string };
    data_disk?: { model?: string; speed_label?: string; recommendation?: string };
  };
  migration_readiness: MigrationReadiness;
  migration_variants: Array<{
    id: string;
    title_key: string;
    risk_level: 'green' | 'yellow' | 'red';
    data_loss_possible: boolean;
    pros_keys: string[];
    cons_keys: string[];
  }>;
  panda_hint_key?: string;
}

export interface LinuxMigrationInstallationPlan {
  contract_version: number;
  plan_status: string;
  status: string;
  write_allowed: boolean;
  execute_allowed: boolean;
  commands: string[];
  system_identity: SystemIdentity;
  storage_assessment: StorageAssessment[];
  migration_profile: string;
  linux_recommendation: { id?: string; name?: string; version_hint?: string; audience?: string };
  variant_id: string;
  partition_plan_preview: PartitionPreview;
  migration_readiness: MigrationReadiness;
  risks: Array<{ code?: string; message?: string }>;
  next_steps: string[];
  errors?: Array<{ code?: string; message?: string }>;
  exports: { json: LinuxMigrationInstallationPlan; markdown: string };
}

export async function fetchLinuxMigrationAnalysis(): Promise<LinuxMigrationAnalysis> {
  const res = await fetch('/api/rescue/linux-migration/analysis');
  if (!res.ok) throw new Error('analysis_failed');
  return res.json();
}

export async function postPartitionPreview(body: {
  migration_profile: string;
  distro_id: string;
  analysis?: LinuxMigrationAnalysis;
}): Promise<PartitionPreview> {
  const res = await fetch('/api/rescue/linux-migration/partition-preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('preview_failed');
  return res.json();
}

export async function postLinuxMigrationInstallationPlan(body: {
  identity_confirmed: boolean;
  migration_profile: string;
  distro_id: string;
  variant_id: string;
  backup_present?: boolean;
  backup_verified?: boolean;
  confirm_data_loss_understood?: boolean;
  confirm_phrase?: string;
  analysis?: LinuxMigrationAnalysis;
}): Promise<LinuxMigrationInstallationPlan> {
  const res = await fetch('/api/rescue/linux-migration/installation-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('plan_failed');
  return res.json();
}
