import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchRescueBootStatus, loadOfflineBootStatus } from './rescueApi';
import { RescueAnalyzePanel } from './RescueAnalyzePanel';
import { RescueBackupPanel } from './RescueBackupPanel';
import { RescueBootSplash } from './RescueBootSplash';
import { RescueBootStatusPanel } from './RescueBootStatus';
import { RescueDashboard } from './RescueDashboard';
import { RescueDataRescuePanel } from './RescueDataRescuePanel';
import { RescueEvidencePanel } from './RescueEvidencePanel';
import { RescueLinuxInstallPanel } from './RescueLinuxInstallPanel';
import { RescueLinuxMigrationPanel } from './RescueLinuxMigrationPanel';
import { RescueNetworkPanel } from './RescueNetworkPanel';
import { RescuePartitionsPanel } from './RescuePartitionsPanel';
import { RescueSectionPage } from './RescueSectionPage';
import { RescueSettingsPanel } from './RescueSettingsPanel';
import { RescueShellLayout } from './RescueShellLayout';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import type { RescueNavTileId } from './rescueNavTiles';
import { isRescueUiSafeWalk, safeWalkBlockedMessage } from './rescueSafeMode';
import {
  checkTerminalAvailable,
  exportRescueDiagnosticBundle,
  requestSystemReboot,
  requestSystemShutdown,
} from './rescueSystemApi';

type View = 'menu' | RescueNavTileId;

export const RescueApp: React.FC = () => {
  const safeWalk = isRescueUiSafeWalk();
  const [locale, setLocale] = useState<RescueLocale>('de');
  const [status, setStatus] = useState(loadOfflineBootStatus());
  const [view, setView] = useState<View>('menu');
  const [bootReady, setBootReady] = useState(false);
  const [apiReady, setApiReady] = useState(false);
  const [notice, setNotice] = useState('');

  const dict = useMemo(() => getRescueDict(locale), [locale]);

  const refreshStatus = useCallback(() => {
    void fetchRescueBootStatus()
      .then(setStatus)
      .catch(() => setStatus(loadOfflineBootStatus()));
  }, []);

  useEffect(() => {
    fetchRescueBootStatus()
      .then((s) => {
        setStatus(s);
        setApiReady(true);
      })
      .catch(() => {
        setStatus(loadOfflineBootStatus());
        setApiReady(true);
      });
  }, []);

  const systemMenuLabels = useMemo(
    () => ({
      menu: tPath(dict, 'systemMenu.title'),
      shell: tPath(dict, 'systemMenu.shell'),
      logs: tPath(dict, 'systemMenu.logs'),
      exportDiagnostic: tPath(dict, 'systemMenu.exportDiagnostic'),
      reboot: tPath(dict, 'footer.reboot'),
      shutdown: tPath(dict, 'footer.shutdown'),
      confirmReboot: tPath(dict, 'systemMenu.confirmReboot'),
      confirmShutdown: tPath(dict, 'systemMenu.confirmShutdown'),
      cancel: tPath(dict, 'systemMenu.cancel'),
      exportOk: tPath(dict, 'systemMenu.exportOk'),
      exportFail: tPath(dict, 'systemMenu.exportFail'),
      hotkey: 'F10',
    }),
    [dict],
  );

  const statusBarLabels = useMemo(
    () => ({
      offline: tPath(dict, 'statusBar.offline'),
      rescue: tPath(dict, 'statusBar.rescue'),
      deutsch: tPath(dict, 'language.de'),
      english: tPath(dict, 'language.en'),
    }),
    [dict],
  );

  const statusLabels = useMemo(
    () => ({
      ok: tPath(dict, 'statusLabels.ok'),
      review_required: tPath(dict, 'statusLabels.review_required'),
      failed: tPath(dict, 'statusLabels.failed'),
      not_configured: tPath(dict, 'statusLabels.not_configured'),
      disabled: tPath(dict, 'statusLabels.disabled'),
      skipped: tPath(dict, 'statusLabels.skipped'),
    }),
    [dict],
  );

  const statusPanelLabels = useMemo(
    () => ({
      medium: tPath(dict, 'status.medium'),
      network: tPath(dict, 'status.network'),
      telemetry: tPath(dict, 'status.telemetry'),
      optional: tPath(dict, 'status.optional'),
      off: tPath(dict, 'status.off'),
      on: tPath(dict, 'status.on'),
    }),
    [dict],
  );

  const goMenu = useCallback(() => setView('menu'), []);

  const onReboot = useCallback(async () => {
    if (safeWalk) {
      setNotice(safeWalkBlockedMessage('Neustart'));
      return;
    }
    const res = await requestSystemReboot();
    setNotice(res.ok ? systemMenuLabels.reboot : res.message || systemMenuLabels.exportFail);
  }, [safeWalk, systemMenuLabels]);

  const onShutdown = useCallback(async () => {
    if (safeWalk) {
      setNotice(safeWalkBlockedMessage('Shutdown'));
      return;
    }
    const res = await requestSystemShutdown();
    setNotice(
      res.ok ? tPath(dict, 'systemMenu.shutdownOk') : tPath(dict, 'systemMenu.shutdownHint'),
    );
  }, [dict, safeWalk]);

  const onOpenShell = useCallback(async () => {
    const term = await checkTerminalAvailable();
    setNotice(
      term.available
        ? `${systemMenuLabels.shell} (${term.terminal || 'terminal'})`
        : systemMenuLabels.shell,
    );
  }, [systemMenuLabels]);

  const onOpenLogs = useCallback(() => {
    setView('system');
  }, []);

  const onExportDiagnostic = useCallback(async () => {
    const res = await exportRescueDiagnosticBundle();
    setNotice(res.ok ? systemMenuLabels.exportOk : systemMenuLabels.exportFail);
  }, [systemMenuLabels]);

  const renderPanel = () => {
    switch (view) {
      case 'menu':
        return <RescueDashboard locale={locale} onSelectTile={(id) => setView(id)} />;
      case 'backup_create':
        return <RescueBackupPanel onBack={goMenu} />;
      case 'data_rescue':
        return (
          <RescueSectionPage
            titleKey="nav.dataRescue.title"
            subtitleKey="nav.dataRescue.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueDataRescuePanel locale={locale} />
          </RescueSectionPage>
        );
      case 'linux_migration':
        return (
          <RescueSectionPage
            titleKey="nav.linuxMigration.title"
            subtitleKey="nav.linuxMigration.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueLinuxMigrationPanel locale={locale} />
          </RescueSectionPage>
        );
      case 'system_analyze':
        return (
          <RescueSectionPage
            titleKey="nav.analyze.title"
            subtitleKey="nav.analyze.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueAnalyzePanel locale={locale} />
          </RescueSectionPage>
        );
      case 'network':
        return (
          <RescueSectionPage
            titleKey="nav.network.title"
            subtitleKey="nav.network.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueNetworkPanel locale={locale} />
          </RescueSectionPage>
        );
      case 'partitions':
        return (
          <RescueSectionPage
            titleKey="nav.partitions.title"
            subtitleKey="nav.partitions.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescuePartitionsPanel locale={locale} />
          </RescueSectionPage>
        );
      case 'linux_install':
        return (
          <RescueSectionPage
            titleKey="nav.linuxInstall.title"
            subtitleKey="nav.linuxInstall.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueLinuxInstallPanel locale={locale} />
          </RescueSectionPage>
        );
      case 'settings':
        return (
          <RescueSectionPage
            titleKey="nav.settings.title"
            subtitleKey="nav.settings.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueSettingsPanel
              locale={locale}
              status={status}
              onLocaleChange={setLocale}
              onStatusRefresh={refreshStatus}
            />
          </RescueSectionPage>
        );
      case 'system':
        return (
          <RescueSectionPage
            titleKey="nav.system.title"
            subtitleKey="nav.system.subtitle"
            locale={locale}
            onBack={goMenu}
          >
            <RescueBootStatusPanel
              status={status}
              labels={statusPanelLabels}
              statusLabels={statusLabels}
            />
            <RescueEvidencePanel locale={locale === 'en' ? 'en' : 'de'} />
          </RescueSectionPage>
        );
      default:
        return <RescueDashboard locale={locale} onSelectTile={(id) => setView(id)} />;
    }
  };

  if (!bootReady) {
    return (
      <RescueBootSplash
        status={status}
        ready={apiReady}
        onReady={() => setBootReady(true)}
      />
    );
  }

  return (
    <RescueShellLayout
      locale={locale}
      status={status}
      onLocaleChange={setLocale}
      onOpenLogs={onOpenLogs}
      onOpenShell={onOpenShell}
      onExportDiagnostic={onExportDiagnostic}
      onReboot={onReboot}
      onShutdown={onShutdown}
      languageLabels={{
        de: tPath(dict, 'language.de'),
        en: tPath(dict, 'language.en'),
      }}
      statusBarLabels={statusBarLabels}
      statusLabels={statusLabels}
      systemMenuLabels={systemMenuLabels}
      showToolbarBrand={view !== 'menu'}
    >
      {safeWalk ? (
        <p className="rescue-safe-walk-banner" role="status" data-rescue-safe-walk="true">
          Safe-Walk aktiv — destruktive Aktionen blockiert
        </p>
      ) : null}
      {notice ? (
        <p className="rescue-notice-banner" role="status">
          {notice}
        </p>
      ) : null}
      {renderPanel()}
    </RescueShellLayout>
  );
};
