import React from 'react';

export const RescueEvidencePanel: React.FC<{ locale: 'de' | 'en' }> = ({ locale }) => (
  <section style={{ color: '#cbd5e1', fontSize: 14 }}>
    <p>
      {locale === 'de'
        ? 'Logs und Evidence werden lokal auf dem Rettungsstick gespeichert (best effort).'
        : 'Logs and evidence are stored locally on the rescue stick (best effort).'}
    </p>
    <ul style={{ marginTop: 8, paddingLeft: 18, color: '#94a3b8' }}>
      <li>setuphelfer/evidence/</li>
      <li>setuphelfer/logs/</li>
      <li>setuphelfer/profiles/machines/</li>
    </ul>
  </section>
);
