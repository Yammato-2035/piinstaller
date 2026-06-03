import { useCallback, useEffect, useState } from 'react'
import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'
import { fetchBackendHealth, type BackendHealthResponse } from '../../api/devDashboardApi'

const OPERATOR_COMMANDS = `systemctl status setuphelfer-backend.service
journalctl -u setuphelfer-backend.service -n 200 --no-pager
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
curl -sS http://127.0.0.1:8000/api/version | jq .
./scripts/dev-dashboard/check-backend-health.sh`

function statusTone(status: string | undefined, stale: boolean): string {
  if (stale) return 'yellow'
  if (status === 'ok') return 'green'
  if (status === 'warning') return 'yellow'
  return 'red'
}

function boolLabel(v: boolean | undefined): string {
  if (v === true) return '✓'
  if (v === false) return '✗'
  return '—'
}

export function BackendHealthPanel({ t }: CockpitPanelProps) {
  const [data, setData] = useState<BackendHealthResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAllHistory, setShowAllHistory] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchBackendHealth(showAllHistory ? 20 : 5)
      if (!res) {
        setError(t('devDashboard.backendHealth.unavailable'))
        setData(null)
      } else {
        setData(res)
      }
    } finally {
      setLoading(false)
    }
  }, [t, showAllHistory])

  useEffect(() => {
    void load()
  }, [load])

  const health = data?.current_health
  const tone = statusTone(data?.status, Boolean(data?.stale))
  const history = data?.history_tail ?? []
  const historyVisible = showAllHistory ? history.slice(-20) : history.slice(-5)

  return (
    <div
      className={`rounded-xl border p-4 ${toneClass(tone)}`}
      data-testid="dev-dashboard-backend-health-panel"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">{t('devDashboard.backendHealth.title')}</h2>
        <button
          type="button"
          className="text-xs px-2 py-1 rounded border border-slate-600 text-slate-300 hover:bg-slate-800/60"
          onClick={() => void load()}
          disabled={loading}
        >
          {loading ? t('devDashboard.backendHealth.refreshing') : t('backup.ui.refresh')}
        </button>
      </div>
      <p className="text-xs text-slate-400 mt-1">{t('devDashboard.backendHealth.subtitle')}</p>

      {error ? <p className="text-sm text-rose-200 mt-2">{error}</p> : null}

      {data ? (
        <>
          <div className="mt-3 grid sm:grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.overall')}:</span>{' '}
              <span className="font-mono font-semibold">{health?.overall_status ?? data.status}</span>
              {data.stale ? (
                <span className="ml-2 text-amber-300">({t('devDashboard.backendHealth.stale')})</span>
              ) : null}
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.checkedAt')}:</span>{' '}
              <span className="font-mono">{String(data.generated_at ?? '—')}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.backendService')}:</span>{' '}
              {boolLabel(health?.backend_service_active)}
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.port8000')}:</span>{' '}
              {boolLabel(health?.backend_port_8000_listening)}
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.apiVersion')}:</span>{' '}
              <span className="font-mono">{health?.api_version_http ?? '—'}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.profile')}:</span>{' '}
              <span className="font-mono">{health?.install_profile ?? '—'}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.devControl')}:</span>{' '}
              <span className="font-mono">{String(health?.dev_control_enabled ?? '—')}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.gateStatus')}:</span>{' '}
              <span className="font-mono">{health?.profile_gate_status ?? '—'}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.dccStatus')}:</span>{' '}
              <span className="font-mono">{health?.dev_dashboard_status_http ?? '—'}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.fleet')}:</span>{' '}
              <span className="font-mono">{health?.fleet_sessions_http ?? '—'}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.recentEvidence')}:</span>{' '}
              <span className="font-mono">{health?.recent_evidence_http ?? '—'}</span>
            </div>
            <div>
              <span className="text-slate-400">{t('devDashboard.backendHealth.webUi')}:</span>{' '}
              <span className="font-mono">{health?.web_ui_http ?? health?.frontend_port_3001_listening ? '—' : '—'}</span>
              {' '}
              {boolLabel(health?.frontend_port_3001_listening)}
            </div>
          </div>

          {health?.failure_classification && health.failure_classification !== 'none' ? (
            <p className="mt-2 text-xs text-amber-200">
              {t('devDashboard.backendHealth.failureClass')}:{' '}
              <span className="font-mono">{health.failure_classification}</span>
            </p>
          ) : null}

          {health?.recommended_operator_action ? (
            <p className="mt-1 text-xs text-sky-200">{health.recommended_operator_action}</p>
          ) : null}

          {historyVisible.length > 0 ? (
            <div className="mt-3">
              <div className="text-[10px] uppercase tracking-wide text-slate-400">
                {t('devDashboard.backendHealth.history')}
              </div>
              <ul className="mt-1 space-y-1 text-[11px] font-mono text-slate-300 max-h-32 overflow-y-auto">
                {historyVisible.map((row, i) => (
                  <li key={`h-${i}`}>
                    {String(row.generated_at ?? '—')} — {String(row.overall_status ?? '?')} /{' '}
                    {String(row.failure_classification ?? 'none')}
                  </li>
                ))}
              </ul>
              {history.length > 5 ? (
                <button
                  type="button"
                  className="mt-1 text-[11px] text-violet-300 hover:underline"
                  onClick={() => setShowAllHistory((v) => !v)}
                >
                  {showAllHistory
                    ? t('devDashboard.backendHealth.showLess')
                    : t('devDashboard.backendHealth.showMore')}
                </button>
              ) : null}
            </div>
          ) : null}

          <details className="mt-3 text-xs">
            <summary className="cursor-pointer text-slate-400 hover:text-slate-200">
              {t('devDashboard.backendHealth.operatorCommands')}
            </summary>
            <pre className="mt-2 p-2 rounded bg-slate-950/80 border border-slate-700 overflow-x-auto text-[10px] text-slate-300 whitespace-pre-wrap select-all">
              {OPERATOR_COMMANDS}
            </pre>
            <p className="mt-1 text-slate-500">{t('devDashboard.backendHealth.noAutoExec')}</p>
          </details>
        </>
      ) : null}
    </div>
  )
}
