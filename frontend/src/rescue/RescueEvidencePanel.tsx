import React from 'react';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { rescueTheme as theme } from './rescueTheme';

export const RescueEvidencePanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = getRescueDict(locale);
  return (
    <section style={{ color: theme.textMuted, fontSize: theme.fontSizeBase }}>
      <p>{tPath(dict, 'evidenceIntro.summary')}</p>
      <ul style={{ marginTop: 8, paddingLeft: 18, color: '#94a3b8' }}>
        <li>setuphelfer/evidence/</li>
        <li>setuphelfer/logs/</li>
        <li>setuphelfer/profiles/machines/</li>
      </ul>
    </section>
  );
};
