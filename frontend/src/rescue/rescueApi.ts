import type { RescueBootStatus } from './rescueTypes';

const DEFAULT_STATUS: RescueBootStatus = {
  medium: { status: 'review_required', squashfs_hash_ok: null, evidence_ok: null, required: true },
  network: { status: 'not_configured', required: false, wifi_scan_started: false },
  telemetry: { status: 'disabled', required: false, opt_in: false },
  ui: { mode: 'react', status: 'ready', shows_systemd_failures: false },
  rs001: { status: 'yellow', reason: 'hardware retest pending', ready_for_operator_retest: false },
};

export async function fetchRescueBootStatus(): Promise<RescueBootStatus> {
  try {
    const res = await fetch('/api/rescue/boot-status', { cache: 'no-store' });
    if (!res.ok) return DEFAULT_STATUS;
    const data = (await res.json()) as { boot_status?: RescueBootStatus };
    return data.boot_status ?? DEFAULT_STATUS;
  } catch {
    return DEFAULT_STATUS;
  }
}

export function loadOfflineBootStatus(): RescueBootStatus {
  return {
    ...DEFAULT_STATUS,
    network: { status: 'not_configured', required: false, wifi_scan_started: false },
    telemetry: { status: 'disabled', required: false, opt_in: false },
    ui: { mode: 'react', status: 'ready', shows_systemd_failures: false },
  };
}
