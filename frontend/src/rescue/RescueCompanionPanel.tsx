import React from 'react';

export const RescueCompanionPanel: React.FC = () => (
  <aside
    aria-label="Setuphelfer Companion"
    style={{
      flex: '0 0 220px',
      borderRadius: 12,
      padding: 16,
      background: 'linear-gradient(180deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95))',
      border: '1px solid rgba(148,163,184,0.3)',
      textAlign: 'center',
    }}
  >
    <div style={{ fontSize: 48, lineHeight: 1, marginBottom: 8 }}>🐼</div>
    <div style={{ color: '#e2e8f0', fontWeight: 600 }}>Setuphelfer</div>
    <div style={{ color: '#86efac', fontSize: 13 }}>Companion</div>
    <p style={{ color: '#94a3b8', fontSize: 12, marginTop: 12 }}>
      Sicher. Transparent. Anfängerfreundlich.
    </p>
  </aside>
);
