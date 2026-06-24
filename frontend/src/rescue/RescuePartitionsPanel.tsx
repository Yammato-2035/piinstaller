import React, { useEffect, useMemo, useState } from 'react';
import { fetchStorageDiscovery, type RescueStorageDevice } from './rescueBackupApi';
import { fetchLinuxMigrationAnalysis } from './linuxMigrationApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

function formatBytes(n?: number | string): string {
  if (n === undefined || n === null || n === '') return '—';
  const num = typeof n === 'string' ? Number(n) : n;
  if (!Number.isFinite(num) || num <= 0) return '—';
  return `${(num / 1024 ** 3).toFixed(2)} GiB`;
}

function roleLabel(dict: Record<string, unknown>, role: string): string {
  return tPath(dict, `section.partitions.roles.${role}`);
}

const GOALS = ['dualboot', 'replace_windows', 'data_disk', 'external_backup', 'view_only'] as const;

export const RescuePartitionsPanel: React.FC<{ locale: RescueLocale; compact?: boolean }> = ({
  locale,
  compact = false,
}) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [devices, setDevices] = useState<RescueStorageDevice[]>([]);
  const [goal, setGoal] = useState<(typeof GOALS)[number]>('view_only');
  const [expert, setExpert] = useState(false);
  const [dualHint, setDualHint] = useState<string>('');

  useEffect(() => {
    (async () => {
      try {
        const [disc, analysis] = await Promise.all([
          fetchStorageDiscovery(),
          fetchLinuxMigrationAnalysis().catch(() => null),
        ]);
        const all = disc.devices || [...(disc.source_candidates || []), ...(disc.target_candidates || [])];
        const byPath = new Map<string, RescueStorageDevice>();
        for (const d of all) {
          if (d?.path) byPath.set(String(d.path), d);
        }
        setDevices([...byPath.values()]);
        const dual = analysis?.dual_disk_recommendation;
        if (dual?.dual_disk && dual.system_disk?.model && dual.data_disk?.model) {
          setDualHint(
            `${dual.system_disk.model} → ${tPath(dict, 'section.partitions.recSystemDisk')}; ${dual.data_disk.model} → ${tPath(dict, 'section.partitions.recDataDisk')}`,
          );
        }
      } catch {
        setError(tPath(dict, 'section.partitions.error'));
      } finally {
        setLoading(false);
      }
    })();
  }, [dict]);

  const summary = useMemo(() => {
    const internal = devices.filter((d) => d.type === 'disk' && d.role !== 'rescue_usb_stick');
    const external = devices.filter((d) => d.role === 'external_backup_hdd' || d.role === 'backup_target');
    const ntfs = devices.filter((d) => String(d.fstype || '').toLowerCase().includes('ntfs'));
    const stick = devices.filter((d) => d.role === 'rescue_usb_stick');
    return { internal: internal.length, external: external.length, ntfs: ntfs.length, stick: stick.length };
  }, [devices]);

  const rows = useMemo(
    () =>
      [...devices].sort((a, b) => String(a.path).localeCompare(String(b.path))),
    [devices],
  );

  if (compact) {
    return null;
  }

  if (loading) {
    return (
      <div className="rescue-partitions-panel" data-rescue-partitions="true" role="status" aria-live="polite">
        <div className="rescue-partitions-spinner" aria-hidden />
        <p className="rescue-partitions-message">{tPath(dict, 'section.partitions.searching')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rescue-partitions-panel">
        <p className="rescue-partitions-error">{error}</p>
      </div>
    );
  }

  return (
    <div className="rescue-partitions-panel rescue-scroll-content" data-rescue-partitions="loaded">
      <p className="rescue-section-intro">{tPath(dict, 'section.partitions.helperIntro')}</p>
      <aside className="rescue-migration-panda" role="note">
        {tPath(dict, 'section.partitions.beginnerNote')}
      </aside>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.partitions.overviewTitle')}</h3>
        <ul className="rescue-migration-list">
          <li>{tPath(dict, 'section.partitions.internalDisks')}: {summary.internal}</li>
          <li>{tPath(dict, 'section.partitions.externalDisks')}: {summary.external}</li>
          <li>{tPath(dict, 'section.partitions.windowsParts')}: {summary.ntfs}</li>
          <li>{tPath(dict, 'section.partitions.rescueStick')}: {summary.stick}</li>
        </ul>
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.partitions.goalTitle')}</h3>
        <select value={goal} onChange={(e) => setGoal(e.target.value as (typeof GOALS)[number])}>
          {GOALS.map((g) => (
            <option key={g} value={g}>
              {tPath(dict, `section.partitions.goals.${g}`)}
            </option>
          ))}
        </select>
        {dualHint ? <p className="rescue-hint">{dualHint}</p> : null}
        <p className="rescue-hint">{tPath(dict, 'section.partitions.recSwap')}</p>
      </section>

      <label className="rescue-settings-row">
        <input type="checkbox" checked={expert} onChange={(e) => setExpert(e.target.checked)} />{' '}
        {tPath(dict, 'settings.expertMode')}
      </label>

      {expert ? (
        <div className="rescue-partitions-table-wrap">
          <table className="rescue-partitions-table">
            <thead>
              <tr>
                <th>{tPath(dict, 'section.partitions.colPath')}</th>
                <th>{tPath(dict, 'section.partitions.colFs')}</th>
                <th>{tPath(dict, 'section.partitions.colSize')}</th>
                <th>{tPath(dict, 'section.partitions.colRole')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => (
                <tr key={d.path}>
                  <td>{d.path}</td>
                  <td>{d.fstype || '—'}</td>
                  <td>{formatBytes(d.size_bytes ?? d.size)}</td>
                  <td>{roleLabel(dict, String(d.role || 'unknown'))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <p className="rescue-hint">{tPath(dict, 'section.partitions.writeBlocked')}</p>
    </div>
  );
};
