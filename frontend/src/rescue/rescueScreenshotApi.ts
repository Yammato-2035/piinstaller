/** Rescue UI screenshot evidence API. */

export type RescueScreenshotResponse = {
  status: 'ok' | 'blocked' | 'failed';
  path?: string | null;
  sha256?: string | null;
  tool?: string | null;
  metadata_path?: string | null;
  errors?: string[];
};

export async function fetchRescueScreenshotCapabilities(): Promise<Record<string, unknown>> {
  const res = await fetch('/api/rescue/ui/screenshot/capabilities', { cache: 'no-store' });
  if (!res.ok) return { status: 'blocked', errors: ['http_error'] };
  return (await res.json()) as Record<string, unknown>;
}

export async function captureRescueScreenshot(label: string): Promise<RescueScreenshotResponse> {
  const res = await fetch('/api/rescue/ui/screenshot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  });
  if (!res.ok) {
    return { status: 'failed', errors: [`http_${res.status}`] };
  }
  return (await res.json()) as RescueScreenshotResponse;
}
