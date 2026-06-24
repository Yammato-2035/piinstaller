/** Best-effort system actions via existing Setuphelfer API (no new contracts). */

export async function requestSystemReboot(): Promise<{ ok: boolean; message?: string }> {
  try {
    const res = await fetch('/api/system/reboot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
    const data = (await res.json()) as { status?: string; message?: string };
    return { ok: data.status === 'success', message: data.message };
  } catch {
    return { ok: false, message: 'reboot_request_failed' };
  }
}

export async function requestSystemShutdown(): Promise<{ ok: boolean; message?: string }> {
  try {
    const res = await fetch('/api/system/shutdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
    const data = (await res.json()) as { status?: string; message?: string };
    return { ok: data.status === 'success', message: data.message };
  } catch {
    return { ok: false, message: 'shutdown_request_failed' };
  }
}

export async function checkTerminalAvailable(): Promise<{ available: boolean; terminal?: string | null }> {
  try {
    const res = await fetch('/api/system/terminal-available', { cache: 'no-store' });
    if (!res.ok) return { available: false };
    return (await res.json()) as { available: boolean; terminal?: string | null };
  } catch {
    return { available: false };
  }
}

export async function exportRescueDiagnosticBundle(): Promise<{ ok: boolean; message?: string }> {
  try {
    const [evidenceRes, bootRes, versionRes] = await Promise.all([
      fetch('/api/rescue/evidence/status', { cache: 'no-store' }),
      fetch('/api/rescue/boot-status', { cache: 'no-store' }),
      fetch('/api/version', { cache: 'no-store' }),
    ]);
    const bundle = {
      exported_at: new Date().toISOString(),
      evidence: evidenceRes.ok ? await evidenceRes.json() : null,
      boot_status: bootRes.ok ? await bootRes.json() : null,
      version: versionRes.ok ? await versionRes.json() : null,
    };
    await fetch('/api/rescue/evidence/write-event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: { event_type: 'diagnostic_export_requested', exported_at: bundle.exported_at },
        stick_build_id: 'RS-P3G',
      }),
    }).catch(() => undefined);

    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `setuphelfer-rescue-diagnostic-${Date.now()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    return { ok: true, message: 'diagnostic_export_download_started' };
  } catch {
    return { ok: false, message: 'diagnostic_export_failed' };
  }
}
