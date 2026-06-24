import React, { useEffect, useState } from 'react';
import { RESCUE_LOGO } from './rescueAssets';
import type { RescueBootStatus } from './rescueTypes';

const STEPS = [
  'Datenträger werden erkannt',
  'Netzwerk wird geprüft',
  'Dienste werden gestartet',
  'Oberfläche wird geladen',
] as const;

function bootProgress(status: RescueBootStatus): number {
  let done = 0;
  if (status.medium.status === 'ok' || status.medium.status === 'skipped') done += 1;
  if (status.network.status === 'ok' || status.network.status === 'connected' || status.network.status === 'skipped') {
    done += 1;
  }
  if (status.ui.status === 'ok' || status.ui.mode === 'react') done += 1;
  if (status.telemetry.status !== 'not_configured') done += 1;
  return Math.min(100, Math.round((done / 4) * 100));
}

function stepDone(index: number, progress: number, ready: boolean): boolean {
  if (ready) return true;
  const thresholds = [15, 35, 60, 85];
  return progress >= thresholds[index];
}

const splashStyles: Record<string, React.CSSProperties> = {
  root: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0f172a',
    padding: 24,
    boxSizing: 'border-box',
    color: '#f8fafc',
    fontFamily: 'system-ui, sans-serif',
  },
  card: {
    maxWidth: 640,
    width: '100%',
    textAlign: 'center',
    padding: '32px 28px',
    borderRadius: 16,
    border: '1px solid rgba(150, 201, 61, 0.35)',
    background: 'linear-gradient(180deg, #0f172a 0%, #111111 100%)',
    boxShadow: '0 12px 40px rgba(0, 0, 0, 0.45)',
  },
  title: { margin: 0, fontSize: 36, fontWeight: 800 },
  subtitle: { margin: '8px 0 0', fontSize: 28, color: '#96c93d', fontWeight: 700 },
  list: { listStyle: 'none', margin: '20px 0 24px', padding: 0, textAlign: 'left', maxWidth: 420, marginLeft: 'auto', marginRight: 'auto' },
  progress: { height: 10, background: '#1e293b', borderRadius: 999, overflow: 'hidden' },
  progressBar: { height: '100%', background: '#96c93d', transition: 'width 0.3s ease' },
};

export const RescueBootSplash: React.FC<{
  status: RescueBootStatus;
  ready: boolean;
  onReady: () => void;
}> = ({ status, ready, onReady }) => {
  const [progress, setProgress] = useState(8);

  useEffect(() => {
    const target = ready ? 100 : Math.max(8, bootProgress(status));
    setProgress((p) => (target > p ? target : p));
    if (ready && progress >= 95) {
      const t = window.setTimeout(onReady, 350);
      return () => window.clearTimeout(t);
    }
    return undefined;
  }, [status, ready, onReady, progress]);

  useEffect(() => {
    if (!ready) {
      const tick = window.setInterval(() => {
        setProgress((p) => (p < 92 ? p + 2 : p));
      }, 320);
      return () => window.clearInterval(tick);
    }
    return undefined;
  }, [ready]);

  return (
    <div style={splashStyles.root} role="status" aria-live="polite" data-rescue-boot-splash="true">
      <div style={splashStyles.card} className="rescue-boot-splash-card">
        <img src={RESCUE_LOGO} alt="" style={{ width: 96, height: 96, objectFit: 'contain', marginBottom: 16 }} aria-hidden />
        <h1 style={splashStyles.title} className="rescue-boot-splash-title">Setuphelfer Rettungsstick</h1>
        <p style={splashStyles.subtitle} className="rescue-boot-splash-subtitle">Rettungsumgebung wird vorbereitet</p>
        <ul style={splashStyles.list} className="rescue-boot-status-list">
          {STEPS.map((label, index) => {
            const done = stepDone(index, progress, ready);
            return (
              <li
                key={label}
                className={done ? 'rescue-boot-status-done' : 'rescue-boot-status-pending'}
                style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 18, margin: '8px 0', color: done ? '#96c93d' : '#94a3b8' }}
              >
                <span aria-hidden>{done ? '✓' : '○'}</span>
                {label}
              </li>
            );
          })}
        </ul>
        <div style={splashStyles.progress} className="rescue-boot-progress" aria-hidden>
          <div className="rescue-boot-progress-bar" style={{ ...splashStyles.progressBar, width: `${progress}%` }} />
        </div>
      </div>
    </div>
  );
};
