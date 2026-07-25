import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchRescueCapabilities } from './rescueBackupApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

type Ampel = 'green' | 'yellow' | 'red' | 'unknown';

type DiagnosisIssue = {
  code: string;
  severity?: string;
  ampel?: Ampel;
  next_action?: string;
};

type DiagnosisResult = {
  ampel?: Ampel;
  status?: string;
  issues?: DiagnosisIssue[];
  next_action?: string;
  bios_flash_allowed?: boolean;
};

type PlanResult = {
  status?: string;
  plan_hash?: string;
  error?: string;
  write_allowed?: boolean;
  windows_nvme_write_allowed?: boolean;
};

const API_BASE = '/api/rescue/install-assistant';

async function postJson<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

/** Install assistant preview — diagnosis + dry-run plan; execute stays gated until A5 handoff. */
export const RescueLinuxInstallPanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [previewAllowed, setPreviewAllowed] = useState(false);
  const [executeAllowed, setExecuteAllowed] = useState(false);
  const [booted, setBooted] = useState(false);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRescueCapabilities()
      .then((caps) => {
        setBooted(Boolean(caps.booted_from_rescue));
        const endpoints = caps.endpoints || {};
        setExecuteAllowed(Boolean(endpoints.linux_install) && endpoints.linux_install !== 'preview');
        setPreviewAllowed(
          Boolean(endpoints.linux_install_preview) ||
            endpoints.linux_install_capability === 'preview' ||
            endpoints.linux_install === 'preview',
        );
      })
      .catch(() => undefined);
  }, []);

  const runDiagnosis = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await postJson<DiagnosisResult>('/diagnosis', {
        locale: locale.startsWith('de') ? 'de' : 'en',
        assessment: {},
        disk_roles: {},
        bios_compare: {},
      });
      setDiagnosis(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'diagnosis_failed');
    } finally {
      setBusy(false);
    }
  }, [locale]);

  const runPlanDryRun = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await postJson<PlanResult>('/linux/install-plan', {
        linux_target: {
          intended_role: 'linux_target',
          serial_hash: 'demo',
          model: 'preview',
          size_bytes: 0,
        },
        root_gib: 200,
      });
      setPlan(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'plan_failed');
    } finally {
      setBusy(false);
    }
  }, []);

  const ampel = diagnosis?.ampel || 'unknown';

  return (
    <div className="rescue-linux-install-panel">
      <p className="rescue-section-intro">{tPath(dict, 'section.linuxInstall.intro')}</p>
      <aside className="rescue-migration-panda" role="note">
        <strong>{tPath(dict, 'guide.title')}:</strong> {tPath(dict, 'guide.step4')}
      </aside>

      <div className="rescue-plan-card rescue-install-diagnosis">
        <h3>{tPath(dict, 'section.linuxInstall.diagnosisTitle')}</h3>
        <p className={`rescue-ampel rescue-ampel-${ampel}`} data-ampel={ampel}>
          {tPath(dict, `section.linuxInstall.ampel.${ampel}`)}
        </p>
        {diagnosis?.next_action ? (
          <p className="rescue-hint">
            {tPath(dict, 'section.linuxInstall.nextAction')}: {diagnosis.next_action}
          </p>
        ) : null}
        {diagnosis?.issues?.length ? (
          <ul>
            {diagnosis.issues.map((iss) => (
              <li key={iss.code}>
                <code>{iss.code}</code>
                {iss.next_action ? ` — ${iss.next_action}` : ''}
              </li>
            ))}
          </ul>
        ) : null}
        <button type="button" disabled={busy || !previewAllowed} onClick={() => void runDiagnosis()}>
          {tPath(dict, 'section.linuxInstall.runDiagnosis')}
        </button>
      </div>

      <div className="rescue-plan-card">
        <h3>{tPath(dict, 'section.linuxInstall.planTitle')}</h3>
        <ul>
          <li>{tPath(dict, 'section.linuxInstall.stepAnalyze')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepBackup')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepPartition')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepInstall')}</li>
        </ul>
        {plan?.plan_hash ? (
          <p className="rescue-hint">
            {tPath(dict, 'section.linuxInstall.planHash')}: <code>{plan.plan_hash.slice(0, 16)}…</code>
          </p>
        ) : null}
        {plan?.error ? <p className="rescue-error">{plan.error}</p> : null}
        <button type="button" disabled={busy || !previewAllowed} onClick={() => void runPlanDryRun()}>
          {tPath(dict, 'section.linuxInstall.runPlanDryRun')}
        </button>
        <p className="rescue-linux-install-status">
          {executeAllowed
            ? tPath(dict, 'section.linuxInstall.statusReady')
            : previewAllowed
              ? tPath(dict, 'section.linuxInstall.statusPreview')
              : tPath(dict, 'section.linuxInstall.statusBlocked')}
        </p>
        <p className="rescue-hint">{tPath(dict, 'section.linuxInstall.wipeHint')}</p>
        <button type="button" disabled title={tPath(dict, 'section.linuxInstall.doubleConfirmDisabled')}>
          {tPath(dict, 'section.linuxInstall.doubleConfirm')}
        </button>
        {booted ? (
          <p className="rescue-linux-install-hint">{tPath(dict, 'section.linuxInstall.rescueHint')}</p>
        ) : null}
      </div>
      {error ? <p className="rescue-error">{error}</p> : null}
    </div>
  );
};
