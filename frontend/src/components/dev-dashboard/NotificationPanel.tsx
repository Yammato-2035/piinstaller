import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { Bell, Mail } from 'lucide-react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'

type NotificationEvent = {
  event_id?: string
  created_at?: string
  severity?: string
  area?: string
  event_type?: string
  title?: string
  message?: string
  technical_summary?: string
  evidence_paths?: string[]
  dashboard_visible?: boolean
  email_status?: string
  email_error?: string | null
  acknowledged?: boolean
}

type NotificationSummary = {
  status?: string
  event_count?: number
  last_event?: NotificationEvent | null
  email?: {
    status?: string
    configured?: boolean
    enabled?: boolean
    recipient_masked?: string | null
  }
  dashboard?: {
    status?: string
    visible_event_count?: number
  }
}

type NotificationEventsResponse = {
  events?: NotificationEvent[]
}

function statusLabel(status: string | undefined, t: (key: string) => string): string {
  switch (status) {
    case 'not_configured':
      return t('devDashboard.notifications.emailStatus.notConfigured')
    case 'sent':
      return t('devDashboard.notifications.emailStatus.sent')
    case 'failed':
      return t('devDashboard.notifications.emailStatus.failed')
    case 'queued':
      return t('devDashboard.notifications.emailStatus.queued')
    case 'disabled':
      return t('devDashboard.notifications.emailStatus.disabled')
    case 'ready':
      return t('devDashboard.notifications.emailStatus.ready')
    default:
      return status || '—'
  }
}

export function NotificationPanel({ refreshSec = 15 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [summary, setSummary] = useState<NotificationSummary | null>(null)
  const [events, setEvents] = useState<NotificationEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<'dashboard' | 'email' | null>(null)

  const loadData = useCallback(async () => {
    try {
      setError(null)
      const [statusRes, eventsRes] = await Promise.all([
        fetchApi('/api/dev-dashboard/notifications/status'),
        fetchApi('/api/dev-dashboard/notifications/events'),
      ])
      const statusBody = (await statusRes.json()) as NotificationSummary
      const eventsBody = (await eventsRes.json()) as NotificationEventsResponse
      setSummary(statusBody)
      setEvents(eventsBody.events || [])
    } catch {
      setError('fetch_failed')
    }
  }, [])

  useEffect(() => {
    void loadData()
    const id = window.setInterval(() => void loadData(), Math.max(5, refreshSec) * 1000)
    return () => window.clearInterval(id)
  }, [loadData, refreshSec])

  const triggerDashboardTest = useCallback(async () => {
    try {
      setBusy('dashboard')
      const res = await fetchApi('/api/dev-dashboard/notifications/test-dashboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          severity: 'warning',
          area: 'dev_dashboard',
          message: 'Dashboard notification smoke test',
        }),
      })
      const body = await res.json()
      if (body?.status === 'created') {
        toast.success(t('devDashboard.notifications.dashboardTestCreated'))
      } else {
        toast.error(t('devDashboard.notifications.dashboardTestFailed'))
      }
      await loadData()
    } catch {
      toast.error(t('devDashboard.notifications.dashboardTestFailed'))
    } finally {
      setBusy(null)
    }
  }, [loadData, t])

  const triggerEmailTest = useCallback(async () => {
    try {
      setBusy('email')
      const res = await fetchApi('/api/dev-dashboard/notifications/test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'Setuphelfer notification email smoke test' }),
      })
      const body = await res.json()
      if (body?.email_status === 'sent') {
        toast.success(t('devDashboard.notifications.emailTestSent'))
      } else if (body?.email_status === 'not_configured' || body?.email_status === 'disabled') {
        toast.error(t('devDashboard.notifications.emailStatus.notConfigured'))
      } else {
        toast.error(body?.email_error || t('devDashboard.notifications.emailTestFailed'))
      }
      await loadData()
    } catch {
      toast.error(t('devDashboard.notifications.emailTestFailed'))
    } finally {
      setBusy(null)
    }
  }, [loadData, t])

  const overall = String(summary?.status || 'gray')
  const emailStatus = String(summary?.email?.status || 'unknown')
  const emailReady = emailStatus === 'ready'

  return (
    <section className={`rounded-xl border p-4 space-y-3 ${toneClass(overall)}`} data-testid="notification-panel">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Bell size={18} className="shrink-0" />
            {t('devDashboard.notifications.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">{t('devDashboard.notifications.subtitle')}</p>
        </div>
        <span className="text-xs uppercase tracking-wide font-mono">{overall}</span>
      </div>

      {error ? <p className="text-xs text-rose-200">{error}</p> : null}

      <div className="grid lg:grid-cols-2 gap-3">
        <div className="rounded-lg border border-slate-700/70 bg-slate-950/30 p-3 space-y-2">
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.notifications.statusTitle')}</p>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-slate-300">{t('devDashboard.notifications.latestEvents')}</span>
            <span className="font-mono text-slate-100">{String(summary?.event_count ?? 0)}</span>
          </div>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-slate-300">{t('devDashboard.notifications.dashboardVisible')}</span>
            <span className="font-mono text-slate-100">{String(summary?.dashboard?.visible_event_count ?? 0)}</span>
          </div>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-slate-300">{t('devDashboard.notifications.emailStatus.title')}</span>
            <span className="font-mono text-slate-100">{statusLabel(emailStatus, t)}</span>
          </div>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-slate-300">{t('devDashboard.notifications.recipient')}</span>
            <span className="font-mono text-slate-100">{summary?.email?.recipient_masked || '—'}</span>
          </div>
        </div>

        <div className="rounded-lg border border-slate-700/70 bg-slate-950/30 p-3 space-y-3">
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.notifications.actions')}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-md border border-slate-700 bg-slate-900/70 px-2.5 py-1.5 text-xs text-slate-100 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={() => void triggerDashboardTest()}
              disabled={busy !== null}
            >
              {t('devDashboard.notifications.dashboardTestEvent')}
            </button>
            <button
              type="button"
              className="rounded-md border border-slate-700 bg-slate-900/70 px-2.5 py-1.5 text-xs text-slate-100 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1"
              onClick={() => void triggerEmailTest()}
              disabled={busy !== null || !emailReady}
              title={!emailReady ? statusLabel(emailStatus, t) : undefined}
            >
              <Mail size={12} />
              {t('devDashboard.notifications.sendTestEmail')}
            </button>
          </div>
          {!emailReady ? (
            <p className="text-xs text-amber-200">
              {t('devDashboard.notifications.emailHint', { status: statusLabel(emailStatus, t) })}
            </p>
          ) : null}
        </div>
      </div>

      <div className="rounded-lg border border-slate-700/70 bg-slate-950/30 p-3 space-y-2">
        <p className="text-xs font-semibold text-slate-100">{t('devDashboard.notifications.latestEvents')}</p>
        {events.length === 0 ? (
          <p className="text-xs text-slate-400">{t('devDashboard.notifications.none')}</p>
        ) : (
          <div className="space-y-2">
            {events.slice(0, 8).map((event) => (
              <div key={event.event_id || `${event.event_type}-${event.created_at}`} className="rounded-md border border-slate-800 bg-slate-900/50 p-3 space-y-1.5">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                  <span className="font-semibold text-slate-100">{event.title || event.event_type}</span>
                  <span className="font-mono text-slate-300">{event.severity || '—'}</span>
                  <span className="font-mono text-slate-300">{event.area || '—'}</span>
                  <span className="font-mono text-slate-300">{event.event_type || '—'}</span>
                  <span className="text-slate-400">
                    {event.created_at ? new Date(event.created_at).toLocaleString() : '—'}
                  </span>
                </div>
                <p className="text-xs text-slate-200">{event.message || '—'}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-400">
                  <span>
                    {t('devDashboard.notifications.dashboardVisible')}: {event.dashboard_visible ? 'true' : 'false'}
                  </span>
                  <span>
                    {t('devDashboard.notifications.emailStatus.title')}: {statusLabel(event.email_status, t)}
                  </span>
                  <span>{t('devDashboard.notifications.acknowledged')}: {event.acknowledged ? 'true' : 'false'}</span>
                </div>
                {event.email_error ? (
                  <p className="text-xs text-rose-200">
                    {t('devDashboard.notifications.emailError')}: {event.email_error}
                  </p>
                ) : null}
                {event.technical_summary ? <p className="text-[11px] text-slate-400">{event.technical_summary}</p> : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
