import React, { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DccCompactStatus } from '../../lib/devDashboard/dccCompactStatus'

export type RescueLabTelemetryClientPanelProps = {
  labClient?: NonNullable<DccCompactStatus['rescue']>['lab_telemetry_client']
  dccVisible?: boolean
}

export const RescueLabTelemetryClientPanel: React.FC<RescueLabTelemetryClientPanelProps> = ({
  labClient,
  dccVisible,
}) => {
  const { t } = useTranslation()
  const [busy, setBusy] = useState(false)
  const [lastCode, setLastCode] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onLabSendTest = useCallback(async () => {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch('/api/rescue/telemetry/lab/send-preview', { method: 'POST' })
      const body = (await res.json().catch(() => null)) as { code?: string; errors?: string[] } | null
      setLastCode(body?.code ?? `HTTP ${res.status}`)
      if (body?.errors?.length) setError(body.errors.join('; '))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'send_failed')
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

  const status = labClient?.last_send_status ?? 'pending'

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
          'PI-RS-TEL-001 — synthetische Lab-Payload ohne Hostdaten. production_ready=false.',
        )}
      </p>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <dt className="text-slate-400">client_id</dt>
        <dd>{labClient?.client_id ?? 'fake-rescue-stick-lab-client'}</dd>
        <dt className="text-slate-400">product</dt>
        <dd>{labClient?.product ?? '—'}</dd>
        <dt className="text-slate-400">source</dt>
        <dd>{labClient?.source ?? '—'}</dd>
        <dt className="text-slate-400">secret_configured</dt>
        <dd>{labClient?.secret_configured ? 'true' : 'false'}</dd>
        <dt className="text-slate-400">lab_base_url_configured</dt>
        <dd>{labClient?.lab_base_url_configured ? 'true' : 'false'}</dd>
        <dt className="text-slate-400">last_send_status</dt>
        <dd>{status}</dd>
        <dt className="text-slate-400">production_ready</dt>
        <dd>false</dd>
        <dt className="text-slate-400">next_required_action</dt>
        <dd className="col-span-1">{labClient?.next_required_action ?? '—'}</dd>
      </dl>
      <p className="text-xs text-amber-200/90">
        {t(
          'devDashboard.rescueLabTelemetry.warning',
          'Sendet ausschließlich synthetische Lab-Payload ohne Hostdaten.',
        )}
      </p>
      <button
        type="button"
        className="rounded bg-cyan-800 px-3 py-2 text-sm text-white disabled:opacity-50"
        disabled={busy}
        onClick={() => void onLabSendTest()}
      >
        {t('devDashboard.rescueLabTelemetry.sendTest', 'Lab-Send testen')}
      </button>
      {lastCode ? <p className="text-xs text-slate-400">last_code: {lastCode}</p> : null}
      {error ? <p className="text-xs text-red-300">{error}</p> : null}
    </section>
  )
}
