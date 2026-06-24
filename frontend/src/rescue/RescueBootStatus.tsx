import React from 'react';
import type { RescueBootStatus, RescueStatusLevel } from './rescueTypes';
import { rescueTheme as t } from './rescueTheme';

const statusColor = (s: string) => {
  if (s === 'ok') return t.statusOk;
  if (s === 'failed') return t.statusErr;
  if (s === 'review_required') return t.statusWarn;
  if (s === 'disabled' || s === 'skipped' || s === 'not_configured') return t.textDim;
  return t.statusWarn;
};

const statusIcon = (s: string) => {
  if (s === 'ok') return '✓';
  if (s === 'failed') return '✕';
  if (s === 'review_required') return '◐';
  if (s === 'disabled' || s === 'skipped' || s === 'not_configured') return '○';
  return '◐';
};

const statusClass = (s: string) => {
  if (s === 'ok') return 'rescue-status-ok';
  if (s === 'failed') return 'rescue-status-err';
  if (s === 'review_required') return 'rescue-status-warn';
  return 'rescue-status-neutral';
};

export function humanStatusLabel(
  value: string,
  labels: Record<string, string>,
): string {
  const key = value as RescueStatusLevel;
  return labels[key] ?? value;
}

export const RescueBootStatusPanel: React.FC<{
  status: RescueBootStatus;
  labels: Record<string, string>;
  statusLabels: Record<string, string>;
}> = ({ status, labels, statusLabels }) => (
  <section className="rescue-analysis-grid" aria-label="System status">
    {[
      { key: labels.medium, value: status.medium.status, icon: '💿' },
      { key: `${labels.network} (${labels.optional})`, value: status.network.status, icon: '📶' },
      {
        key: status.telemetry.opt_in
          ? `${labels.telemetry} (${labels.on})`
          : `${labels.telemetry} (${labels.off})`,
        value: status.telemetry.status,
        icon: '📡',
      },
    ].map((row) => (
      <div key={row.key} className={`rescue-analysis-card ${statusClass(row.value)}`}>
        <div className="rescue-analysis-card-label">
          <span className="rescue-analysis-card-icon" aria-hidden>
            {row.icon}
          </span>
          <span>{row.key}</span>
        </div>
        <div className="rescue-analysis-card-value" style={{ color: statusColor(row.value) }}>
          <span className="rescue-analysis-status-icon" aria-hidden>
            {statusIcon(row.value)}
          </span>
          {humanStatusLabel(row.value, statusLabels)}
        </div>
      </div>
    ))}
  </section>
);
