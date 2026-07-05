import React, { useEffect, useState } from 'react';
import {
  collectMsiRs011bEvidence,
  fetchDisksStatus,
  fetchEvidenceStatusFull,
  fetchOperatorStatus,
  type DiskStatusEntry,
  type EvidenceStatusFull,
} from './rescueOperatorApi';
import {
  exportAiEvidence,
  fetchBootDiagnosis,
  fetchSystemHealth,
  healthScoreLabel,
  type BootDiagnosis,
  type HealthCheck,
  type SystemHealth,
} from './rescueMonitoringApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { rescueTheme as theme } from './rescueTheme';

function mountLabel(dict: Record<string, unknown>, status?: string): string {
  switch (status) {
    case 'mounted_rw':
      return tPath(dict, 'evidence.mountRw');
    case 'mounted_ro':
      return tPath(dict, 'evidence.mountRo');
    case 'not_mounted':
      return tPath(dict, 'evidence.notMounted');
    default:
      return status || tPath(dict, 'evidence.unknown');
  }
}

function statusColor(status?: string): string {
  switch (status) {
    case 'OK':
      return '#96c93d';
    case 'WARN':
      return '#fbbf24';
    case 'FAIL':
    case 'CRITICAL':
      return '#f87171';
    default:
      return '#94a3b8';
  }
}

export const RescueEvidenceStatusPanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = getRescueDict(locale);
  const t = (key: string) => tPath(dict, key);
  const yn = (value: boolean) => (value ? t('evidence.yes') : t('evidence.no'));

  const [disks, setDisks] = useState<DiskStatusEntry[]>([]);
  const [evidence, setEvidence] = useState<EvidenceStatusFull | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [bootDiag, setBootDiag] = useState<BootDiagnosis | null>(null);
  const [operatorSteps, setOperatorSteps] = useState<unknown[]>([]);
  const [exportMsg, setExportMsg] = useState('');
  const [msiCollectMsg, setMsiCollectMsg] = useState('');
  const [msiCollectBusy, setMsiCollectBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      fetchDisksStatus(),
      fetchEvidenceStatusFull(),
      fetchSystemHealth().catch(() => null),
      fetchBootDiagnosis().catch(() => null),
      fetchOperatorStatus().catch(() => ({})),
    ])
      .then(([d, e, h, b, op]) => {
        setDisks(d.devices || []);
        setEvidence(e.full || null);
        setHealth(h);
        setBootDiag(b);
        const steps = (op as { recent_steps?: unknown[] }).recent_steps || e.full?.operator_steps_recent || [];
        setOperatorSteps(Array.isArray(steps) ? steps : []);
      })
      .catch(() => setError(t('evidence.loadFailed')));
  }, [locale]);

  const problemChecks = (health?.checks || []).filter((c: HealthCheck) => c.status && c.status !== 'OK');

  async function onMsiCollect() {
    setMsiCollectMsg('');
    setMsiCollectBusy(true);
    try {
      const out = await collectMsiRs011bEvidence();
      const path = String(out.evidence_path || '');
      const st = String(out.status || 'ok');
      setMsiCollectMsg(`MSI Evidence: ${st}${path ? ` → ${path}` : ''} ${t('evidence.msiNoBackup')}`);
    } catch {
      setMsiCollectMsg(t('evidence.msiFailed'));
    } finally {
      setMsiCollectBusy(false);
    }
  }

  async function onAiExport() {
    setExportMsg('');
    try {
      const out = await exportAiEvidence({ ui_route: 'diagnostics' });
      setExportMsg(out.json_path || t('evidence.exportCreated'));
    } catch {
      setExportMsg(t('evidence.exportFailed'));
    }
  }

  if (error) return <p style={{ color: '#f87171' }}>{error}</p>;

  return (
    <section className="rescue-evidence-status" style={{ color: theme.text, fontSize: 16 }}>
      <h3 style={{ marginTop: 0 }}>{t('evidence.title')}</h3>

      {health ? (
        <div className="rescue-status-card" style={card} data-rescue-health-score={health.score}>
          <h4 style={h4}>{t('evidence.systemHealth')}</h4>
          <p style={{ margin: '4px 0', fontSize: 18 }}>
            <strong style={{ color: statusColor(health.overall_status) }}>{health.overall_status}</strong>
            {' · '}
            Score: {health.score}/100 ({healthScoreLabel(health.score)})
          </p>
          {problemChecks.length > 0 ? (
            <ul style={{ margin: '8px 0 0', paddingLeft: 18, color: '#94a3b8' }}>
              {problemChecks.slice(0, 8).map((c) => (
                <li key={c.check_id}>
                  [{c.status}] {c.message}
                  {c.next_step ? ` → ${c.next_step}` : ''}
                </li>
              ))}
            </ul>
          ) : (
            <p style={muted}>{t('evidence.noOpenIssues')}</p>
          )}
        </div>
      ) : null}

      {bootDiag ? (
        <div className="rescue-status-card" style={card} data-rescue-boot-diagnosis="true">
          <h4 style={h4}>{t('evidence.bootDiagnostics')}</h4>
          <p style={{ margin: '4px 0' }}>
            Boot Score: <strong>{bootDiag.boot_score ?? '—'}</strong>/100
            {bootDiag.total_boot_ms != null ? ` · ${Math.round(bootDiag.total_boot_ms / 1000)}s` : ''}
          </p>
          <ul style={{ margin: 0, paddingLeft: 18, color: '#94a3b8', fontSize: 14 }}>
            <li>
              {t('evidence.lastPhase')}: {bootDiag.last_phase || '—'} ({bootDiag.last_status || '—'})
            </li>
            <li>
              {t('evidence.bootStatusVisible')}: {yn(!!bootDiag.boot_status_visible)}
            </li>
            <li>
              {t('evidence.blackScreenWarning')}: {yn(!!bootDiag.black_screen_warning)}
            </li>
            <li>
              {t('evidence.firstScreenshot')}: {yn(!!bootDiag.first_screenshot_recorded)}
            </li>
            <li>
              SETUP_LOGS: {bootDiag.setup_logs_active ? t('evidence.active') : t('evidence.inactive')}
            </li>
            <li>
              {t('evidence.aiExport')}:{' '}
              {bootDiag.ai_export_available ? t('evidence.available') : '—'}
            </li>
          </ul>
          {(bootDiag.error_codes || []).length > 0 ? (
            <p style={{ color: '#fbbf24', marginTop: 8, fontSize: 13 }}>
              {(bootDiag.error_codes || []).join(', ')}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="rescue-status-card" style={card}>
        <h4 style={h4}>{t('evidence.detectedDrives')}</h4>
        {disks.length === 0 ? <p style={muted}>{t('evidence.noDevices')}</p> : null}
        {disks.map((d) => (
          <div key={d.path} style={row}>
            <strong>{d.path}</strong>
            <span style={muted}>
              {d.model || d.label || '—'} · {d.fstype || '—'} · {mountLabel(dict, d.mount_status)}
              {d.mountpoint ? ` @ ${d.mountpoint}` : ''}
            </span>
            <span style={role}>{d.role || t('evidence.unknownRole')}</span>
          </div>
        ))}
      </div>

      <div className="rescue-status-card" style={card}>
        <h4 style={h4}>{t('evidence.setupLogsTitle')}</h4>
        <p style={muted}>
          {evidence?.setup_logs?.persistent
            ? t('evidence.setupLogsPersistent')
            : t('evidence.setupLogsRamFallback')}
        </p>
        <ul style={{ margin: 0, paddingLeft: 18, color: '#94a3b8' }}>
          {(evidence?.log_files || []).slice(0, 12).map((f) => (
            <li key={f.path}>
              {f.path.split('/').slice(-3).join('/')} ({Math.round(f.size_bytes / 1024)} KiB)
            </li>
          ))}
        </ul>
        <button type="button" className="rescue-btn-secondary" style={{ marginTop: 10 }} onClick={onAiExport}>
          {t('evidence.exportForAi')}
        </button>
        <button
          type="button"
          className="rescue-btn-primary"
          style={{ marginTop: 10, marginLeft: 8 }}
          disabled={msiCollectBusy}
          onClick={onMsiCollect}
        >
          {msiCollectBusy ? t('evidence.msiCollecting') : t('evidence.msiCollect')}
        </button>
        {exportMsg ? <p style={{ ...muted, marginTop: 6 }}>{exportMsg}</p> : null}
        {msiCollectMsg ? <p style={{ ...muted, marginTop: 6 }}>{msiCollectMsg}</p> : null}
      </div>

      {operatorSteps.length > 0 ? (
        <div className="rescue-status-card" style={card}>
          <h4 style={h4}>{t('evidence.recentOperatorSteps')}</h4>
          <ul style={{ margin: 0, paddingLeft: 18, color: '#94a3b8', fontSize: 13 }}>
            {operatorSteps.slice(0, 10).map((s, i) => (
              <li key={i}>{typeof s === 'string' ? s : JSON.stringify(s).slice(0, 120)}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <details style={{ marginTop: 12 }}>
        <summary>{t('evidence.expertMode')}</summary>
        <pre style={pre}>{JSON.stringify({ disks, evidence, health, bootDiag }, null, 2)}</pre>
      </details>
    </section>
  );
};

const card: React.CSSProperties = {
  background: 'rgba(15,23,42,0.85)',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: 10,
  padding: 12,
  marginBottom: 12,
};
const h4: React.CSSProperties = { margin: '0 0 8px', fontSize: 15 };
const muted: React.CSSProperties = { color: '#94a3b8', fontSize: 14 };
const row: React.CSSProperties = { display: 'grid', gap: 2, marginBottom: 10 };
const role: React.CSSProperties = { fontSize: 13, color: '#96c93d' };
const pre: React.CSSProperties = {
  background: '#0f172a',
  padding: 10,
  borderRadius: 8,
  overflow: 'auto',
  fontSize: 11,
};
