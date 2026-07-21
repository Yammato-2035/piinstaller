import React, { useEffect, useState } from 'react';

type AutoE2eStatus = {
  active?: boolean;
  status?: string;
  phase?: string;
  phase_label_de?: string;
  last_progress?: string;
  run_id?: string;
};

/** Live banner for unattended GUI physical E2E (PI-RS-MSI-GUI-AUTO-BVR-001). */
export const RescueAutoE2eProgressBanner: React.FC = () => {
  const [data, setData] = useState<AutoE2eStatus | null>(null);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const res = await fetch('/api/rescue/auto-e2e-status', { cache: 'no-store' });
        if (!res.ok) return;
        const json = (await res.json()) as AutoE2eStatus;
        if (alive) setData(json);
      } catch {
        /* offline / backend not ready */
      }
    };
    void tick();
    const id = window.setInterval(() => void tick(), 1500);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, []);

  if (!data?.active) return null;

  return (
    <aside
      className="rescue-auto-e2e-banner"
      data-rescue-auto-e2e="true"
      aria-live="polite"
      style={{
        margin: '0 0 1rem',
        padding: '0.85rem 1rem',
        borderRadius: 12,
        border: '1px solid #334155',
        background: '#0f172a',
        color: '#f8fafc',
      }}
    >
      <strong style={{ display: 'block', marginBottom: 4 }}>Automatischer Lab-Lauf</strong>
      <div style={{ fontSize: '0.95rem', opacity: 0.95 }}>
        {data.phase_label_de || data.phase || 'läuft…'}
        {data.status ? ` · ${data.status}` : ''}
      </div>
      {data.last_progress ? (
        <div style={{ fontSize: '0.85rem', opacity: 0.8, marginTop: 4 }}>{data.last_progress}</div>
      ) : null}
      {data.run_id ? (
        <div style={{ fontSize: '0.75rem', opacity: 0.65, marginTop: 4 }}>Run-ID: {data.run_id}</div>
      ) : null}
    </aside>
  );
};
