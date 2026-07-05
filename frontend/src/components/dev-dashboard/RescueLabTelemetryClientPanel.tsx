import React, { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DccCompactStatus } from '../../lib/devDashboard/dccCompactStatus'

export type RescueLabTelemetryClientPanelProps = {
  labClient?: NonNullable<DccCompactStatus['rescue']>['lab_telemetry_client']
  installProfile?: string
  dccVisible?: boolean
}

type ReachabilityBody = {
  code?: string
  reachability?: {
    network_state?: string
    telemetry_reachability?: string
    checked_at?: string
  }
}

type SendPreviewBody = {
  code?: string
  result?: {
    send_mode?: string
    send_executed?: boolean
    production_ready?: boolean
  }
  errors?: string[]
}

export const RescueLabTelemetryClientPanel: React.FC<RescueLabTelemetryClientPanelProps> = ({
  labClient,
  installProfile,
  dccVisible,
}) => {
  const { t } = useTranslation()
  const [busy, setBusy] = useState(false)
  const [lastReachability, setLastReachability] = useState<ReachabilityBody | null>(null)
  const [lastSendPreview, setLastSendPreview] = useState<SendPreviewBody | null>(null)
  const [error, setError] = useState<string | null>(null)

  const profile = installProfile ?? labClient?.install_profile ?? 'unknown'
  const labApiEnabled = labClient?.lab_api_enabled ?? dccVisible ?? false

  const onReachabilityCheck = useCallback(async () => {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch('/api/rescue/telemetry/lab/reachability', { cache: 'no-store' })
      const body = (await res.json().catch(() => null)) as ReachabilityBody | null
      setLastReachability(body)
      if (!res.ok) setError(`HTTP ${res.status}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'reachability_failed')
    } finally {
      setBusy(false)
    }
  }, [busy])

  const onSendPreviewPrepare = useCallback(async () => {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch('/api/rescue/telemetry/lab/send-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          allow_send_when_reachable: false,
          create_offline_queue_preview_when_blocked: true,
        }),
      })
      const body = (await res.json().catch(() => null)) as SendPreviewBody | null
      setLastSendPreview(body)
      if (body?.errors?.length) setError(body.errors.join('; '))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'send_preview_failed')
    } finally {
      setBusy(false)
    }
  }, [busy])

  const onLiveLabSendTest = useCallback(async () => {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch('/api/rescue/telemetry/lab/send-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          allow_send_when_reachable: true,
          create_offline_queue_preview_when_blocked: true,
        }),
      })
      const body = (await res.json().catch(() => null)) as SendPreviewBody | null
      setLastSendPreview(body)
      if (body?.errors?.length) setError(body.errors.join('; '))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'live_send_failed')
    } finally {
      setBusy(false)
    }
  }, [busy])

  if (!dccVisible) {
    return (
      <p className="text-sm text-slate-400">
        {t('devDashboard.rescueLabTelemetry.hidden', 'Rescue Lab-Telemetrie nur im DCC-Lab-Profil sichtbar.')}
      </p>
    )
  }

  const networkGate =
    lastReachability?.reachability?.network_state ?? labClient?.network_gate ?? 'unknown'
  const lastSendMode = lastSendPreview?.result?.send_mode ?? labClient?.last_send_mode ?? 'pending'

  return (
    <section
      className="rounded-lg border border-cyan-900/50 bg-slate-900/60 p-4 space-y-3"
      data-testid="rescue-lab-telemetry-client-panel"
    >
      <h3 className="text-lg font-semibold text-cyan-100">
        {t('devDashboard.rescueLabTelemetry.title', 'Rescue Telemetry Lab Client')}
      </h3>
      <p className="text-sm text-slate-300">
        {t(
          'devDashboard.rescueLabTelemetry.subtitle',
          'PI-RS-TEL-002 — Reachability + Offline-Queue-Preview. production_ready=false.',
        )}
      </p>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <dt className="text-slate-400">Profil</dt>
        <dd>{profile}</dd>
        <dt className="text-slate-400">Lab-API</dt>
        <dd>{labApiEnabled ? 'enabled' : 'disabled'}</dd>
        <dt className="text-slate-400">Lab-Base-URL</dt>
        <dd>{labClient?.lab_base_url_configured ? 'configured' : 'missing'}</dd>
        <dt className="text-slate-400">Secret</dt>
        <dd>{labClient?.secret_configured ? 'configured' : 'missing'}</dd>
        <dt className="text-slate-400">Network Gate</dt>
        <dd>{networkGate}</dd>
        <dt className="text-slate-400">Last Reachability</dt>
        <dd>
          {lastReachability?.reachability?.checked_at
            ? `${lastReachability.reachability.checked_at} / ${lastReachability.reachability.telemetry_reachability}`
            : labClient?.last_reachability_checked_at ?? '—'}
        </dd>
        <dt className="text-slate-400">Last Send Preview</dt>
        <dd>{lastSendMode}</dd>
        <dt className="text-slate-400">Offline Queue Preview</dt>
        <dd>
          count={labClient?.offline_queue_preview_count ?? 0}; reason=
          {labClient?.offline_queue_preview_latest_reason ?? '—'}; auto replay=false
        </dd>
        <dt className="text-slate-400">production_ready</dt>
        <dd>false</dd>
      </dl>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded bg-slate-700 px-3 py-2 text-sm text-white disabled:opacity-50"
          disabled={busy}
          onClick={() => void onReachabilityCheck()}
        >
          {t('devDashboard.rescueLabTelemetry.reachability', 'Reachability prüfen')}
        </button>
        <button
          type="button"
          className="rounded bg-cyan-800 px-3 py-2 text-sm text-white disabled:opacity-50"
          disabled={busy}
          onClick={() => void onSendPreviewPrepare()}
        >
          {t('devDashboard.rescueLabTelemetry.sendPreview', 'Send-Preview vorbereiten')}
        </button>
        {labApiEnabled ? (
          <button
            type="button"
            className="rounded bg-amber-800 px-3 py-2 text-sm text-white disabled:opacity-50"
            disabled={busy}
            onClick={() => void onLiveLabSendTest()}
          >
            {t('devDashboard.rescueLabTelemetry.liveSend', 'Live-Lab-Send testen')}
          </button>
        ) : null}
      </div>
      <p className="text-xs text-amber-200/90">
        {t(
          'devDashboard.rescueLabTelemetry.warning',
          'Sendet ausschließlich synthetische Lab-Payload ohne Hostdaten. Live-Send erfordert SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST=1.',
        )}
      </p>
      {error ? <p className="text-xs text-red-300">{error}</p> : null}
    </section>
  )
}
