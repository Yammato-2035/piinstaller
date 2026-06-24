import React, { useEffect, useMemo, useState } from 'react';
import { fetchStorageDiscovery } from './rescueBackupApi';
import { fetchLinuxMigrationAnalysis } from './linuxMigrationApi';
import { fetchRescueBootStatus } from './rescueApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { rescueTheme as theme } from './rescueTheme';

export const RescueAnalyzePanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [loading, setLoading] = useState(true);
  const [hw, setHw] = useState<Record<string, unknown> | null>(null);
  const [storage, setStorage] = useState<{
    diskCount: number;
    windowsFound: boolean;
    externalTargets: number;
    smartWarnings: number;
  }>({ diskCount: 0, windowsFound: false, externalTargets: 0, smartWarnings: 0 });
  const [boot, setBoot] = useState<Awaited<ReturnType<typeof fetchRescueBootStatus>> | null>(null);

  useEffect(() => {
    Promise.all([
      fetchLinuxMigrationAnalysis().catch(() => null),
      fetchStorageDiscovery().catch(() => null),
      fetchRescueBootStatus().catch(() => null),
    ])
      .then(([analysis, disc, bootStatus]) => {
        const identity = analysis?.linux_migration_system_identity || analysis?.hardware;
        if (identity) setHw(identity as Record<string, unknown>);
        const devices = disc?.devices || [];
        const disks = devices.filter((d) => d.type === 'disk');
        const ntfs = devices.some((d) => String(d.fstype || '').toLowerCase().includes('ntfs'));
        const ext = (disc?.target_candidates || []).length;
        const smartWarn = (analysis?.linux_migration_storage_assessment || []).filter(
          (d) => d.health_rating === 'warning' || d.health_rating === 'critical',
        ).length;
        setStorage({
          diskCount: disks.length,
          windowsFound: ntfs,
          externalTargets: ext,
          smartWarnings: smartWarn,
        });
        setBoot(bootStatus);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p>{tPath(dict, 'section.analyze.loading')}</p>;
  }

  const recs: string[] = [];
  if (storage.windowsFound) recs.push(tPath(dict, 'section.analyze.recWindowsFound'));
  recs.push(tPath(dict, 'section.analyze.recBackupFirst'));
  if (storage.externalTargets > 0) {
    recs.push(tPath(dict, 'section.analyze.recTargetOk'));
  } else {
    recs.push(tPath(dict, 'section.analyze.recTargetMissing'));
  }

  return (
    <div className="rescue-analyze-panel rescue-scroll-content" data-rescue-analyze="true">
      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.analyze.computerTitle')}</h3>
        <ul className="rescue-migration-list">
          <li>{tPath(dict, 'section.linuxMigration.manufacturer')}: {String(hw?.manufacturer || '—')}</li>
          <li>{tPath(dict, 'section.linuxMigration.model')}: {String(hw?.model || '—')}</li>
          <li>{tPath(dict, 'section.linuxMigration.cpu')}: {String(hw?.cpu || '—')}</li>
          <li>{tPath(dict, 'section.linuxMigration.ram')}: {hw?.ram_gb ? `${hw.ram_gb} GB` : '—'}</li>
          <li>{tPath(dict, 'section.linuxMigration.bootMode')}: {String(hw?.boot_mode || hw?.bios_uefi || '—')}</li>
          <li>{tPath(dict, 'section.linuxMigration.secureBoot')}: {String(hw?.secure_boot || '—')}</li>
        </ul>
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.analyze.statusTitle')}</h3>
        <ul className="rescue-migration-list">
          <li>GUI: {boot?.ui?.status || '—'}</li>
          <li>Backend: {boot?.medium?.status || '—'}</li>
          <li>{tPath(dict, 'status.telemetry')}: {boot?.telemetry?.status || '—'}</li>
          <li>{tPath(dict, 'status.network')}: {boot?.network?.status || '—'}</li>
          <li>SETUP_LOGS: {boot?.medium?.evidence_ok ? '✓' : '—'}</li>
        </ul>
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.analyze.storageTitle')}</h3>
        <ul className="rescue-migration-list">
          <li>{tPath(dict, 'section.analyze.diskCount')}: {storage.diskCount}</li>
          <li>{tPath(dict, 'section.analyze.windowsFound')}: {storage.windowsFound ? '✓' : '—'}</li>
          <li>{tPath(dict, 'section.analyze.externalTargets')}: {storage.externalTargets}</li>
          <li>{tPath(dict, 'section.analyze.smartWarnings')}: {storage.smartWarnings}</li>
        </ul>
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.analyze.recommendTitle')}</h3>
        <ul className="rescue-migration-list">
          {recs.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      </section>
    </div>
  );
};
