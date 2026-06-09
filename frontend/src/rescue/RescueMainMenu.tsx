import React from 'react';
import type { RescueMenuAction } from './rescueTypes';

const ACTIONS: RescueMenuAction[] = [
  'safe_check',
  'backup_find',
  'network',
  'export_logs',
  'media_ram',
  'advanced',
  'power',
];

export const RescueMainMenu: React.FC<{
  labels: Record<string, string>;
  selected: RescueMenuAction;
  onSelect: (action: RescueMenuAction) => void;
}> = ({ labels, selected, onSelect }) => (
  <nav aria-label="Rescue main menu" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
    {ACTIONS.map((action) => {
      const active = selected === action;
      return (
        <button
          key={action}
          type="button"
          onClick={() => onSelect(action)}
          style={{
            textAlign: 'left',
            padding: '14px 16px',
            borderRadius: 10,
            border: active ? '2px solid #38bdf8' : '1px solid rgba(148,163,184,0.35)',
            background: active ? 'rgba(56,189,248,0.12)' : 'rgba(15,23,42,0.75)',
            color: '#f8fafc',
            fontSize: 16,
            cursor: 'pointer',
            minHeight: 48,
          }}
        >
          {labels[action] ?? action}
        </button>
      );
    })}
  </nav>
);
