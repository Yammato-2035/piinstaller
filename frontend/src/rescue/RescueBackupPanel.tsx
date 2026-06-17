import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchCloudTargetStatus,
  fetchRescueCapabilities,
  fetchStorageDiscovery,
  runBackupPlan,
  saveCloudTargetLocal,
  writeEvidenceEvent,
  type BackupPlanResult,
  type RescueStorageDevice,
} from './rescueBackupApi';

const BOOT_BG = '/assets/rescue/boot-menu/setuphelfer-boot-menu-de.png';
const LOGO = '/assets/rescue/logo/setuphelfer-logo2.png';

type TargetMode = 'hdd' | 'cloud';

function formatBytes(n?: number): string {
  if (!n) return '—';
  const gib = n / 1024 ** 3;
  return `${gib.toFixed(2)} GiB`;
}

export const RescueBackupPanel: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<RescueStorageDevice[]>([]);
  const [targets, setTargets] = useState<RescueStorageDevice[]>([]);
  const [sourcePath, setSourcePath] = useState('');
  const [targetMode, setTargetMode] = useState<TargetMode>('hdd');
  const [targetPath, setTargetPath] = useState('');
  const [targetMount, setTargetMount] = useState('');
  const [capabilities, setCapabilities] = useState<{ booted_from_rescue?: boolean }>({});
  const [plan, setPlan] = useState<BackupPlanResult | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [error, setError] = useState('');
  const [cloudEndpoint, setCloudEndpoint] = useState('');
  const [cloudUser, setCloudUser] = useState('');
  const [cloudPassword, setCloudPassword] = useState('');
  const [cloudBucket, setCloudBucket] = useState('');
  const [cloudSaved, setCloudSaved] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [disc, caps, cloud] = await Promise.all([
          fetchStorageDiscovery(),
          fetchRescueCapabilities(),
          fetchCloudTargetStatus(),
        ]);
        setSources(disc.source_candidates || []);
        setTargets(disc.target_candidates || []);
        setCapabilities(caps);
        const win = (disc.source_candidates || []).find((d) => d.type === 'disk') || disc.source_candidates[0];
        if (win?.path) setSourcePath(win.path);
        const ext = (disc.target_candidates || []).find((t) => t.role === 'external_backup_hdd');
        if (ext?.path) {
          setTargetPath(ext.path);
          if (ext.mountpoint) setTargetMount(String(ext.mountpoint));
        }
      } catch {
        setError('Geräteerkennung fehlgeschlagen');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const selectedTarget = useMemo(
    () => targets.find((t) => t.path === targetPath),
    [targets, targetPath],
  );

  const runPlanCheck = async () => {
    setError('');
    setPlan(null);
    setPlanLoading(true);
    try {
      const body = {
        source_device: sourcePath,
        source_size_bytes: sources.find((s) => s.path === sourcePath)?.size || 0,
        source_type: 'windows_ntfs_disk',
        target_mode: targetMode === 'cloud' ? 'cloud' : 'external_hdd',
        target_mount: targetMount,
        target_device: targetPath,
        target_label: selectedTarget?.label,
        target_tran: selectedTarget?.tran,
        free_bytes: 0,
        fstype: selectedTarget?.fstype || 'ext4',
        wifi_status: 'missing',
        operator_confirm_source: true,
        operator_confirm_target: true,
        operator_confirm_no_restore: true,
        operator_confirm_no_wipe: true,
      };
      const result = await runBackupPlan(body);
      setPlan(result);
      await writeEvidenceEvent({
        event: { phase: 'backup_plan_check', plan_status: result.plan_status, plan_id: result.plan_id },
        stick_build_id: 'RS-F2B1',
      }).catch(() => undefined);
    } catch {
      setError('Backup-Plan konnte nicht geprüft werden (API nicht erreichbar).');
    } finally {
      setPlanLoading(false);
    }
  };

  const planCardStyle: React.CSSProperties = {
    marginTop: 12,
    padding: 14,
    borderRadius: 10,
    border: '1px solid',
  };

  const renderPlanFeedback = () => {
    if (!plan) return null;
    const blocked = plan.plan_status === 'blocked';
    const review = plan.plan_status === 'review_required';
    const color = blocked ? '#f87171' : review ? '#fbbf24' : '#4ade80';
    const border = blocked ? '#7f1d1d' : review ? '#78350f' : '#14532d';
    const primaryErr = plan.errors?.[0];
    const primaryWarn = plan.warnings?.[0];
    return (
      <div style={{ ...planCardStyle, borderColor: border, background: 'rgba(15,23,42,0.95)' }}>
        <h3 style={{ margin: '0 0 8px', color }}>Backup-Plan konnte {blocked ? 'nicht' : review ? 'mit Hinweisen' : ''} erstellt werden</h3>
        {primaryErr ? (
          <p style={{ margin: '4px 0' }}>
            <strong>Ursache:</strong> {primaryErr.message}
            {primaryErr.code ? ` (${primaryErr.code})` : ''}
          </p>
        ) : null}
        {primaryWarn ? (
          <p style={{ margin: '4px 0', color: '#fbbf24' }}>
            <strong>Hinweis:</strong> {primaryWarn.message}
            {primaryWarn.code ? ` (${primaryWarn.code})` : ''}
          </p>
        ) : null}
        {plan.wifi?.required === false && primaryWarn?.code === 'wifi_missing_but_not_required' ? (
          <p style={{ fontSize: 14, color: '#94a3b8' }}>
            WLAN wurde nicht gefunden. Für ein lokales Backup auf externe HDD ist WLAN nicht erforderlich.
          </p>
        ) : null}
        {plan.wifi?.blocks_plan ? (
          <p style={{ fontSize: 14 }}>
            Cloud-Backup wurde gewählt, aber es ist keine Netzwerkverbindung verfügbar. Wähle eine externe HDD oder richte WLAN ein.
          </p>
        ) : null}
        <p style={{ fontSize: 13, color: '#94a3b8' }}>
          Nächster Schritt: Geräte prüfen, Ziel wählen, dann „Plan erneut prüfen“. Ausführung bleibt gesperrt (RS-F2B.1).
        </p>
        <pre style={pre}>{JSON.stringify(plan, null, 2)}</pre>
      </div>
    );
  };

  const saveCloud = async () => {
    setError('');
    try {
      await saveCloudTargetLocal({
        endpoint: cloudEndpoint,
        username: cloudUser,
        password: cloudPassword,
        bucket: cloudBucket,
        enabled: true,
      });
      setCloudSaved(true);
      setCloudPassword('');
    } catch {
      setError('Cloud-Konfiguration konnte nicht lokal gespeichert werden');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc', position: 'relative' }}>
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url(${BOOT_BG})`,
          backgroundSize: 'cover',
          opacity: 0.3,
          pointerEvents: 'none',
        }}
      />
      <div style={{ position: 'relative', zIndex: 1, padding: 24, maxWidth: 960, margin: '0 auto' }}>
        <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <img src={LOGO} alt="" style={{ width: 56, height: 56, borderRadius: 10 }} />
          <div>
            <h1 style={{ margin: 0, fontSize: 28 }}>Backup — Block-Image</h1>
            <p style={{ margin: 0, color: '#94a3b8' }}>Windows/NTFS-Quelle → externes Ziel oder Cloud (lokal)</p>
          </div>
          <button type="button" onClick={onBack} style={btnSecondary}>
            Zurück
          </button>
        </header>

        {loading ? <p>Lade Geräte…</p> : null}
        {error ? <p style={{ color: '#f87171' }}>{error}</p> : null}

        <section style={panel}>
          <h2 style={h2}>Quelle (Windows)</h2>
          <select value={sourcePath} onChange={(e) => setSourcePath(e.target.value)} style={input}>
            {sources.map((s) => (
              <option key={s.path} value={s.path}>
                {s.path} · {s.fstype || 'disk'} · {formatBytes(s.size)} · {s.role}
              </option>
            ))}
          </select>
        </section>

        <section style={panel}>
          <h2 style={h2}>Ziellaufwerk</h2>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button type="button" style={targetMode === 'hdd' ? btnPrimary : btnSecondary} onClick={() => setTargetMode('hdd')}>
              Externe HDD/USB
            </button>
            <button type="button" style={targetMode === 'cloud' ? btnPrimary : btnSecondary} onClick={() => setTargetMode('cloud')}>
              Cloud (lokal, Test)
            </button>
          </div>

          {targetMode === 'hdd' ? (
            <>
              <label style={label}>Backup-Gerät</label>
              <select value={targetPath} onChange={(e) => setTargetPath(e.target.value)} style={input}>
                <option value="">— wählen —</option>
                {targets.map((t) => (
                  <option key={t.path} value={t.path}>
                    {t.path} · {t.label || t.fstype} · {formatBytes(t.size)}
                  </option>
                ))}
              </select>
              <label style={label}>Mountpoint (ext4 Backup-Partition)</label>
              <input
                value={targetMount}
                onChange={(e) => setTargetMount(e.target.value)}
                placeholder="/media/.../Backup"
                style={input}
              />
            </>
          ) : (
            <>
              <p style={{ color: '#94a3b8', fontSize: 14 }}>
                Cloud-Zugangsdaten werden nur lokal auf dem Stick gespeichert — nicht ins GitHub/Public-Repo.
              </p>
              <label style={label}>Endpoint / URL</label>
              <input value={cloudEndpoint} onChange={(e) => setCloudEndpoint(e.target.value)} style={input} />
              <label style={label}>Benutzer</label>
              <input value={cloudUser} onChange={(e) => setCloudUser(e.target.value)} style={input} />
              <label style={label}>Passwort / Token</label>
              <input type="password" value={cloudPassword} onChange={(e) => setCloudPassword(e.target.value)} style={input} />
              <label style={label}>Bucket / Pfad (optional)</label>
              <input value={cloudBucket} onChange={(e) => setCloudBucket(e.target.value)} style={input} />
              <button type="button" style={{ ...btnPrimary, marginTop: 8 }} onClick={saveCloud}>
                Lokal speichern
              </button>
              {cloudSaved ? <p style={{ color: '#4ade80' }}>Cloud-Konfiguration lokal gespeichert.</p> : null}
            </>
          )}
        </section>

        <section style={panel}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <button type="button" style={btnPrimary} onClick={runPlanCheck} disabled={planLoading}>
              {planLoading ? 'Prüfe…' : 'Plan erneut prüfen'}
            </button>
            <button type="button" style={btnSecondary} onClick={() => window.location.reload()}>
              Geräte neu erkennen
            </button>
          </div>
          {!capabilities.booted_from_rescue ? (
            <p style={{ color: '#fbbf24', marginTop: 12 }}>
              Backup-Ausführung nur nach Boot vom Rettungsstick — auf dem Dev-Laptop nur Plan/Preflight.
            </p>
          ) : null}
          {renderPlanFeedback()}
        </section>
      </div>
    </div>
  );
};

const panel: React.CSSProperties = {
  background: 'rgba(15,23,42,0.85)',
  border: '1px solid rgba(148,163,184,0.35)',
  borderRadius: 12,
  padding: 16,
  marginBottom: 16,
};
const h2: React.CSSProperties = { margin: '0 0 12px', fontSize: 17 };
const label: React.CSSProperties = { display: 'block', fontSize: 13, color: '#94a3b8', marginTop: 8 };
const input: React.CSSProperties = {
  width: '100%',
  marginTop: 4,
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid #475569',
  background: '#0f172a',
  color: '#f8fafc',
};
const btnPrimary: React.CSSProperties = {
  background: '#0284c7',
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  padding: '10px 16px',
  cursor: 'pointer',
  fontWeight: 600,
};
const btnSecondary: React.CSSProperties = {
  ...btnPrimary,
  background: 'rgba(15,23,42,0.9)',
  border: '1px solid #475569',
  marginLeft: 'auto',
};
const pre: React.CSSProperties = {
  marginTop: 12,
  background: '#0f172a',
  padding: 12,
  borderRadius: 8,
  overflow: 'auto',
  fontSize: 12,
};
