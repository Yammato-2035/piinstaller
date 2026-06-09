import React from 'react';
import type { RescueBootStatus } from './rescueTypes';

export const RescueAdvancedOptions: React.FC<{
  status: RescueBootStatus;
  locale: 'de' | 'en';
}> = ({ status, locale }) => (
  <section style={{ color: '#94a3b8', fontSize: 13, fontFamily: 'monospace' }}>
    <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
      {JSON.stringify(
        {
          ui_mode: status.ui.mode,
          medium: status.medium,
          network_required: status.network.required,
          telemetry: status.telemetry,
          rs001: status.rs001,
        },
        null,
        2,
      )}
    </pre>
    <p style={{ fontFamily: 'sans-serif', marginTop: 12 }}>
      {locale === 'de'
        ? 'Experteninfos — keine systemd-Fehler im Anfängerbildschirm.'
        : 'Expert info — no raw systemd failures on beginner screen.'}
    </p>
  </section>
);
