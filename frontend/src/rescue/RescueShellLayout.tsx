import React from 'react';
import { RescueLanguageSelect } from './RescueLanguageSelect';
import { RESCUE_LOGO } from './rescueAssets';
import type { RescueLocale } from './rescueLocale';
import { RescuePowerButton } from './RescuePowerButton';
import { RescueStatusBar } from './RescueStatusBar';
import { RescueSystemMenu } from './RescueSystemMenu';
import type { RescueBootStatus } from './rescueTypes';
import { rescueTheme as t } from './rescueTheme';

declare const __APP_VERSION__: string;

/** RS-P3L — document-flow shell (no absolute overlay toolbar). */
export const RescueShellLayout: React.FC<{
  locale: RescueLocale;
  status: RescueBootStatus;
  onLocaleChange: (locale: RescueLocale) => void;
  onOpenLogs: () => void;
  onOpenShell: () => void;
  onExportDiagnostic: () => void;
  onReboot: () => void;
  onShutdown: () => void;
  languageLabels: { de: string; en: string };
  statusBarLabels: {
    offline: string;
    rescue: string;
    deutsch: string;
    english: string;
  };
  statusLabels: Record<string, string>;
  systemMenuLabels: Record<string, string>;
  showToolbarBrand?: boolean;
  children: React.ReactNode;
}> = (props) => {
  const version = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0';
  const showBrand = props.showToolbarBrand !== false;

  return (
    <div
      className="rescue-shell"
      style={{ fontFamily: t.font }}
      onDragStart={(e) => e.preventDefault()}
    >
      <div className="rescue-app-shell" data-rescue-app-shell="true">
        <header className="rescue-toolbar" role="toolbar" aria-label={props.systemMenuLabels.menu}>
          {showBrand ? (
            <div className="rescue-toolbar-brand">
              <img src={RESCUE_LOGO} alt="" className="rescue-toolbar-logo" aria-hidden />
              <span className="rescue-toolbar-wordmark">
                Setup<span className="rescue-brand-green">helfer</span>
              </span>
            </div>
          ) : (
            <div className="rescue-toolbar-spacer" aria-hidden />
          )}
          <div className="rescue-toolbar-actions">
            <RescueLanguageSelect locale={props.locale} onLocaleChange={props.onLocaleChange} />
          <RescueSystemMenu
            labels={props.systemMenuLabels as never}
            onOpenLogs={props.onOpenLogs}
            onOpenShell={props.onOpenShell}
            onExportDiagnostic={props.onExportDiagnostic}
            onReboot={props.onReboot}
          />
          <RescuePowerButton
            label={props.systemMenuLabels.shutdown}
            confirmLabel={props.systemMenuLabels.confirmShutdown}
            cancelLabel={props.systemMenuLabels.cancel}
            onShutdown={props.onShutdown}
          />
          </div>
        </header>
        <main className="rescue-main">{props.children}</main>
      </div>
      <RescueStatusBar
        version={version}
        locale={props.locale}
        status={props.status}
        labels={props.statusBarLabels}
        statusLabels={props.statusLabels}
      />
    </div>
  );
};
