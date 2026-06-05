import React from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw } from 'lucide-react'
import type { DccBootClassification, DccBootProbeResult } from '../../lib/devDashboard/dccBootState'
import { hasDccBundleMarkers } from '../../lib/devDashboard/dccBootState'
import { extractDccPortsFromVersion } from '../../lib/devDashboard/dccGate'

const STATE_LABEL_KEYS: Record<string, string> = {
  dcc_active: 'devDashboard.bootDiagnostics.state.dccActive',
  profile_blocked_release: 'devDashboard.bootDiagnostics.state.profileBlocked',
  api_unreachable: 'devDashboard.bootDiagnostics.state.apiUnreachable',
  api_error: 'devDashboard.bootDiagnostics.state.apiError',
  frontend_runtime_error: 'devDashboard.bootDiagnostics.state.runtimeError',
  stale_or_wrong_bundle: 'devDashboard.bootDiagnostics.state.staleBundle',
  unknown_dcc_boot_failure: 'devDashboard.bootDiagnostics.state.unknown',
  boot_loading: 'devDashboard.bootDiagnostics.state.loading',
}

export const DccBootDiagnosticsPanel: React.FC<{
  classification: DccBootClassification
  probe: DccBootProbeResult | null
  onRetry: () => void
  retryDisabled?: boolean
  runtimeError?: { message: string; componentStack?: string | null } | null
}> = ({ classification, probe, onRetry, retryDisabled, runtimeError }) => {
  const { t } = useTranslation()
  const bundle = hasDccBundleMarkers()
  const ports = extractDccPortsFromVersion(
    (probe?.versionPayload as Parameters<typeof extractDccPortsFromVersion>[0]) ?? null,
  )
  const stateKey = STATE_LABEL_KEYS[classification.state] ?? classification.state
  const installProfile =
    (probe?.versionPayload?.install_profile as string | undefined) ?? probe?.frontendBuildProfile ?? '—'
  const devControlEnabled = probe?.versionPayload?.dev_control_enabled

  return (
    <section
      className="border-b border-slate-700 bg-slate-900/90 px-4 py-3"
      data-testid="dcc-boot-diagnostics"
      data-dcc-boot-state={classification.state}
    >
      <div className="max-w-[1600px] mx-auto">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-violet-200">
              {t('devDashboard.bootDiagnostics.title', 'DCC Boot-Diagnose')}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {t('devDashboard.bootDiagnostics.subtitle', 'Fail-safe — diese Seite bleibt nie leer.')}
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary inline-flex items-center gap-1 text-xs"
            onClick={onRetry}
            disabled={retryDisabled}
            data-testid="dcc-boot-diagnostics-retry"
          >
            <RefreshCw size={14} />
            {t('devDashboard.profileDisabled.retry', 'DCC-Status erneut prüfen')}
          </button>
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3 text-xs font-mono text-slate-300">
          <div className="rounded border border-slate-700 bg-slate-950/60 px-2 py-1.5">
            <span className="text-slate-500">{t('devDashboard.bootDiagnostics.bootState', 'Boot-State')}: </span>
            <span className="text-amber-200" data-testid="dcc-boot-state-label">
              {t(stateKey, classification.state)}
            </span>
          </div>
          <div className="rounded border border-slate-700 bg-slate-950/60 px-2 py-1.5">
            <span className="text-slate-500">{t('devDashboard.bootDiagnostics.bundleMarker', 'Bundle')}: </span>
            <span className={bundle.ok ? 'text-emerald-300' : 'text-red-300'}>
              {bundle.marker} ({bundle.ok ? 'ok' : 'missing'})
            </span>
          </div>
          <div className="rounded border border-slate-700 bg-slate-950/60 px-2 py-1.5">
            <span className="text-slate-500">{t('devDashboard.bootDiagnostics.dccExpected', 'DCC erwartet')}: </span>
            <span className={classification.dccExpectedVisible ? 'text-emerald-300' : 'text-slate-400'}>
              {classification.dccExpectedVisible ? 'yes' : 'no'}
            </span>
          </div>
        </div>

        <ul className="mt-2 text-xs text-slate-400 space-y-1 font-mono list-none">
          <li>
            {t('devDashboard.bootDiagnostics.loadedUrl', 'URL')}: {probe?.loadedUrl ?? (typeof window !== 'undefined' ? window.location.href : '—')}
          </li>
          <li>
            {t('devDashboard.bootDiagnostics.apiBase', 'API Base')}: {probe?.apiBaseUrl ?? '—'}
          </li>
          <li>
            {t('devDashboard.bootDiagnostics.build', 'Build')}: v{probe?.buildVersion ?? '—'} / id={probe?.buildId ?? '—'} / profile=
            {probe?.frontendBuildProfile ?? '—'}
          </li>
          <li>
            GET {probe?.versionUrl ?? '/api/version'} =&gt; HTTP {probe?.versionHttp ?? '—'}
          </li>
          <li>
            GET {probe?.statusUrl ?? '/api/dev-dashboard/status'} =&gt; HTTP {probe?.statusHttp ?? '—'}
            {probe?.statusCode ? ` (code=${probe.statusCode})` : ''}
          </li>
          <li>
            install_profile={String(installProfile)} dev_control_enabled={String(devControlEnabled ?? '—')}
          </li>
          <li>
            {t('devDashboard.bootDiagnostics.ports', 'Ports')}: API {ports.api} · UI {ports.ui} · nginx {ports.nginx}{' '}
            {t('devDashboard.bootDiagnostics.nginxHint', '(8080 nicht DCC)')}
          </li>
          {classification.reason ? (
            <li className="text-amber-200/90">
              {t('devDashboard.bootDiagnostics.reason', 'Grund')}: {classification.reason}
            </li>
          ) : null}
        </ul>

        {runtimeError ? (
          <div
            className="mt-3 rounded border border-red-700/50 bg-red-950/30 p-3 text-xs text-red-100"
            data-testid="dcc-boot-runtime-error"
          >
            <p className="font-semibold">{t('devDashboard.bootDiagnostics.runtimeError', 'frontend_runtime_error')}</p>
            <pre className="mt-1 whitespace-pre-wrap break-all text-red-200/90">{runtimeError.message}</pre>
            {runtimeError.componentStack ? (
              <pre className="mt-2 whitespace-pre-wrap break-all text-red-200/70 text-[10px]">
                {runtimeError.componentStack}
              </pre>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  )
}
