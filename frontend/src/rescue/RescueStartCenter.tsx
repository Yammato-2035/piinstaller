import React, { useMemo, useState } from 'react';
import de from './i18n/de.json';
import en from './i18n/en.json';
import { RESCUE_START_MENU_ITEMS, type RescueMenuItemId } from './rescueMenuItems';
import type { RescueBootStatus } from './rescueTypes';

const BOOT_BG_DE = '/assets/rescue/boot-menu/setuphelfer-boot-menu-de.png';
const BOOT_BG_EN = '/assets/rescue/boot-menu/setuphelfer-boot-menu-en.png';
const LOGO = '/assets/rescue/logo/setuphelfer-logo2.png';

const iconGlyph: Record<string, string> = {
  monitor: '01',
  backup: '02',
  shield: '03',
  restore: '04',
  bug: '05',
  cloud: '06',
  gear: '07',
};

function tPath(dict: Record<string, unknown>, key: string): string {
  const parts = key.split('.');
  let cur: unknown = dict;
  for (const p of parts) {
    if (cur && typeof cur === 'object' && p in (cur as object)) {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return key;
    }
  }
  return typeof cur === 'string' ? cur : key;
}

export const RescueStartCenter: React.FC<{
  status: RescueBootStatus;
  locale: 'de' | 'en';
  onLocaleChange: (locale: 'de' | 'en') => void;
  onSelectItem?: (id: RescueMenuItemId) => void;
}> = ({ status, locale, onLocaleChange, onSelectItem }) => {
  const [selected, setSelected] = useState<RescueMenuItemId>('system_analyze');
  const dict = useMemo(() => (locale === 'de' ? de : en), [locale]);
  const bg = locale === 'de' ? BOOT_BG_DE : BOOT_BG_EN;

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#020617',
        color: '#f8fafc',
        fontFamily: 'system-ui, sans-serif',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url(${bg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          opacity: 0.35,
          pointerEvents: 'none',
        }}
      />
      <div style={{ position: 'relative', zIndex: 1, padding: 24, maxWidth: 1100, margin: '0 auto' }}>
        <header style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
          <img src={LOGO} alt="" style={{ width: 72, height: 72, borderRadius: 12 }} />
          <div>
            <h1 style={{ margin: 0, fontSize: 34 }}>
              <span style={{ color: '#fff' }}>Setup</span>
              <span style={{ color: '#4ade80' }}>helfer</span>
            </h1>
            <p style={{ margin: '4px 0 0', color: '#94a3b8' }}>{tPath(dict, 'subtitle')}</p>
          </div>
          <button
            type="button"
            onClick={() => onLocaleChange(locale === 'de' ? 'en' : 'de')}
            style={{
              marginLeft: 'auto',
              background: 'rgba(15,23,42,0.8)',
              border: '1px solid #475569',
              color: '#e2e8f0',
              borderRadius: 8,
              padding: '8px 12px',
              cursor: 'pointer',
            }}
          >
            {tPath(dict, 'footer.language')}
          </button>
        </header>

        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>
          {tPath(dict, 'status.medium')}: {status.medium.status} · {tPath(dict, 'status.network')}:{' '}
          {status.network.status}
        </p>

        <h2 style={{ fontSize: 18, marginBottom: 12 }}>{tPath(dict, 'menuPrompt')}</h2>
        <div style={{ display: 'grid', gap: 10 }}>
          {RESCUE_START_MENU_ITEMS.map((item) => {
            const active = selected === item.id;
            return (
              <button
                key={item.id}
                type="button"
                disabled={!item.enabled}
                onClick={() => {
                  setSelected(item.id);
                  onSelectItem?.(item.id);
                }}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '48px 1fr',
                  gap: 12,
                  textAlign: 'left',
                  padding: '14px 16px',
                  borderRadius: 12,
                  border: active ? '2px solid #38bdf8' : '1px solid rgba(148,163,184,0.35)',
                  background: active ? 'rgba(56,189,248,0.15)' : 'rgba(15,23,42,0.82)',
                  color: item.enabled ? '#f8fafc' : '#64748b',
                  cursor: item.enabled ? 'pointer' : 'not-allowed',
                  minHeight: 56,
                }}
              >
                <span
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 8,
                    background: '#1e293b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    color: '#38bdf8',
                  }}
                >
                  {iconGlyph[item.icon] ?? '·'}
                </span>
                <span>
                  <div style={{ fontWeight: 600 }}>{tPath(dict, item.titleKey)}</div>
                  <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>
                    {tPath(dict, item.subtitleKey)}
                  </div>
                </span>
              </button>
            );
          })}
        </div>

        <footer style={{ marginTop: 24, display: 'flex', gap: 12, flexWrap: 'wrap', color: '#64748b', fontSize: 12 }}>
          <span>F1 {tPath(dict, 'footer.help')}</span>
          <span>F2 {tPath(dict, 'footer.language')}</span>
          <span>F3 {tPath(dict, 'footer.network')}</span>
          <span>Esc {tPath(dict, 'footer.reboot')}</span>
          <span>Enter {tPath(dict, 'footer.select')}</span>
        </footer>
        <p style={{ color: '#475569', fontSize: 13, marginTop: 16 }}>{tPath(dict, 'hint')}</p>
      </div>
    </div>
  );
};
