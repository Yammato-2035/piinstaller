import React from 'react';
import type { RescueBootStatus } from './rescueTypes';

const statusColor = (s: string) => {
  if (s === 'ok') return '#22c55e';
  if (s === 'failed') return '#ef4444';
  if (s === 'disabled' || s === 'skipped' || s === 'not_configured') return '#94a3b8';
  return '#f59e0b';
};

export const RescueBootStatusPanel: React.FC<{
  status: RescueBootStatus;
  labels: Record<string, string>;
}> = ({ status, labels }) => (
  <section
    style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
      gap: 12,
      marginBottom: 20,
    }}
  >
    {[
      { key: labels.medium, value: status.medium.status },
      { key: `${labels.network} (${labels.optional})`, value: status.network.status },
      { key: `${labels.telemetry} (${labels.off})`, value: status.telemetry.status },
    ].map((row) => (
      <div
        key={row.key}
        style={{
          padding: '12px 14px',
          borderRadius: 10,
          background: 'rgba(15,23,42,0.8)',
          border: '1px solid rgba(148,163,184,0.25)',
        }}
      >
        <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>{row.key}</div>
        <div style={{ fontSize: 16, fontWeight: 600, color: statusColor(row.value) }}>{row.value}</div>
      </div>
    ))}
  </section>
);
