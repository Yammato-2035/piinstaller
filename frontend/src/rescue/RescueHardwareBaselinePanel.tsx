import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchHardwareBaselineStatus,
  postHardwareBaselineExtendedPreview,
  postHardwareBaselineQuick,
  type RescueBaselineResult,
  type RescueBaselineSubsystemResult,
} from './rescueHardwareApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

const SUBSYSTEM_ORDER: RescueBaselineSubsystemResult['subsystem'][] = ['memory', 'cpu', 'gpu', 'hdd', 'sata_ssd', 'nvme'];

function severityClass(severity: string | undefined | null): 'ok' | 'warn' | 'err' | 'neutral' {
  switch (severity) {
    case 'green':
      return 'ok';
    case 'yellow':
      return 'warn';
    case 'red':
      return 'err';
    default:
      return 'neutral';
  }
}

const SeverityBadge: React.FC<{ severity: string | null | undefined; label: string }> = ({ severity, label }) => {
  const cls = severityClass(severity);
  const icon = cls === 'ok' ? '✓' : cls === 'err' ? '✕' : cls === 'warn' ? '◐' : '○';
  return (
    <span className={`rescue-hw-badge rescue-hw-badge-${cls}`}>
      {icon} {label}
    </span>
  );
};

function statusLabel(dict: Record<string, unknown>, status: string): string {
  const key = `section.hardwareBaseline.status.${status}`;
  const label = tPath(dict, key);
  return label === key ? status : label;
}

function subsystemLabel(dict: Record<string, unknown>, subsystem: string): string {
  return tPath(dict, `section.hardwareBaseline.subsystem.${subsystem}`);
}

function gateStatusLabel(dict: Record<string, unknown>, status: string): string {
  return tPath(dict, `section.hardwareBaseline.gateStatus.${status}`);
}

const PermissionRow: React.FC<{ label: string; allowed: boolean; dict: Record<string, unknown> }> = ({ label, allowed, dict }) => (
  <li>
    {label}:{' '}
    <span className={`rescue-hw-badge rescue-hw-badge-${allowed ? 'ok' : 'err'}`}>
      {allowed ? tPath(dict, 'section.hardwareBaseline.allowedLabel') : tPath(dict, 'section.hardwareBaseline.blockedLabel')}
    </span>
  </li>
);

const SubsystemTile: React.FC<{ result: RescueBaselineSubsystemResult; dict: Record<string, unknown> }> = ({ result, dict }) => {
  const title = subsystemLabel(dict, result.subsystem) + (result.device_id ? ` (${result.device_id})` : '');
  return (
    <div className="rescue-baseline-tile" data-rescue-baseline-tile={result.subsystem}>
      <div className="rescue-baseline-tile-header">
        <span className="rescue-baseline-device-id">{title}</span>
        <SeverityBadge severity={result.severity} label={statusLabel(dict, result.status)} />
      </div>
      <div className="rescue-baseline-details">
        <p>
          {tPath(dict, 'section.hardwareBaseline.durationLabel')}: {result.duration_ms} ms —{' '}
          {tPath(dict, 'section.hardwareBaseline.checksRunLabel')}: {result.checks_run.length} —{' '}
          {tPath(dict, 'section.hardwareBaseline.checksSkippedLabel')}: {result.checks_skipped.length}
        </p>

        {result.findings.length > 0 ? (
          <div>
            <strong>{tPath(dict, 'section.hardwareBaseline.findingsTitle')}</strong>
            <ul className="rescue-migration-list">
              {result.findings.map((f, idx) => (
                <li key={`${f.code}-${idx}`}>
                  <SeverityBadge severity={f.severity} label={f.code} /> {f.message}
                  {f.category ? (
                    <span className="rescue-hw-hint">
                      {' '}
                      [{f.category}
                      {f.action_blocking === false
                        ? ', non-blocking'
                        : f.action_blocking === true
                          ? ', action-blocking'
                          : ''}
                      ]
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="rescue-hw-hint">{tPath(dict, 'section.hardwareBaseline.noFindings')}</p>
        )}

        {Object.keys(result.metrics).length > 0 ? (
          <details>
            <summary>{tPath(dict, 'section.hardwareBaseline.metricsTitle')}</summary>
            <ul className="rescue-migration-list">
              {Object.values(result.metrics).map((m) => (
                <li key={m.name}>
                  {m.name}: {String(m.value)}
                  {m.unit ? ` ${m.unit}` : ''}
                </li>
              ))}
            </ul>
          </details>
        ) : null}

        {result.recommendations.length > 0 ? (
          <div>
            <strong>{tPath(dict, 'section.hardwareBaseline.recommendationsTitle')}</strong>
            <ul className="rescue-migration-list">
              {result.recommendations.map((r, idx) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {result.extended_test.recommended || result.extended_test.required ? (
          <p className="rescue-hw-hint" data-rescue-baseline-extended-test="true">
            <strong>{tPath(dict, 'section.hardwareBaseline.extendedTestTitle')}</strong>:{' '}
            {result.extended_test.required
              ? tPath(dict, 'section.hardwareBaseline.extendedTestRequiredLabel')
              : tPath(dict, 'section.hardwareBaseline.extendedTestRecommendedLabel')}{' '}
            ({result.extended_test.test_type}, {result.extended_test.estimated_duration}) —{' '}
            {tPath(dict, 'section.hardwareBaseline.extendedTestNotStartedDisclaimer')}
          </p>
        ) : null}
      </div>
    </div>
  );
};

export const RescueHardwareBaselinePanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RescueBaselineResult | null>(null);
  const [hasRun, setHasRun] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHardwareBaselineStatus()
      .then((status) => {
        setHasRun(status.has_run);
      })
      .catch(() => setError(tPath(dict, 'section.hardwareBaseline.loadError')))
      .finally(() => setLoading(false));
  }, [dict]);

  const runQuick = () => {
    setRunning(true);
    setError(null);
    postHardwareBaselineQuick()
      .then((r) => {
        setResult(r);
        setHasRun(true);
      })
      .catch(() => setError(tPath(dict, 'section.hardwareBaseline.loadError')))
      .finally(() => setRunning(false));
  };

  const runExtendedPreview = () => {
    setRunning(true);
    setError(null);
    postHardwareBaselineExtendedPreview()
      .then((r) => {
        setResult(r);
        setHasRun(true);
      })
      .catch(() => setError(tPath(dict, 'section.hardwareBaseline.loadError')))
      .finally(() => setRunning(false));
  };

  if (loading) {
    return <p>{tPath(dict, 'section.hardwareBaseline.loading')}</p>;
  }

  const orderedSubsystems = result
    ? [...result.subsystems].sort((a, b) => SUBSYSTEM_ORDER.indexOf(a.subsystem) - SUBSYSTEM_ORDER.indexOf(b.subsystem))
    : [];

  return (
    <section className="rescue-hardware-baseline-panel rescue-plan-card" data-rescue-hardware-baseline="true">
      <h3>{tPath(dict, 'section.hardwareBaseline.title')}</h3>
      <p className="rescue-section-intro">{tPath(dict, 'section.hardwareBaseline.intro')}</p>

      {error ? (
        <p className="rescue-notice-banner" role="status">
          {error}
        </p>
      ) : null}

      <div className="rescue-hw-inline-form">
        <button type="button" className="rescue-hw-btn" onClick={runQuick} disabled={running}>
          {running ? tPath(dict, 'section.hardwareBaseline.runningLabel') : tPath(dict, 'section.hardwareBaseline.runQuickButton')}
        </button>
        <button type="button" className="rescue-hw-btn" onClick={runExtendedPreview} disabled={running}>
          {tPath(dict, 'section.hardwareBaseline.runExtendedPreviewButton')}
        </button>
      </div>

      {!hasRun && !result ? <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardwareBaseline.notRunYet')}</p> : null}

      {result ? (
        <>
          <div className="rescue-baseline-gate-summary" data-rescue-baseline-gate-status={result.gate.status}>
            <h4>{tPath(dict, 'section.hardwareBaseline.gateTitle')}</h4>
            <p>
              <SeverityBadge
                severity={result.gate.status === 'passed' ? 'green' : result.gate.status === 'blocked' ? 'red' : result.gate.status === 'review_required' ? 'yellow' : 'gray'}
                label={gateStatusLabel(dict, result.gate.status)}
              />
            </p>
            <ul className="rescue-migration-list">
              <PermissionRow label={tPath(dict, 'section.hardwareBaseline.permissionBackup')} allowed={result.gate.backup_allowed} dict={dict} />
              <PermissionRow label={tPath(dict, 'section.hardwareBaseline.permissionRestore')} allowed={result.gate.restore_allowed} dict={dict} />
              <PermissionRow label={tPath(dict, 'section.hardwareBaseline.permissionOsInstall')} allowed={result.gate.os_installation_allowed} dict={dict} />
              <PermissionRow label={tPath(dict, 'section.hardwareBaseline.permissionGuiMode')} allowed={result.gate.gui_mode_allowed} dict={dict} />
            </ul>
            {result.gate.action_impact && Object.keys(result.gate.action_impact).length > 0 ? (
              <div>
                <strong>Action impact</strong>
                <ul className="rescue-migration-list">
                  {Object.entries(result.gate.action_impact).map(([k, v]) => (
                    <li key={k}>
                      {k}: {v}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {result.gate.reasons.length > 0 ? (
              <div>
                <strong>{tPath(dict, 'section.hardwareBaseline.reasonsTitle')}</strong>
                <ul className="rescue-migration-list">
                  {result.gate.reasons.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {result.gate.warnings.length > 0 ? (
              <div>
                <strong>{tPath(dict, 'section.hardwareBaseline.warningsTitle')}</strong>
                <ul className="rescue-migration-list">
                  {result.gate.warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {result.gate.required_next_actions.length > 0 ? (
              <div>
                <strong>{tPath(dict, 'section.hardwareBaseline.nextActionsTitle')}</strong>
                <ul className="rescue-migration-list">
                  {result.gate.required_next_actions.map((a, idx) => (
                    <li key={idx}>{a}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>

          <div className="rescue-baseline-tile-grid">
            {orderedSubsystems.map((s) => (
              <SubsystemTile key={`${s.subsystem}-${s.device_id ?? ''}`} result={s} dict={dict} />
            ))}
          </div>
        </>
      ) : null}

      <p className="rescue-hw-hint" data-rescue-baseline-disclaimer="true">
        {tPath(dict, 'section.hardwareBaseline.disclaimerNeverGuaranteed')}
      </p>
    </section>
  );
};
