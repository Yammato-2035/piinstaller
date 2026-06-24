import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { isRescueUiSafeWalk } from './rescueSafeMode';
import {
  DATA_RESCUE_FOLDER_IDS,
  fetchDataRescueDiscovery,
  fetchDataRescueJob,
  fetchDataRescueVerify,
  fetchStorageDiscoveryForRescue,
  postDataRescueEstimate,
  postDataRescueExecute,
  postDataRescuePlan,
  type DataRescueDiscovery,
  type DataRescueExecuteResult,
  type DataRescuePlan,
  type DataRescueProfile,
  type RescueStorageDevice,
} from './dataRescueApi';
import { rescueTheme as theme } from './rescueTheme';

type Step = 'loading' | 'user' | 'folders' | 'target' | 'plan' | 'running' | 'done';

const defaultFolders = (): Record<string, boolean> => ({
  documents: true,
  pictures: true,
  videos: false,
  music: false,
  downloads: true,
  desktop: true,
  onedrive: false,
});

export const RescueDataRescuePanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const safeWalk = isRescueUiSafeWalk();
  const [step, setStep] = useState<Step>('loading');
  const [discovery, setDiscovery] = useState<DataRescueDiscovery | null>(null);
  const [targets, setTargets] = useState<RescueStorageDevice[]>([]);
  const [profileHash, setProfileHash] = useState('');
  const [folderSel, setFolderSel] = useState(defaultFolders);
  const [targetPath, setTargetPath] = useState('');
  const [estimateHuman, setEstimateHuman] = useState('');
  const [plan, setPlan] = useState<DataRescuePlan | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [executeResult, setExecuteResult] = useState<DataRescueExecuteResult | null>(null);
  const [verifyOk, setVerifyOk] = useState<boolean | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([fetchDataRescueDiscovery(locale), fetchStorageDiscoveryForRescue()])
      .then(([disc, storage]) => {
        setDiscovery(disc);
        setTargets(storage.target_candidates || []);
        const first = disc.sources?.[0]?.profiles?.[0];
        if (first) setProfileHash(first.profile_hash);
        setStep('user');
      })
      .catch(() => {
        setError(tPath(dict, 'section.dataRescue.error'));
        setStep('user');
      });
  }, [dict, locale]);

  const profiles: DataRescueProfile[] = useMemo(() => {
    const out: DataRescueProfile[] = [];
    for (const src of discovery?.sources || []) {
      out.push(...(src.profiles || []));
    }
    return out;
  }, [discovery]);

  const selectedProfile = profiles.find((p) => p.profile_hash === profileHash);
  const hasProfiles = profiles.length > 0;
  const mountHint = discovery?.windows_mount;
  const selectedFolderIds = DATA_RESCUE_FOLDER_IDS.filter((id) => folderSel[id]);
  const selectedTarget = targets.find((t) => t.path === targetPath);

  const teacherHint = (key: string) => {
    const hint = discovery?.teacher_mode?.hints?.[key];
    if (!hint) return null;
    return (
      <aside className="rescue-migration-panda" role="note">
        <span aria-hidden>📁</span> <strong>{hint.title}:</strong> {hint.body}
      </aside>
    );
  };

  const runEstimate = useCallback(async () => {
    if (!profileHash || selectedFolderIds.length === 0) return;
    setBusy(true);
    setError('');
    try {
      const est = await postDataRescueEstimate({ profile_hash: profileHash, folder_ids: [...selectedFolderIds] });
      setEstimateHuman(est.estimation?.total_human || '');
      setStep('target');
    } catch {
      setError(tPath(dict, 'section.dataRescue.estimateError'));
    } finally {
      setBusy(false);
    }
  }, [profileHash, selectedFolderIds, dict]);

  const createPlan = useCallback(async () => {
    const tgt = selectedTarget;
    if (!profileHash || !tgt || selectedFolderIds.length === 0) {
      setError(tPath(dict, 'section.dataRescue.targetRequired'));
      return;
    }
    setBusy(true);
    setError('');
    try {
      const result = await postDataRescuePlan({
        profile_hash: profileHash,
        folder_ids: [...selectedFolderIds],
        target_device: tgt.path,
        target_mount: tgt.mountpoint || '',
        target_mode: tgt.tran === 'usb' ? 'usb_hdd' : 'usb_ssd',
        locale,
        operator_confirm: true,
      });
      setPlan(result);
      setStep('plan');
    } catch {
      setError(tPath(dict, 'section.dataRescue.planError'));
    } finally {
      setBusy(false);
    }
  }, [profileHash, selectedTarget, selectedFolderIds, locale, dict]);

  const startExecute = useCallback(async () => {
    if (!plan?.plan_id) return;
    setBusy(true);
    setError('');
    setStep('running');
    setConfirmOpen(false);
    try {
      const result = await postDataRescueExecute({ plan_id: plan.plan_id, operator_confirm: true });
      setExecuteResult(result);
      if (result.job_id) {
        await fetchDataRescueJob(result.job_id);
        const verify = await fetchDataRescueVerify(result.job_id);
        setVerifyOk(Boolean(verify.VERIFY_SUCCESS));
      }
      setStep('done');
    } catch {
      setError(tPath(dict, 'section.dataRescue.executeError'));
      setStep('plan');
    } finally {
      setBusy(false);
    }
  }, [plan, dict]);

  const folderLabel = (id: string) => tPath(dict, `section.dataRescue.folders.${id}`);
  const folderSizeHint = (id: string) => {
    const stats = selectedProfile?.folders?.[id];
    if (!stats?.size_bytes) return '';
    const gb = stats.size_bytes / (1024 ** 3);
    return gb >= 1 ? ` (~${gb.toFixed(0)} GB)` : '';
  };

  return (
    <div className="rescue-data-rescue rescue-scroll-content" data-rescue-data-rescue="true">
      <p className="rescue-section-intro">{tPath(dict, 'section.dataRescue.intro')}</p>
      {teacherHint('overview')}

      {error ? <p style={{ color: theme.statusErr }}>{error}</p> : null}
      {step === 'loading' ? <p>{tPath(dict, 'section.dataRescue.loading')}</p> : null}

      {!hasProfiles && step !== 'loading' ? (
        <div className="rescue-migration-warning" role="alert">
          <p>
            <strong>{tPath(dict, 'section.dataRescue.noProfiles')}</strong>
          </p>
          {discovery?.diagnostics?.situation ? (
            <p>{tPath(dict, `section.dataRescue.diagnostics.${discovery.diagnostics.situation}`)}</p>
          ) : (
            <p>{tPath(dict, 'section.dataRescue.noWindowsHint')}</p>
          )}
          {discovery?.diagnostics?.ntfs_partition_count ? (
            <p>
              {tPath(dict, 'section.dataRescue.ntfsFound')}: {discovery.diagnostics.ntfs_partition_count}
            </p>
          ) : null}
          {mountHint?.status === 'error' ? (
            <p>
              {tPath(dict, 'section.dataRescue.mountFailed')}{' '}
              {String(mountHint.detail || mountHint.code || '')}
            </p>
          ) : null}
          {mountHint?.users_path_missing ? (
            <p>{tPath(dict, 'section.dataRescue.usersPathMissing')}</p>
          ) : null}
          {mountHint?.code === 'no_ntfs_candidate' ? (
            <p>{tPath(dict, 'section.dataRescue.noNtfs')}</p>
          ) : null}
        </div>
      ) : null}

      {hasProfiles && step !== 'loading' && !['running', 'done'].includes(step) && step !== 'plan' ? (
        <>
          <h3>{tPath(dict, 'section.dataRescue.stepUser')}</h3>
          <select value={profileHash} onChange={(e) => setProfileHash(e.target.value)} disabled={!hasProfiles}>
            {profiles.map((p) => (
              <option key={p.profile_hash} value={p.profile_hash}>
                {p.display_label}
              </option>
            ))}
          </select>
          <h3 style={{ marginTop: 24 }}>{tPath(dict, 'section.dataRescue.stepFolders')}</h3>
          {teacherHint('documents')}
          {teacherHint('downloads')}
          {DATA_RESCUE_FOLDER_IDS.map((id) => (
            <label key={id} style={{ display: 'block', marginBottom: 8 }}>
              <input
                type="checkbox"
                checked={folderSel[id]}
                onChange={(e) => setFolderSel((s) => ({ ...s, [id]: e.target.checked }))}
              />{' '}
              {folderLabel(id)}
              {folderSizeHint(id)}
            </label>
          ))}
          {(step === 'target' || step === 'folders') && (
            <>
              <h3 style={{ marginTop: 24 }}>{tPath(dict, 'section.dataRescue.stepTarget')}</h3>
              <select value={targetPath} onChange={(e) => setTargetPath(e.target.value)}>
                <option value="">{tPath(dict, 'section.dataRescue.chooseTarget')}</option>
                {targets.map((t) => (
                  <option key={t.path} value={t.path}>
                    {t.label || t.path} {t.mountpoint ? `(${t.mountpoint})` : ''}
                  </option>
                ))}
              </select>
              {estimateHuman ? (
                <p>
                  {tPath(dict, 'section.dataRescue.selectedSize')}: <strong>{estimateHuman}</strong>
                </p>
              ) : null}
            </>
          )}
          <div style={{ marginTop: 24 }}>
            {(step === 'user' || step === 'folders') && (
              <button
                type="button"
                className="rescue-migration-btn"
                disabled={busy || !profileHash || selectedFolderIds.length === 0}
                onClick={runEstimate}
              >
                {tPath(dict, 'section.dataRescue.nextTarget')}
              </button>
            )}
            {step === 'target' && (
              <button type="button" className="rescue-migration-btn" disabled={busy || !targetPath} onClick={createPlan}>
                {tPath(dict, 'section.dataRescue.createPlan')}
              </button>
            )}
          </div>
        </>
      ) : null}

      {step === 'plan' && plan ? (
        <div className="rescue-data-rescue-plan">
          <h3>{tPath(dict, 'section.dataRescue.planTitle')}</h3>
          <p>{plan.recommendation}</p>
          <p>
            {tPath(dict, 'section.dataRescue.targetFree')}: {plan.target_validation?.free_human || '—'}
          </p>
          {confirmOpen ? (
            <div className="rescue-migration-warning" style={{ borderColor: theme.statusWarn }}>
              <p>{tPath(dict, 'section.dataRescue.confirmIntro')}</p>
              <ul>
                <li>{tPath(dict, 'section.dataRescue.confirmSource')}: {plan.source?.display_label}</li>
                <li>{tPath(dict, 'section.dataRescue.confirmTarget')}: {plan.target?.mount}</li>
                <li>{tPath(dict, 'section.dataRescue.confirmSize')}: {plan.estimation?.total_human}</li>
                <li>{tPath(dict, 'section.dataRescue.confirmFree')}: {plan.target?.free_human || plan.target_validation?.free_human}</li>
              </ul>
              <p>{tPath(dict, 'section.dataRescue.confirmNoDelete')}</p>
              <button type="button" className="rescue-migration-btn" disabled={busy || safeWalk} onClick={startExecute}>
                {tPath(dict, 'section.dataRescue.confirmStart')}
              </button>
              <button type="button" className="rescue-migration-btn" style={{ marginLeft: 12 }} onClick={() => setConfirmOpen(false)}>
                {tPath(dict, 'section.dataRescue.confirmCancel')}
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="rescue-migration-btn"
              disabled={!plan.execute_allowed || busy || safeWalk}
              onClick={() => setConfirmOpen(true)}
            >
              {tPath(dict, 'section.dataRescue.startCopyNow')}
            </button>
          )}
        </div>
      ) : null}

      {step === 'running' ? <p>{tPath(dict, 'section.dataRescue.running')}</p> : null}

      {step === 'done' && executeResult ? (
        <div>
          <h3>{tPath(dict, 'section.dataRescue.resultTitle')}</h3>
          <p>
            {tPath(dict, 'section.dataRescue.resultStatus')}: <strong>{executeResult.status}</strong>
          </p>
          <p>
            {tPath(dict, 'section.dataRescue.filesCopied')}: {executeResult.files_copied ?? 0}
          </p>
          <p>{tPath(dict, 'section.dataRescue.targetPath')}: {executeResult.target_path}</p>
          <p>
            {tPath(dict, 'section.dataRescue.verifyStatus')}:{' '}
            <strong style={{ color: verifyOk ? theme.statusOk : theme.statusErr }}>
              {verifyOk ? tPath(dict, 'section.dataRescue.verifyOk') : tPath(dict, 'section.dataRescue.verifyFail')}
            </strong>
          </p>
        </div>
      ) : null}
    </div>
  );
};
