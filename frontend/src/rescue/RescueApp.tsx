import React, { useEffect, useMemo, useState } from 'react';
import de from './i18n/de.json';
import en from './i18n/en.json';
import { fetchRescueBootStatus, loadOfflineBootStatus } from './rescueApi';
import { RescueAdvancedOptions } from './RescueAdvancedOptions';
import { RescueBootStatusPanel } from './RescueBootStatus';
import { RescueCompanionPanel } from './RescueCompanionPanel';
import { RescueEvidencePanel } from './RescueEvidencePanel';
import { RescueMainMenu } from './RescueMainMenu';
import { RescueNetworkPanel } from './RescueNetworkPanel';
import type { RescueMenuAction } from './rescueTypes';

export const RescueApp: React.FC = () => {
  const [locale, setLocale] = useState<'de' | 'en'>('de');
  const [selected, setSelected] = useState<RescueMenuAction>('safe_check');
  const [status, setStatus] = useState(loadOfflineBootStatus());

  const t = useMemo(() => (locale === 'de' ? de : en), [locale]);

  useEffect(() => {
    fetchRescueBootStatus().then(setStatus).catch(() => setStatus(loadOfflineBootStatus()));
  }, []);

  const detail = () => {
    if (selected === 'network') return <RescueNetworkPanel locale={locale} />;
    if (selected === 'export_logs') return <RescueEvidencePanel locale={locale} />;
    if (selected === 'advanced') return <RescueAdvancedOptions status={status} locale={locale} />;
    return (
      <p style={{ color: '#cbd5e1', fontSize: 15, lineHeight: 1.6 }}>
        {locale === 'de'
          ? 'Diese Aktion ist im MVP nur als read-only Vorschau vorbereitet. Keine Reparatur, kein Restore, keine Installation.'
          : 'This action is prepared as read-only preview in the MVP. No repair, restore, or install.'}
      </p>
    );
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'radial-gradient(circle at 20% 20%, #0f172a, #020617)',
        color: '#f8fafc',
        padding: 24,
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <header style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 32 }}>
          <span style={{ color: '#fff' }}>Setup</span>
          <span style={{ color: '#4ade80' }}>helfer</span>
        </h1>
        <p style={{ color: '#94a3b8', margin: '6px 0 0' }}>{t.subtitle}</p>
        <button
          type="button"
          onClick={() => setLocale((l) => (l === 'de' ? 'en' : 'de'))}
          style={{
            marginTop: 8,
            background: 'transparent',
            border: '1px solid #475569',
            color: '#cbd5e1',
            borderRadius: 6,
            padding: '4px 10px',
            cursor: 'pointer',
          }}
        >
          {t.lang}: {locale.toUpperCase()}
        </button>
      </header>

      <RescueBootStatusPanel status={status} labels={t.status} />

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <RescueCompanionPanel />
        <div style={{ flex: '1 1 320px' }}>
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>{t.menuPrompt}</h2>
          <RescueMainMenu labels={t.actions} selected={selected} onSelect={setSelected} />
          <div
            style={{
              marginTop: 16,
              padding: 16,
              borderRadius: 10,
              background: 'rgba(15,23,42,0.6)',
              border: '1px solid rgba(148,163,184,0.2)',
            }}
          >
            {detail()}
          </div>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 16 }}>{t.hint}</p>
        </div>
      </div>
    </div>
  );
};
