import React, { useEffect, useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { fetchRescueAgentSessions, type RescueAgentSession } from '../../api/fleetSessionsApi'

export function RescueAgentPanel() {
  const { t } = useTranslation()
  const [sessions, setSessions] = useState<RescueAgentSession[]>([])

  useEffect(() => {
    let mounted = true
    void fetchRescueAgentSessions().then((rows) => {
      if (mounted) setSessions(rows)
    })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 mb-4" data-testid="rescue-agent-panel">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-2">
        <ShieldCheck size={16} className="text-emerald-400" />
        {t('devDashboard.rescueAgent.title', 'Rescue Agents / Rettungsstick-Knoten')}
      </h3>
      <p className="text-xs text-amber-300 mb-2">
        {t(
          'devDashboard.rescueAgent.previewWarning',
          'Vorschau / Sicherheitsmenü - keine Reparatur ohne spätere Freigabe.'
        )}
      </p>
      {sessions.length === 0 ? (
        <p className="text-xs text-slate-400">{t('devDashboard.rescueAgent.empty', 'Keine Rescue-Agent-Sessions sichtbar.')}</p>
      ) : (
        <ul className="space-y-2 text-xs">
          {sessions.map((s) => {
            const flags = [
              s.registration_status === 'pending' ? 'pending_pairing' : null,
              s.registration_status === 'accepted' ? 'paired' : null,
              s.last_heartbeat_at ? 'heartbeat_seen' : 'offline',
              s.report_received ? 'report_received' : null,
              'e2ee_required',
              s.report_received ? 'e2ee_ok' : null,
              'firewall_policy_ready',
              s.agent_state === 'stalled' ? 'timeout' : null,
            ].filter(Boolean)
            return (
            <li key={s.session_id} className="rounded border border-slate-700 p-2">
              <p className="text-slate-200 font-mono">{s.session_id}</p>
              <p className="text-slate-400">
                {t('devDashboard.rescueAgent.status', 'Status')}: {s.registration_status} / {s.agent_state || 'booting'}
              </p>
              <p className="text-slate-400 font-mono text-[10px]">{flags.join(' · ')}</p>
              <p className="text-slate-400">
                {t('devDashboard.rescueAgent.heartbeat', 'Letzter Heartbeat')}: {s.last_heartbeat_at || '—'}
              </p>
              <p className="text-slate-400">
                {t('devDashboard.rescueAgent.siteHint', 'Standort')}: {s.operator_label || 'operator_label/site_hint only'}
              </p>
            </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
