import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import {
  fetchLinuxMigrationAnalysis,
  postLinuxMigrationInstallationPlan,
  postPartitionPreview,
  type LinuxMigrationAnalysis,
  type LinuxMigrationInstallationPlan,
  type PartitionPreview,
} from './linuxMigrationApi';
import { rescueTheme as theme } from './rescueTheme';

type Step =
  | 'loading'
  | 'identity'
  | 'disks'
  | 'profile'
  | 'distro'
  | 'partitions'
  | 'readiness'
  | 'variants'
  | 'backup_warning'
  | 'confirm'
  | 'plan';

const CONFIRM_PHRASE = 'ICH MÖCHTE DIESEN COMPUTER LÖSCHEN';

const PROFILE_IDS = [
  'office',
  'standard_pc',
  'gaming',
  'developer',
  'home_server',
  'nas',
  'custom',
] as const;

const riskColor = (level: string) => {
  if (level === 'green') return theme.statusOk;
  if (level === 'red') return theme.statusErr;
  return theme.statusWarn;
};

const healthColor = (level: string) => {
  if (level === 'excellent' || level === 'good') return theme.statusOk;
  if (level === 'critical') return theme.statusErr;
  return theme.statusWarn;
};

export const RescueLinuxMigrationPanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [step, setStep] = useState<Step>('loading');
  const [analysis, setAnalysis] = useState<LinuxMigrationAnalysis | null>(null);
  const [error, setError] = useState('');
  const [identityConfirmed, setIdentityConfirmed] = useState(false);
  const [profileId, setProfileId] = useState('standard_pc');
  const [variantId, setVariantId] = useState('');
  const [distroId, setDistroId] = useState('linux_mint');
  const [confirmDataLoss, setConfirmDataLoss] = useState(false);
  const [confirmPhrase, setConfirmPhrase] = useState('');
  const [plan, setPlan] = useState<LinuxMigrationInstallationPlan | null>(null);
  const [partitionPreview, setPartitionPreview] = useState<PartitionPreview | null>(null);
  const [planLoading, setPlanLoading] = useState(false);

  useEffect(() => {
    fetchLinuxMigrationAnalysis()
      .then((data) => {
        setAnalysis(data);
        setStep('identity');
      })
      .catch(() => {
        setError(tPath(dict, 'section.linuxMigration.error'));
        setStep('identity');
      });
  }, [dict]);

  const selectedVariant = analysis?.migration_variants.find((v) => v.id === variantId);
  const isDestructive = selectedVariant?.data_loss_possible ?? false;

  const generatePlan = useCallback(async () => {
    if (!analysis || !variantId || !identityConfirmed) return;
    setPlanLoading(true);
    setError('');
    try {
      const result = await postLinuxMigrationInstallationPlan({
        identity_confirmed: identityConfirmed,
        migration_profile: profileId,
        distro_id: distroId,
        variant_id: variantId,
        confirm_data_loss_understood: confirmDataLoss,
        confirm_phrase: confirmPhrase,
        analysis,
      });
      setPlan(result);
      setStep('plan');
    } catch {
      setError(tPath(dict, 'section.linuxMigration.planError'));
    } finally {
      setPlanLoading(false);
    }
  }, [analysis, variantId, identityConfirmed, profileId, distroId, confirmDataLoss, confirmPhrase, dict]);

  const downloadExport = (format: 'json' | 'markdown') => {
    if (!plan) return;
    const content = format === 'json' ? JSON.stringify(plan.exports.json, null, 2) : plan.exports.markdown;
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `linux-migration-plan.${format === 'json' ? 'json' : 'md'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const pandaHint = (key: string) => (
    <aside className="rescue-migration-panda" role="note">
      <span aria-hidden>🐼</span> {tPath(dict, key)}
    </aside>
  );

  const planOnlyBanner = (
    <div className="rescue-migration-plan-only-banner" role="status">
      {tPath(dict, 'section.linuxMigration.planOnlyBanner')}
    </div>
  );

  if (step === 'loading') {
    return (
      <div className="rescue-linux-migration-panel">
        {planOnlyBanner}
        <p className="rescue-section-intro">{tPath(dict, 'section.linuxMigration.loading')}</p>
        {pandaHint('migration.panda.welcome')}
      </div>
    );
  }

  const ident = analysis?.linux_migration_system_identity;
  const storage = analysis?.linux_migration_storage_assessment ?? [];
  const readiness = analysis?.migration_readiness;

  return (
    <div className="rescue-linux-migration-panel rescue-scroll-content">
      {planOnlyBanner}
      <p className="rescue-section-intro">{tPath(dict, 'section.linuxMigration.intro')}</p>
      {error ? <p className="rescue-network-error">{error}</p> : null}

      {step === 'identity' && ident ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.identityTitle')}</h3>
          {pandaHint('migration.panda.identity')}
          <div className="rescue-plan-card">
            <p>
              <strong>{tPath(dict, 'section.linuxMigration.manufacturer')}:</strong> {ident.manufacturer}
            </p>
            <p>
              <strong>{tPath(dict, 'section.linuxMigration.model')}:</strong> {ident.model}
            </p>
            <p>
              <strong>{tPath(dict, 'section.linuxMigration.cpu')}:</strong> {ident.cpu}
            </p>
            <p>
              <strong>{tPath(dict, 'section.linuxMigration.ram')}:</strong> {ident.ram_gb} GB
            </p>
            {ident.mainboard ? (
              <p>
                <strong>{tPath(dict, 'section.linuxMigration.mainboard')}:</strong> {ident.mainboard}
              </p>
            ) : null}
            <p>
              <strong>{tPath(dict, 'section.linuxMigration.bootMode')}:</strong> {ident.bios_uefi ?? ident.boot_mode}
            </p>
          </div>
          <label className="rescue-migration-check">
            <input
              type="checkbox"
              checked={identityConfirmed}
              onChange={(e) => setIdentityConfirmed(e.target.checked)}
            />
            {tPath(dict, 'section.linuxMigration.identityConfirm')}
          </label>
          <button
            type="button"
            className="rescue-migration-btn"
            disabled={!identityConfirmed}
            onClick={() => setStep('disks')}
          >
            {tPath(dict, 'section.linuxMigration.nextDisks')}
          </button>
        </section>
      ) : null}

      {step === 'disks' && analysis ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.disksTitle')}</h3>
          {pandaHint('migration.panda.disks')}
          {storage.map((disk) => (
            <div key={disk.path} className="rescue-plan-card rescue-migration-disk-card">
              <h4>{disk.model}</h4>
              <p>{disk.size_human} · {disk.media_type.toUpperCase()}</p>
              <p className="rescue-migration-health" style={{ color: healthColor(disk.health_rating) }}>
                {tPath(dict, `section.linuxMigration.health.${disk.health_rating}`)} · SMART: {disk.smart_status}
              </p>
              <p>{disk.recommendation}</p>
            </div>
          ))}
          <button type="button" className="rescue-migration-btn" onClick={() => setStep('profile')}>
            {tPath(dict, 'section.linuxMigration.nextProfile')}
          </button>
        </section>
      ) : null}

      {step === 'profile' ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.profileTitle')}</h3>
          {pandaHint('migration.panda.profile')}
          <div className="rescue-migration-variant-grid">
            {PROFILE_IDS.map((id) => (
              <button
                key={id}
                type="button"
                className={`rescue-migration-variant-btn${profileId === id ? ' rescue-migration-variant-active' : ''}`}
                onClick={() => setProfileId(id)}
              >
                <strong>{tPath(dict, `section.linuxMigration.profile.${id}`)}</strong>
              </button>
            ))}
          </div>
          <button type="button" className="rescue-migration-btn" onClick={() => setStep('distro')}>
            {tPath(dict, 'section.linuxMigration.nextDistro')}
          </button>
        </section>
      ) : null}

      {step === 'distro' && analysis ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.distrosTitle')}</h3>
          {pandaHint('migration.panda.distros')}
          {(['beginner', 'advanced', 'server'] as const).map((group) => (
            <div key={group} className="rescue-migration-distro-group">
              <h4>{tPath(dict, `section.linuxMigration.group.${group}`)}</h4>
              {(analysis.linux_recommendations[group] ?? []).map((d) => (
                <label key={d.id} className="rescue-migration-distro-option">
                  <input
                    type="radio"
                    name="distro"
                    value={d.id}
                    checked={distroId === d.id}
                    onChange={() => setDistroId(d.id)}
                  />
                  <span>
                    <strong>{d.name} {d.version_hint}</strong>
                    {d.audience ? <span className="rescue-migration-meta"> ({d.audience})</span> : null}
                    {d.recommended ? (
                      <span className="rescue-migration-badge" style={{ color: theme.statusOk }}>
                        {' '}{tPath(dict, 'section.linuxMigration.recommended')}
                      </span>
                    ) : null}
                    <br />
                    {tPath(dict, d.description_key)}
                  </span>
                </label>
              ))}
            </div>
          ))}
          <button
            type="button"
            className="rescue-migration-btn"
            onClick={() => {
              if (!analysis) {
                setStep('partitions');
                return;
              }
              postPartitionPreview({ migration_profile: profileId, distro_id: distroId, analysis })
                .then(setPartitionPreview)
                .catch(() => setPartitionPreview(analysis.partition_plan_preview))
                .finally(() => setStep('partitions'));
            }}
          >
            {tPath(dict, 'section.linuxMigration.nextPartitions')}
          </button>
        </section>
      ) : null}

      {step === 'partitions' && analysis ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.partitionsTitle')}</h3>
          {pandaHint('migration.panda.partitions')}
          {analysis.dual_disk_recommendation?.dual_disk ? (
            <div className="rescue-plan-card">
              <p className="rescue-migration-meta">{tPath(dict, 'section.linuxMigration.dualDiskIntro')}</p>
              <p>
                <strong>{tPath(dict, 'section.linuxMigration.dualDiskSystem')}:</strong>{' '}
                {analysis.dual_disk_recommendation.system_disk?.model}{' '}
                ({analysis.dual_disk_recommendation.system_disk?.speed_label || '—'})
              </p>
              <p className="rescue-hint">{analysis.dual_disk_recommendation.system_disk?.recommendation}</p>
              <p>
                <strong>{tPath(dict, 'section.linuxMigration.dualDiskData')}:</strong>{' '}
                {analysis.dual_disk_recommendation.data_disk?.model}{' '}
                ({analysis.dual_disk_recommendation.data_disk?.speed_label || '—'})
              </p>
              <p className="rescue-hint">{analysis.dual_disk_recommendation.data_disk?.recommendation}</p>
            </div>
          ) : (
            <p className="rescue-migration-meta">{tPath(dict, 'section.linuxMigration.dualDiskSingle')}</p>
          )}
          <div className="rescue-plan-card">
            <p className="rescue-migration-meta">{tPath(dict, 'section.linuxMigration.partitionsPreviewOnly')}</p>
            {((partitionPreview ?? analysis.partition_plan_preview)?.disk_layouts ?? []).length > 0 ? (
              ((partitionPreview ?? analysis.partition_plan_preview)?.disk_layouts ?? []).map((layout) => (
                <div key={String(layout.disk_path)}>
                  <strong>{layout.disk_label}</strong>
                  <ul>
                    {(layout.partitions ?? []).map((p) => (
                      <li key={`${layout.disk_path}-${p.role}`}>
                        {p.role}: {p.size} — {p.notes}
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            ) : (
              <ul>
                {((partitionPreview ?? analysis.partition_plan_preview)?.partitions ?? []).map((p) => (
                  <li key={p.role}>{p.role}: {p.size}</li>
                ))}
              </ul>
            )}
          </div>
          <button type="button" className="rescue-migration-btn" onClick={() => setStep('readiness')}>
            {tPath(dict, 'section.linuxMigration.nextReadiness')}
          </button>
        </section>
      ) : null}

      {step === 'readiness' && readiness ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.readinessTitle')}</h3>
          {pandaHint('migration.panda.readiness')}
          <p className="rescue-migration-overall" style={{ color: riskColor(readiness.overall) }}>
            {tPath(dict, 'section.linuxMigration.readinessOverall')}: {readiness.overall.toUpperCase()}
          </p>
          <ul className="rescue-migration-list">
            {Object.entries(readiness.areas).map(([key, area]) => (
              <li key={key} style={{ color: riskColor(area.status) }}>
                {area.label}: {area.ok ? '✓' : '○'} ({area.status})
              </li>
            ))}
          </ul>
          <button type="button" className="rescue-migration-btn" onClick={() => setStep('variants')}>
            {tPath(dict, 'section.linuxMigration.nextVariants')}
          </button>
        </section>
      ) : null}

      {step === 'variants' && analysis ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.variantsTitle')}</h3>
          {pandaHint('migration.panda.variants')}
          <div className="rescue-migration-variant-grid">
            {analysis.migration_variants.map((v) => (
              <button
                key={v.id}
                type="button"
                className={`rescue-migration-variant-btn${variantId === v.id ? ' rescue-migration-variant-active' : ''}`}
                style={{ borderColor: riskColor(v.risk_level) }}
                onClick={() => setVariantId(v.id)}
              >
                <span className="rescue-migration-risk" style={{ color: riskColor(v.risk_level) }}>
                  {tPath(dict, v.title_key)}
                </span>
              </button>
            ))}
          </div>
          <button
            type="button"
            className="rescue-migration-btn"
            disabled={!variantId}
            onClick={() => setStep(isDestructive ? 'backup_warning' : 'confirm')}
          >
            {tPath(dict, 'section.linuxMigration.nextConfirm')}
          </button>
        </section>
      ) : null}

      {step === 'backup_warning' ? (
        <section className="rescue-migration-step">
          <div className="rescue-migration-warning" style={{ borderColor: theme.statusErr }}>
            <h3>{tPath(dict, 'section.linuxMigration.warningTitle')}</h3>
            <p>{tPath(dict, 'section.linuxMigration.warningBody')}</p>
          </div>
          <button type="button" className="rescue-migration-btn" onClick={() => setStep('confirm')}>
            {tPath(dict, 'section.linuxMigration.nextConfirm')}
          </button>
        </section>
      ) : null}

      {step === 'confirm' ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.confirmTitle')}</h3>
          {isDestructive ? (
            <>
              <label className="rescue-migration-check">
                <input type="checkbox" checked={confirmDataLoss} onChange={(e) => setConfirmDataLoss(e.target.checked)} />
                {tPath(dict, 'section.linuxMigration.confirmDataLoss')}
              </label>
              <label className="rescue-migration-phrase-label">
                {tPath(dict, 'section.linuxMigration.confirmPhrasePrompt')}
                <input
                  type="text"
                  className="rescue-network-password"
                  value={confirmPhrase}
                  onChange={(e) => setConfirmPhrase(e.target.value)}
                  placeholder={CONFIRM_PHRASE}
                  spellCheck={false}
                />
              </label>
            </>
          ) : (
            <p>{tPath(dict, 'section.linuxMigration.confirmSafe')}</p>
          )}
          <button
            type="button"
            className="rescue-migration-btn"
            disabled={
              planLoading ||
              !identityConfirmed ||
              (isDestructive && (!confirmDataLoss || confirmPhrase !== CONFIRM_PHRASE))
            }
            onClick={() => void generatePlan()}
          >
            {planLoading
              ? tPath(dict, 'section.linuxMigration.planGenerating')
              : tPath(dict, 'section.linuxMigration.generatePlan')}
          </button>
        </section>
      ) : null}

      {step === 'plan' && plan ? (
        <section className="rescue-migration-step">
          <h3>{tPath(dict, 'section.linuxMigration.planTitle')}</h3>
          {pandaHint('migration.panda.planReady')}
          <div className="rescue-plan-card">
            <p><strong>{tPath(dict, 'section.linuxMigration.readinessOverall')}:</strong>{' '}
              <span style={{ color: riskColor(plan.migration_readiness.overall) }}>{plan.migration_readiness.overall}</span>
            </p>
            <p><strong>{tPath(dict, 'section.linuxMigration.profileTitle')}:</strong> {plan.migration_profile}</p>
            <p><strong>{tPath(dict, 'section.linuxMigration.planTarget')}:</strong>{' '}
              {plan.linux_recommendation.name} {plan.linux_recommendation.version_hint}
            </p>
            <h4>{tPath(dict, 'section.linuxMigration.planPartitions')}</h4>
            <ul>
              {plan.partition_plan_preview.partitions.map((p) => (
                <li key={p.role}>{p.role}: {p.size}</li>
              ))}
            </ul>
            <h4>{tPath(dict, 'section.linuxMigration.risksTitle')}</h4>
            <ul>
              {plan.risks.map((r) => (
                <li key={r.code}>{r.message}</li>
              ))}
            </ul>
            <p className="rescue-migration-status" style={{ color: theme.statusWarn }}>
              {tPath(dict, 'section.linuxMigration.planStatus')}: {plan.plan_status} · write_allowed={String(plan.write_allowed)}
            </p>
          </div>
          <div className="rescue-migration-export-row">
            <button type="button" className="rescue-migration-btn" onClick={() => downloadExport('json')}>
              {tPath(dict, 'section.linuxMigration.exportJson')}
            </button>
            <button type="button" className="rescue-migration-btn" onClick={() => downloadExport('markdown')}>
              {tPath(dict, 'section.linuxMigration.exportMarkdown')}
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
};
