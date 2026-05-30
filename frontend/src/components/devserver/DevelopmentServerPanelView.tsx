import React from 'react'
import { useTranslation } from 'react-i18next'
import { Server, Shield, Terminal } from 'lucide-react'
import type { DevServerHealth, DevServerNode, DevServerSummary } from '../../api/devServerApi'
import { toneClass } from '../../pages/devDashboardFilters'

function nodeKindLabel(kind: string | undefined, t: (k: string) => string): string {
  const key = `devDashboard.devServer.nodeKind.${kind || 'unknown'}`
  const translated = t(key)
  return translated === key ? kind || 'unknown' : translated
}

function statusDot(status: string | undefined): string {
  if (status === 'online') return 'bg-emerald-500'
  if (status === 'busy') return 'bg-amber-400'
  if (status === 'error') return 'bg-red-500'
  if (status === 'offline') return 'bg-slate-500'
  return 'bg-slate-600'
}

export type DevelopmentServerPanelViewProps = {
  health: DevServerHealth | null
  summary: DevServerSummary | null
  nodes: DevServerNode[]
  busyNode: string | null
  error: string | null
  onRunAction: (nodeId: string, action: 'check' | 'inventory' | 'storage' | 'boot') => void
}

export function DevelopmentServerPanelView({
  health,
  summary,
  nodes,
  busyNode,
  error,
  onRunAction,
}: DevelopmentServerPanelViewProps) {
  const { t } = useTranslation()
  const sshAllowed = Boolean(health?.enabled && health?.ssh_allowed)
  const enabled = Boolean(health?.enabled)

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 mb-4"
      data-testid="development-server-panel"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Server className="text-sky-400" size={18} aria-hidden />
            {t('devDashboard.devServer.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-1">{t('devDashboard.devServer.subtitle')}</p>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded border ${enabled ? 'border-emerald-600/50 text-emerald-200' : 'border-slate-600 text-slate-400'}`}
          data-testid="dev-server-enabled-badge"
        >
          {enabled ? t('devDashboard.devServer.enabled') : t('devDashboard.devServer.disabled')}
        </span>
      </div>

      <ul className="text-[11px] text-slate-400 space-y-1 mb-3" data-testid="dev-server-safety-hints">
        <li className="flex items-center gap-1">
          <Shield size={12} aria-hidden />
          {t('devDashboard.devServer.hintReadOnly')}
        </li>
        <li>{t('devDashboard.devServer.hintNoWrite')}</li>
        <li>{t('devDashboard.devServer.hintPublicBlocked')}</li>
        <li>{t('devDashboard.devServer.hintBetaRedacted')}</li>
      </ul>

      {error ? <p className="text-xs text-red-300 mb-2">{error}</p> : null}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2 mb-4 text-xs" data-testid="dev-server-status-grid">
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.devServer.mode')}</span>
          <div className="text-slate-200">{health?.mode ?? '—'}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.devServer.storageOk')}</span>
          <div className={health?.storage_ok ? 'text-emerald-300' : 'text-slate-400'} data-testid="dev-server-storage-ok">
            {health?.storage_ok ? t('devDashboard.greenVisibility.ok') : '—'}
          </div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.devServer.nodes')}</span>
          <div className="text-slate-200">{summary?.node_count ?? 0}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.devServer.online')}</span>
          <div className="text-slate-200">{summary?.online_count ?? 0}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.devServer.reports24h')}</span>
          <div className="text-slate-200">{summary?.reports_last_24h ?? 0}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5" data-testid="dev-server-ssh-safe">
          <span className="text-slate-500">{t('devDashboard.devServer.sshStatus')}</span>
          <div className={sshAllowed ? 'text-amber-300' : 'text-emerald-300'}>
            {sshAllowed ? t('devDashboard.devServer.sshEnabled') : t('devDashboard.devServer.sshDisabledSafe')}
          </div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5" data-testid="dev-server-public-uploads">
          <span className="text-slate-500">{t('devDashboard.devServer.publicUploads')}</span>
          <div className={health?.public_uploads_allowed ? 'text-amber-300' : 'text-emerald-300'}>
            {health?.public_uploads_allowed ? t('devDashboard.devServer.publicUploadsEnabled') : t('devDashboard.devServer.publicUploadsDisabledSafe')}
          </div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.devServer.errors')}</span>
          <div className="text-slate-200">{summary?.error_count ?? 0}</div>
        </div>
      </div>

      {(summary?.latest_findings?.length ?? 0) > 0 ? (
        <div className="mb-4 rounded-lg border border-slate-700/60 bg-slate-950/30 p-3" data-testid="dev-server-latest-findings">
          <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">{t('devDashboard.devServer.latestFindings')}</div>
          <ul className="space-y-1 text-xs text-slate-300">
            {(summary?.latest_findings || []).slice(0, 5).map((f, i) => (
              <li key={String(f.report_id || i)} className="font-mono truncate">
                {String(f.node_id || '—')} · {String(f.report_type || '—')} · {String(f.created_at || '').slice(0, 19)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!enabled ? (
        <p className="text-xs text-slate-400" data-testid="dev-server-disabled-message">
          {t('devDashboard.devServer.disabledHint')}
        </p>
      ) : null}

      {nodes.length > 0 ? (
        <div className="space-y-2" data-testid="dev-server-node-list">
          {nodes.map((node) => {
            const nid = node.node_id || ''
            const isBusy = busyNode === nid || node.status === 'busy'
            return (
              <div
                key={nid}
                className={`rounded-lg border px-3 py-2 text-sm ${toneClass(node.status === 'error' ? 'red' : node.status === 'online' ? 'green' : 'gray')}`}
                data-testid={`dev-server-node-${nid}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${statusDot(node.status)}`} aria-hidden />
                  <span className="font-medium text-white">{node.display_name || nid}</span>
                  <span className="text-[10px] uppercase tracking-wide text-slate-400">
                    {nodeKindLabel(node.node_kind, t)}
                  </span>
                  <span className="text-xs text-slate-400 ml-auto">{node.status}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1 grid sm:grid-cols-2 gap-1">
                  <span>
                    {t('devDashboard.devServer.lastReport')}: {node.last_report_type || '—'}
                  </span>
                  <span>
                    {t('devDashboard.devServer.sshStatus')}: {node.ssh?.last_check_status || '—'}
                  </span>
                  {node.current_action ? (
                    <span className="sm:col-span-2">
                      {t('devDashboard.devServer.currentAction')}: {node.current_action}
                    </span>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-1 mt-2" data-testid={`dev-server-node-actions-${nid}`}>
                  {(['check', 'inventory', 'storage', 'boot'] as const).map((action) => (
                    <button
                      key={action}
                      type="button"
                      disabled={!sshAllowed || isBusy}
                      data-testid={`dev-server-ssh-${action}-${nid}`}
                      className="px-2 py-1 text-[10px] rounded border border-slate-600 text-slate-200 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800/60 inline-flex items-center gap-1"
                      onClick={() => onRunAction(nid, action)}
                    >
                      <Terminal size={10} aria-hidden />
                      {t(`devDashboard.devServer.sshAction.${action}`)}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      ) : enabled ? (
        <p className="text-xs text-slate-400">{t('devDashboard.devServer.noNodes')}</p>
      ) : null}
    </section>
  )
}
