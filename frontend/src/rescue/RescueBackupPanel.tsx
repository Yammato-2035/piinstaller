import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchCloudTargetStatus,
  fetchRescueCapabilities,
  fetchStorageDiscovery,
  fetchSystemSummary,
  runFullBackupPlan,
  runSystemDiskRestoreExecute,
  runSystemDiskRestorePreview,
  runWindowsBackupExecute,
  runWindowsBackupVerify,
  saveCloudTargetLocal,
  writeEvidenceEvent,
  type BackupPlanResult,
  type RescueStorageDevice,
} from './rescueBackupApi';
import { backupSourceLabel, pickAutoBackupSource, sortBackupSources } from './backupSourceSelection';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

const BOOT_BG = '/assets/rescue/boot-menu/setuphelfer-boot-menu-de.png';
const LOGO = '/assets/rescue/logo/setuphelfer-logo2.png';

type TargetMode = 'hdd' | 'cloud';
type BackupScope = 'full' | 'selective_personal' | 'selective_custom';

function formatBytes(n?: number): string {
  if (!n) return '—';
  const gib = n / 1024 ** 3;
  return `${gib.toFixed(2)} GiB`;
}

export const RescueBackupPanel: React.FC<{ locale: RescueLocale; onBack: () => void }> = ({ locale, onBack }) => {
  const dict = getRescueDict(locale);
  const t = (key: string) => tPath(dict, key);
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<RescueStorageDevice[]>([]);
  const [targets, setTargets] = useState<RescueStorageDevice[]>([]);
  const [sourcePath, setSourcePath] = useState('');
  const [targetMode, setTargetMode] = useState<TargetMode>('hdd');
  const [targetPath, setTargetPath] = useState('');
  const [targetMount, setTargetMount] = useState('');
  const [capabilities, setCapabilities] = useState<{ booted_from_rescue?: boolean }>({});
  const [backupMode, setBackupMode] = useState<'raw_image' | 'linux_full_root_tar' | 'auto'>('auto');
  const [backupScope, setBackupScope] = useState<BackupScope>('full');
  const [customPathsText, setCustomPathsText] = useState('Users/*/Documents\nUsers/*/Desktop\nUsers/*/Pictures');
  const [encryptionRequested, setEncryptionRequested] = useState(false);
  const [verifyRequested, setVerifyRequested] = useState(true);
  const [systemSummary, setSystemSummary] = useState<Record<string, unknown> | null>(null);
  const [plan, setPlan] = useState<BackupPlanResult | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [execLoading, setExecLoading] = useState(false);
  const [execResult, setExecResult] = useState<Record<string, unknown> | null>(null);
  const [restoreArtifact, setRestoreArtifact] = useState('');
  const [restoreTargetPartition, setRestoreTargetPartition] = useState('');
  const [restoreConsent, setRestoreConsent] = useState(false);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreResult, setRestoreResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [cloudEndpoint, setCloudEndpoint] = useState('');
  const [cloudUser, setCloudUser] = useState('');
  const [cloudPassword, setCloudPassword] = useState('');
  const [cloudBucket, setCloudBucket] = useState('');
  const [cloudSaved, setCloudSaved] = useState(false);
  const autoPlanTriggered = useRef(false);

  useEffect(() => {
    (async () => {
      try {
        const [disc, caps, cloud, summary] = await Promise.all([
          fetchStorageDiscovery(),
          fetchRescueCapabilities(),
          fetchCloudTargetStatus(),
          fetchSystemSummary().catch(() => null),
        ]);
        setSystemSummary(summary as Record<string, unknown> | null);
        const sorted = sortBackupSources(disc.source_candidates || []);
        setSources(sorted);
        setTargets(disc.target_candidates || []);
        setCapabilities(caps);
        const pick = pickAutoBackupSource(disc);
        if (pick?.path) setSourcePath(pick.path);
        const ext = (disc.target_candidates || []).find(
          (t) => t.role === 'backup_target' || t.role === 'external_backup_hdd',
        );
        if (ext?.path) {
          setTargetPath(ext.path);
          if (ext.mountpoint) setTargetMount(String(ext.mountpoint));
        }
      } catch {
        setError(t('backupPanel.discoveryFailed'));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const selectedSource = useMemo(
    () => sources.find((s) => s.path === sourcePath),
    [sources, sourcePath],
  );

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
        source_type: selectedSource?.type === 'system_group' ? 'system_group' : selectedSource?.type || 'disk',
        source_size_bytes: selectedSource?.size_bytes || Number(selectedSource?.size) || 0,
        source_tran: selectedSource?.tran,
        source_fstype: selectedSource?.fstype,
        source_role: selectedSource?.role,
        source_label: selectedSource?.label,
        backup_mode: backupMode,
        backup_scope: backupScope,
        custom_paths:
          backupScope === 'selective_custom'
            ? customPathsText
                .split('\n')
                .map((line) => line.trim())
                .filter(Boolean)
            : [],
        target_mode: targetMode === 'cloud' ? 'cloud_pro' : 'external_hdd',
        target_mount: targetMount,
        target_device: targetPath,
        target_label: selectedTarget?.label,
        target_tran: selectedTarget?.tran,
        free_bytes: 0,
        fstype: selectedTarget?.fstype || selectedSource?.fstype || 'ext4',
        encryption_requested: encryptionRequested,
        verify_requested: verifyRequested,
        operator_confirm_source: true,
        operator_confirm_target: true,
        operator_confirm_no_restore: true,
        operator_confirm_no_wipe: true,
      };
      const result = await runFullBackupPlan(body);
      setPlan(result);
      await writeEvidenceEvent({
        event: { event_type: 'backup_plan_requested', plan_status: result.plan_status, plan_id: result.plan_id },
        stick_build_id: 'RS-P1',
      }).catch(() => undefined);
    } catch {
      setError(t('backupPanel.planCheckFailed'));
    } finally {
      setPlanLoading(false);
    }
  };

  useEffect(() => {
    if (loading || autoPlanTriggered.current || !sourcePath || !targetPath) return;
    autoPlanTriggered.current = true;
    const timer = window.setTimeout(() => {
      void runPlanCheck();
    }, 500);
    return () => window.clearTimeout(timer);
  }, [loading, sourcePath, targetPath]);

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
    const planTitle = blocked
      ? t('backupPanel.planTitleBlocked')
      : review
        ? t('backupPanel.planTitleReview')
        : t('backupPanel.planTitleOk');
    return (
      <div style={{ ...planCardStyle, borderColor: border, background: 'rgba(15,23,42,0.95)' }}>
        <h3 style={{ margin: '0 0 8px', color }}>{planTitle}</h3>
        {primaryErr ? (
          <p style={{ margin: '4px 0' }}>
            <strong>{t('backupPanel.cause')}:</strong> {primaryErr.message}
            {primaryErr.code ? ` (${primaryErr.code})` : ''}
          </p>
        ) : null}
        {primaryWarn ? (
          <p style={{ margin: '4px 0', color: '#fbbf24' }}>
            <strong>{t('backupPanel.hint')}:</strong> {primaryWarn.message}
            {primaryWarn.code ? ` (${primaryWarn.code})` : ''}
          </p>
        ) : null}
        {plan.wifi?.required === false && primaryWarn?.code === 'wifi_missing_but_not_required' ? (
          <p style={{ fontSize: 14, color: '#94a3b8' }}>{t('backupPanel.wifiNotRequired')}</p>
        ) : null}
        {plan.wifi?.blocks_plan ? (
          <p style={{ fontSize: 14 }}>{t('backupPanel.wifiBlocksPlan')}</p>
        ) : null}
        <p style={{ fontSize: 13, color: '#94a3b8' }}>
          {(plan as BackupPlanResult).next_safe_step || t('backupPanel.nextStepBlocked')}
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
      setError(t('backupPanel.cloudSaveFailed'));
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
            <h1 style={{ margin: 0, fontSize: 28 }}>{t('backupPanel.title')}</h1>
            <p style={{ margin: 0, color: '#94a3b8' }}>{t('backupPanel.subtitle')}</p>
          </div>
          <button type="button" onClick={onBack} style={btnSecondary}>
            {t('backupPanel.back')}
          </button>
        </header>

        {loading ? <p>{t('backupPanel.loadingDevices')}</p> : null}
        {error ? <p style={{ color: '#f87171' }}>{error}</p> : null}

        {systemSummary?.identity ? (
          <p style={{ color: '#94a3b8', fontSize: 14 }}>
            {t('backupPanel.computer')}: {(systemSummary.identity as { vendor?: string; model?: string }).vendor} /{' '}
            {(systemSummary.identity as { model?: string }).model} · {t('backupPanel.boot')}:{' '}
            {(systemSummary.identity as { boot_mode?: string }).boot_mode}
          </p>
        ) : null}

        <section style={panel}>
          <h2 style={h2}>{t('backupPanel.backupType')}</h2>
          <label style={label}>Umfang</label>
          <select
            value={backupScope}
            onChange={(e) => setBackupScope(e.target.value as BackupScope)}
            style={input}
          >
            <option value="full">Vollbackup (Systemvolume)</option>
            <option value="selective_personal">Persönliche Daten (Benutzerprofile)</option>
            <option value="selective_custom">Manuelle Auswahl</option>
          </select>
          {backupScope === 'selective_custom' ? (
            <>
              <label style={label}>Pfade (eine Zeile je Glob relativ zum Windows-Volume)</label>
              <textarea
                value={customPathsText}
                onChange={(e) => setCustomPathsText(e.target.value)}
                rows={5}
                style={{ ...input, fontFamily: 'monospace' }}
              />
            </>
          ) : null}
          <label style={{ ...label, marginTop: 12 }}>Technikmodus</label>
          <select value={backupMode} onChange={(e) => setBackupMode(e.target.value as typeof backupMode)} style={input}>
            <option value="auto">{t('backupPanel.modeAuto')}</option>
            <option value="raw_image">{t('backupPanel.modeRawImage')}</option>
            <option value="linux_full_root_tar">{t('backupPanel.modeLinuxTar')}</option>
          </select>
          <label style={{ ...label, display: 'flex', alignItems: 'center', gap: 8, marginTop: 12 }}>
            <input type="checkbox" checked={encryptionRequested} onChange={(e) => setEncryptionRequested(e.target.checked)} />
            {t('backupPanel.encryptionRequest')}
          </label>
          <label style={{ ...label, display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" checked={verifyRequested} onChange={(e) => setVerifyRequested(e.target.checked)} />
            {t('backupPanel.verifyRequired')}
          </label>
        </section>

        <section style={panel}>
          <h2 style={h2}>{t('backupPanel.source')}</h2>
          <p style={{ fontSize: 14, color: '#94a3b8', marginTop: 0 }}>{t('backupPanel.sourceHint')}</p>
          <select value={sourcePath} onChange={(e) => setSourcePath(e.target.value)} style={input}>
            {sources.map((s) => (
              <option key={s.path} value={s.path}>
                {backupSourceLabel(s)} · {formatBytes(s.size_bytes ?? s.size)}
              </option>
            ))}
          </select>
        </section>

        <section style={panel}>
          <h2 style={h2}>{t('backupPanel.targetDrive')}</h2>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button type="button" style={targetMode === 'hdd' ? btnPrimary : btnSecondary} onClick={() => setTargetMode('hdd')}>
              {t('backupPanel.targetHdd')}
            </button>
            <button type="button" style={targetMode === 'cloud' ? btnPrimary : btnSecondary} onClick={() => setTargetMode('cloud')}>
              {t('backupPanel.targetCloud')}
            </button>
          </div>

          {targetMode === 'hdd' ? (
            <>
              <label style={label}>{t('backupPanel.backupDevice')}</label>
              <select value={targetPath} onChange={(e) => setTargetPath(e.target.value)} style={input}>
                <option value="">{t('backupPanel.selectPlaceholder')}</option>
                {targets.map((t) => (
                  <option key={t.path} value={t.path}>
                    {t.path} · {t.label || t.fstype} · {formatBytes(t.size)}
                  </option>
                ))}
              </select>
              <label style={label}>{t('backupPanel.mountpoint')}</label>
              <input
                value={targetMount}
                onChange={(e) => setTargetMount(e.target.value)}
                placeholder="/media/.../Backup"
                style={input}
              />
            </>
          ) : (
            <>
              <p style={{ color: '#94a3b8', fontSize: 14 }}>{t('backupPanel.cloudHint')}</p>
              <label style={label}>{t('backupPanel.endpoint')}</label>
              <input value={cloudEndpoint} onChange={(e) => setCloudEndpoint(e.target.value)} style={input} />
              <label style={label}>{t('backupPanel.user')}</label>
              <input value={cloudUser} onChange={(e) => setCloudUser(e.target.value)} style={input} />
              <label style={label}>{t('backupPanel.passwordToken')}</label>
              <input type="password" value={cloudPassword} onChange={(e) => setCloudPassword(e.target.value)} style={input} />
              <label style={label}>{t('backupPanel.bucketOptional')}</label>
              <input value={cloudBucket} onChange={(e) => setCloudBucket(e.target.value)} style={input} />
              <button type="button" style={{ ...btnPrimary, marginTop: 8 }} onClick={saveCloud}>
                {t('backupPanel.saveLocal')}
              </button>
              {cloudSaved ? <p style={{ color: '#4ade80' }}>{t('backupPanel.cloudSavedOk')}</p> : null}
            </>
          )}
        </section>

        <section style={panel}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <button type="button" style={btnPrimary} onClick={runPlanCheck} disabled={planLoading}>
              {planLoading ? t('backupPanel.checking') : t('backupPanel.createPlan')}
            </button>
            <button
              type="button"
              style={btnPrimary}
              disabled={execLoading || !capabilities.booted_from_rescue || plan?.plan_status === 'blocked'}
              onClick={async () => {
                setError('');
                setExecLoading(true);
                setExecResult(null);
                try {
                  const body = {
                    source_device: sourcePath,
                    source_partition: sourcePath,
                    target_mount: targetMount,
                    target_device: targetPath,
                    backup_scope: backupScope,
                    custom_paths:
                      backupScope === 'selective_custom'
                        ? customPathsText
                            .split('\n')
                            .map((line) => line.trim())
                            .filter(Boolean)
                        : [],
                    operator_confirm_source: true,
                    operator_confirm_target: true,
                    lab_force_execute: backupScope !== 'full',
                  };
                  const result = await runWindowsBackupExecute(body);
                  setExecResult(result);
                  if (verifyRequested && result.artifact) {
                    const verified = await runWindowsBackupVerify({
                      artifact: result.artifact,
                      sha256: result.sha256,
                      manifest: result.manifest,
                    });
                    setExecResult({ ...result, verify: verified });
                  }
                } catch {
                  setError('Backup-Ausführung fehlgeschlagen');
                } finally {
                  setExecLoading(false);
                }
              }}
            >
              {execLoading ? 'Backup läuft…' : 'Backup starten'}
            </button>
            <button type="button" style={btnSecondary} onClick={() => window.location.reload()}>
              {t('backupPanel.refreshDevices')}
            </button>
          </div>
          {!capabilities.booted_from_rescue ? (
            <p style={{ color: '#fbbf24', marginTop: 12 }}>{t('backupPanel.rescueBootOnly')}</p>
          ) : null}
          {renderPlanFeedback()}
          {execResult ? (
            <pre style={pre}>{JSON.stringify(execResult, null, 2)}</pre>
          ) : null}
        </section>

        <section style={panel}>
          <h2 style={h2}>Systemdisk-Restore (Phase C, gated)</h2>
          <p style={{ fontSize: 14, color: '#fbbf24', marginTop: 0 }}>
            Standardmäßig blockiert. Benötigt one-shot Run-Control (
            <code>system-disk-restore-control.json</code>) und explizite Bestätigung. Nur selektives
            Tar-Artefakt; Vollimage-Restore bleibt deaktiviert.
          </p>
          <label style={label}>Backup-Artefakt</label>
          <input
            value={restoreArtifact}
            onChange={(e) => setRestoreArtifact(e.target.value)}
            placeholder={
              typeof execResult?.artifact === 'string'
                ? String(execResult.artifact)
                : '/media/.../selective-backup.tar.gz'
            }
            style={input}
          />
          <label style={label}>Zielpartition (NTFS, z. B. /dev/nvme0n1p4)</label>
          <input
            value={restoreTargetPartition}
            onChange={(e) => setRestoreTargetPartition(e.target.value)}
            placeholder="/dev/nvme0n1p4"
            style={input}
          />
          <label style={{ ...label, display: 'flex', alignItems: 'center', gap: 8, marginTop: 12 }}>
            <input
              type="checkbox"
              checked={restoreConsent}
              onChange={(e) => setRestoreConsent(e.target.checked)}
            />
            Ich bestätige explizit den Restore auf die Windows-Systempartition (destruktiv).
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
            <button
              type="button"
              style={btnSecondary}
              disabled={restoreLoading}
              onClick={async () => {
                setError('');
                setRestoreLoading(true);
                try {
                  const preview = await runSystemDiskRestorePreview({
                    artifact: restoreArtifact || execResult?.artifact,
                    target_device: restoreTargetPartition,
                    operator_consent: restoreConsent ? 'explicit' : '',
                    machine_vendor:
                      (systemSummary?.identity as { vendor?: string } | undefined)?.vendor || '',
                    machine_model:
                      (systemSummary?.identity as { model?: string } | undefined)?.model || '',
                  });
                  setRestoreResult(preview);
                } catch {
                  setError('Systemdisk-Restore-Preview fehlgeschlagen');
                } finally {
                  setRestoreLoading(false);
                }
              }}
            >
              Preview
            </button>
            <button
              type="button"
              style={{ ...btnPrimary, background: '#b91c1c' }}
              disabled={
                restoreLoading ||
                !capabilities.booted_from_rescue ||
                !restoreConsent ||
                !(restoreArtifact || execResult?.artifact) ||
                !restoreTargetPartition
              }
              onClick={async () => {
                setError('');
                setRestoreLoading(true);
                try {
                  const result = await runSystemDiskRestoreExecute({
                    artifact: restoreArtifact || execResult?.artifact,
                    sha256: execResult?.sha256,
                    manifest: execResult?.manifest,
                    target_partition: restoreTargetPartition,
                    operator_consent: 'explicit',
                    machine_vendor:
                      (systemSummary?.identity as { vendor?: string } | undefined)?.vendor || '',
                    machine_model:
                      (systemSummary?.identity as { model?: string } | undefined)?.model || '',
                  });
                  setRestoreResult(result);
                } catch {
                  setError('Systemdisk-Restore fehlgeschlagen');
                } finally {
                  setRestoreLoading(false);
                }
              }}
            >
              {restoreLoading ? 'Restore…' : 'Systemdisk-Restore ausführen'}
            </button>
          </div>
          {restoreResult ? <pre style={pre}>{JSON.stringify(restoreResult, null, 2)}</pre> : null}
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
