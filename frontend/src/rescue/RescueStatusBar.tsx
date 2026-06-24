import React from 'react';
import type { RescueBootStatus } from './rescueTypes';
import { humanStatusLabel } from './RescueBootStatus';
import { getRescueDict, languageLabel, type RescueLocale } from './rescueLocale';
import { rescueTheme as t } from './rescueTheme';

function networkLabel(
  status: RescueBootStatus,
  offline: string,
  statusLabels: Record<string, string>,
): string {
  const s = status.network.status;
  if (!s || s === 'not_configured' || s === 'disabled') return offline;
  return humanStatusLabel(s, statusLabels);
}

export const RescueStatusBar: React.FC<{
  version: string;
  locale: RescueLocale;
  status: RescueBootStatus;
  labels: {
    offline: string;
    rescue: string;
  };
  statusLabels: Record<string, string>;
}> = ({ version, locale, status, labels, statusLabels }) => {
  const lang = languageLabel(getRescueDict(locale), locale);
  const net = networkLabel(status, labels.offline, statusLabels);
  const medium = humanStatusLabel(status.medium.status, statusLabels);
  const bootMode = status.ui.mode === 'react' ? labels.rescue : status.ui.mode;

  return (
    <footer
      className="rescue-status-bar"
      style={{
        padding: '12px 20px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 10,
        color: t.textMuted,
      }}
    >
      <span>v{version}</span>
      <span aria-hidden>·</span>
      <span>{net}</span>
      <span aria-hidden>·</span>
      <span>{bootMode}</span>
      <span aria-hidden>·</span>
      <span>{lang}</span>
      <span aria-hidden>·</span>
      <span>{medium}</span>
    </footer>
  );
};
