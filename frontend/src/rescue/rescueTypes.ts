export type RescueStatusLevel = 'ok' | 'review_required' | 'failed' | 'not_configured' | 'disabled' | 'skipped';

export interface RescueBootStatus {
  medium: {
    status: RescueStatusLevel;
    squashfs_hash_ok: boolean | null;
    evidence_ok: boolean | null;
    required: boolean;
  };
  network: {
    status: string;
    required: boolean;
    wifi_scan_started: boolean;
  };
  telemetry: {
    status: string;
    required: boolean;
    opt_in: boolean;
  };
  ui: {
    mode: 'react' | 'fallback_tui' | 'headless';
    status: string;
    shows_systemd_failures: boolean;
  };
  rs001: {
    status: string;
    reason: string;
    ready_for_operator_retest: boolean;
  };
}

export type RescueMenuAction =
  | 'safe_check'
  | 'backup_find'
  | 'network'
  | 'export_logs'
  | 'media_ram'
  | 'advanced'
  | 'power';
