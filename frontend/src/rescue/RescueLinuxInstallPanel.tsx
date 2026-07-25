import React, { useEffect, useMemo, useState } from 'react'
import { fetchRescueCapabilities } from './rescueBackupApi'
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale'

type DistroProfile = {
  id: string
  label_de?: string
  label_en?: string
  support_level?: string
}

/** Multi-distro plan preview — execute only after approval or backup gate. */
export const RescueLinuxInstallPanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale])
  const [executeAllowed, setExecuteAllowed] = useState(false)
  const [booted, setBooted] = useState(false)
  const [profiles, setProfiles] = useState<DistroProfile[]>([])

  useEffect(() => {
    fetchRescueCapabilities()
      .then((caps) => {
        setBooted(Boolean(caps.booted_from_rescue))
        setExecuteAllowed(Boolean(caps.endpoints?.linux_install))
      })
      .catch(() => undefined)
    fetch('/api/rescue/linux-install/distro-profiles')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.profiles) setProfiles(data.profiles as DistroProfile[])
      })
      .catch(() => undefined)
  }, [])

  const de = locale === 'de'

  return (
    <div className="rescue-linux-install-panel" data-testid="rescue-linux-install-panel">
      <p className="rescue-section-intro">{tPath(dict, 'section.linuxInstall.intro')}</p>
      <aside className="rescue-migration-panda" role="note">
        <strong>{tPath(dict, 'guide.title')}:</strong> {tPath(dict, 'guide.step4')}
      </aside>

      <div className="rescue-plan-card">
        <h3>{tPath(dict, 'section.linuxInstall.diagnosisTitle')}</h3>
        <ul>
          <li>{tPath(dict, 'section.linuxInstall.distroMint')}</li>
          <li>{tPath(dict, 'section.linuxInstall.distroUbuntuLts')}</li>
          <li>{tPath(dict, 'section.linuxInstall.distroUbuntuServer')}</li>
          <li>{tPath(dict, 'section.linuxInstall.distroDebian')}</li>
        </ul>
        {profiles.length > 0 ? (
          <p className="rescue-hint" data-testid="distro-profile-count">
            {de ? `Profile geladen: ${profiles.length}` : `Profiles loaded: ${profiles.length}`}
          </p>
        ) : null}
      </div>

      <div className="rescue-plan-card">
        <h3>{tPath(dict, 'section.linuxInstall.planTitle')}</h3>
        <ul>
          <li>{tPath(dict, 'section.linuxInstall.stepAnalyze')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepBackup')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepPartition')}</li>
          <li>{tPath(dict, 'section.linuxInstall.stepInstall')}</li>
          <li>{tPath(dict, 'section.linuxInstall.setuphelferBootstrap')}</li>
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
  )
}
