import React, { useEffect, useMemo, useState } from 'react';
import { fetchRescueCapabilities } from './rescueBackupApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

/** Plan-only preview — full install requires migration plan + operator hand-off. */
export const RescueLinuxInstallPanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [executeAllowed, setExecuteAllowed] = useState(false);
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    fetchRescueCapabilities()
      .then((caps) => {
        setBooted(Boolean(caps.booted_from_rescue));
        setExecuteAllowed(Boolean(caps.endpoints?.linux_install));
      })
      .catch(() => undefined);
  }, []);

  return (
    <div className="rescue-linux-install-panel">
      <p className="rescue-section-intro">{tPath(dict, 'section.linuxInstall.intro')}</p>
      <aside className="rescue-migration-panda" role="note">
        <strong>{tPath(dict, 'guide.title')}:</strong> {tPath(dict, 'guide.step4')}
      </aside>
      <div className="rescue-plan-card">
        <h3>{tPath(dict, 'section.linuxInstall.planTitle')}</h3>
        <ul>
          <li>{tPath(dict, 'section.linuxInstall.stepAnalyze')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepBackup')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepPartition')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepInstall')}</li>
        </ul>
        <p className="rescue-linux-install-status">
          {executeAllowed
            ? tPath(dict, 'section.linuxInstall.statusReady')
            : tPath(dict, 'section.linuxInstall.statusBlocked')}
        </p>
        <p className="rescue-hint">{tPath(dict, 'section.linuxInstall.wipeHint')}</p>
        {booted ? (
          <p className="rescue-linux-install-hint">{tPath(dict, 'section.linuxInstall.rescueHint')}</p>
        ) : null}
      </div>
    </div>
  );
};
