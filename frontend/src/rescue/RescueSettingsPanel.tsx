import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchTelemetryRuntimeStatus, runTelemetryFunctionalTest } from './rescueBackupApi';
import { fetchTelemetryOptIn, setTelemetryOptIn } from './rescueNetworkApi';
import type { RescueBootStatus } from './rescueTypes';
import { RESCUE_LOCALES, getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { rescueTheme as theme } from './rescueTheme';

export const RescueSettingsPanel: React.FC<{
  locale: RescueLocale;
  status: RescueBootStatus;
  onLocaleChange: (locale: RescueLocale) => void;
  onStatusRefresh?: () => void;
}> = ({ locale, status, onLocaleChange, onStatusRefresh }) => {
  const [expert, setExpert] = useState(false);
  const [telemetryBusy, setTelemetryBusy] = useState(false);
  const [telemetryError, setTelemetryError] = useState('');
  const [telemetryOn, setTelemetryOn] = useState(status.telemetry.opt_in);
  const [telemetryTestMsg, setTelemetryTestMsg] = useState('');
  const dict = useMemo(() => getRescueDict(locale), [locale]);

  useEffect(() => {
    if (!telemetryOn) return;
    void fetchTelemetryRuntimeStatus().then((st) => {
      const ft = (st.functional_test || {}) as Record<string, unknown>;
      if (ft.push_attempted) {
        setTelemetryTestMsg(
          ft.network_upload_ok
            ? tPath(dict, 'settings.telemetryTestOk')
            : ft.spooled_locally
              ? tPath(dict, 'settings.telemetryTestSpooled')
              : tPath(dict, 'settings.telemetryTestPending'),
        );
      }
    });
  }, [telemetryOn, dict]);

  useEffect(() => {
    setTelemetryOn(status.telemetry.opt_in);
  }, [status.telemetry.opt_in]);

  useEffect(() => {
    void fetchTelemetryOptIn().then((on) => setTelemetryOn(on || status.telemetry.opt_in));
  }, [status.telemetry.opt_in]);

  const enableTelemetry = useCallback(async () => {
    setTelemetryBusy(true);
    setTelemetryError('');
    try {
      const res = await setTelemetryOptIn(true);
      if (!res.success) {
        setTelemetryError(tPath(dict, 'settings.telemetryEnableFailed'));
        return;
      }
      setTelemetryOn(true);
      onStatusRefresh?.();
    } catch {
      setTelemetryError(tPath(dict, 'settings.telemetryEnableFailed'));
    } finally {
      setTelemetryBusy(false);
    }
  }, [dict, onStatusRefresh]);

  const row = (label: string, value: React.ReactNode) => (
    <div className="rescue-settings-row">
      <span className="rescue-settings-label">{label}</span>
      <span className="rescue-settings-value">{value}</span>
    </div>
  );

  return (
    <div className="rescue-settings" data-rescue-settings="true">
      {row(
        tPath(dict, 'settings.language'),
        <div className="rescue-settings-lang" role="group" aria-label={tPath(dict, 'settings.language')}>
          {RESCUE_LOCALES.map(({ code, flag }) => (
            <button
              key={code}
              type="button"
              className={`rescue-focus-ring rescue-settings-chip${locale === code ? ' rescue-settings-chip-active' : ''}`}
              aria-pressed={locale === code}
              onClick={() => onLocaleChange(code)}
            >
              {flag} {tPath(dict, `language.${code}`)}
            </button>
          ))}
        </div>,
      )}
      {row(tPath(dict, 'settings.theme'), tPath(dict, 'settings.themeDark'))}
      {row(
        tPath(dict, 'settings.telemetry'),
        telemetryOn ? (
          tPath(dict, 'settings.telemetryOn')
        ) : (
          <div className="rescue-settings-telemetry">
            <span>{tPath(dict, 'settings.telemetryOff')}</span>
            <button
              type="button"
              className="rescue-focus-ring rescue-settings-chip"
              disabled={telemetryBusy}
              onClick={() => void enableTelemetry()}
            >
              {telemetryBusy ? tPath(dict, 'settings.telemetryEnabling') : tPath(dict, 'settings.telemetryEnable')}
            </button>
          </div>
        ),
      )}
      {telemetryError ? <p style={{ color: theme.statusErr }}>{telemetryError}</p> : null}
      {telemetryOn ? (
        <>
          {row(
            tPath(dict, 'settings.telemetryTest'),
            <button
              type="button"
              className="rescue-focus-ring rescue-settings-chip"
              onClick={() => {
                setTelemetryTestMsg(tPath(dict, 'settings.telemetryTestRunning'));
                void runTelemetryFunctionalTest().then((r) => {
                  setTelemetryTestMsg(
                    r.ok
                      ? tPath(dict, 'settings.telemetryTestOk')
                      : tPath(dict, 'settings.telemetryTestFailed'),
                  );
                });
              }}
            >
              {tPath(dict, 'settings.telemetryTest')}
            </button>,
          )}
          {telemetryTestMsg ? row('', telemetryTestMsg) : null}
        </>
      ) : null}
      {row(tPath(dict, 'settings.rescueMode'), tPath(dict, 'settings.rescueModeReact'))}
      {row(
        tPath(dict, 'settings.expertMode'),
        <label>
          <input type="checkbox" checked={expert} onChange={(e) => setExpert(e.target.checked)} />{' '}
          {expert ? tPath(dict, 'settings.yes') : tPath(dict, 'settings.no')}
        </label>,
      )}
      {expert ? <p className="rescue-section-intro">{tPath(dict, 'settings.expertHint')}</p> : null}
      <p className="rescue-section-intro">{tPath(dict, 'settings.noSystemdDump')}</p>
      <aside className="rescue-migration-panda" role="note">
        <strong>{tPath(dict, 'guide.title')}:</strong> {tPath(dict, 'guide.summary')}
      </aside>
    </div>
  );
};
