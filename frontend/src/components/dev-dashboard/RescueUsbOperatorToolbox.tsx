import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, ClipboardCopy, HardDrive, ShieldAlert } from 'lucide-react'
import { fetchDccApi } from '../../lib/devDashboard/dccDeveloperToken'
import {
  RESCUE_USB_CONFIRMATION_PHRASE,
  RESCUE_USB_REQUIRED_CONFIRMATIONS,
  type RescueUsbCandidate,
  type RescueUsbCandidatesResponse,
  type RescueUsbConfirmationKey,
  type RescueUsbSelectionRecord,
  canSubmitRescueUsbSelection,
  rescueUsbToolboxVisible,
} from '../../lib/devDashboard/rescueUsbOperatorToolbox'

type CompactUsbOperator = {
  usb_detected?: boolean
  old_rescue_stick_detected?: boolean
  operator_selection_present?: boolean
  operator_selection_device?: string | null
  destructive_write_allowed?: boolean
  dd_execution_allowed?: boolean
  blockers?: string[]
  next_step?: string
}

export type RescueUsbOperatorToolboxProps = {
  compactUsbOperator?: CompactUsbOperator | null
  developerCapabilityValid?: boolean
  dccVisible?: boolean
}

const CHECKBOX_LABELS: Record<RescueUsbConfirmationKey, string> = {
  confirm_correct_usb: 'Ich bestätige, dass dies der richtige USB-Stick ist.',
  confirm_data_destruction: 'Ich bestätige, dass alle Daten auf diesem USB-Stick überschrieben werden dürfen.',
  confirm_not_system_or_backup:
    'Ich bestätige, dass /dev/sda, /dev/nvme* und Backup-Datenträger nicht Ziel sind.',
  confirm_old_stick_replace:
    'Ich bestätige, dass der vorhandene Stick alt ist und durch die aktuelle ISO ersetzt werden soll.',
  confirm_iso_sha256_and_device: 'Ich bestätige ISO-SHA256 und Zielgerät.',
}

export const RescueUsbOperatorToolbox: React.FC<RescueUsbOperatorToolboxProps> = ({
  compactUsbOperator,
  developerCapabilityValid = false,
  dccVisible = false,
}) => {
  const { t } = useTranslation()
  const visible = rescueUsbToolboxVisible({ developerCapabilityValid, dccVisible })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [candidates, setCandidates] = useState<RescueUsbCandidatesResponse | null>(null)
  const [selection, setSelection] = useState<RescueUsbSelectionRecord | null>(null)
  const [selectedDevice, setSelectedDevice] = useState('')
  const [confirmationPhrase, setConfirmationPhrase] = useState('')
  const [confirmations, setConfirmations] = useState<Partial<Record<RescueUsbConfirmationKey, boolean>>>({})

  const load = useCallback(async () => {
    if (!visible) return
    setLoading(true)
    setError(null)
    try {
      const [candRes, selRes] = await Promise.all([
        fetchDccApi('/api/dev-dashboard/rescue-usb/candidates'),
        fetchDccApi('/api/dev-dashboard/rescue-usb/selection'),
      ])
      if (!candRes.ok) throw new Error(`candidates HTTP ${candRes.status}`)
      if (!selRes.ok) throw new Error(`selection HTTP ${selRes.status}`)
      const candBody = (await candRes.json()) as RescueUsbCandidatesResponse
      const selBody = (await selRes.json()) as { selection?: RescueUsbSelectionRecord | null }
      setCandidates(candBody)
      setSelection(selBody.selection ?? null)
      if (selBody.selection?.selected_device) {
        setSelectedDevice(selBody.selection.selected_device)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed')
    } finally {
      setLoading(false)
    }
  }, [visible])

  useEffect(() => {
    void load()
  }, [load])

  const selectedCandidate = useMemo(
    () => (candidates?.devices ?? []).find((d) => d.device === selectedDevice) ?? null,
    [candidates, selectedDevice],
  )

  const canSubmit = canSubmitRescueUsbSelection({
    selectedDevice,
    confirmations,
    confirmationPhrase,
    candidate: selectedCandidate,
  })

  const onSubmit = async () => {
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetchDccApi('/api/dev-dashboard/rescue-usb/selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_device: selectedDevice,
          operator_confirmations: confirmations,
          confirmation_phrase: confirmationPhrase,
        }),
      })
      const body = (await res.json()) as { selection?: RescueUsbSelectionRecord; write_allowed?: boolean }
      if (!res.ok) throw new Error(`selection HTTP ${res.status}`)
      setSelection(body.selection ?? null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'submit failed')
    } finally {
      setLoading(false)
    }
  }

  const copyCommand = async () => {
    const cmd = selection?.generated_dd_command
    if (!cmd) return
    await navigator.clipboard.writeText(cmd)
  }

  if (!visible) {
    return (
      <section
        className="rounded-xl border border-slate-700/60 bg-slate-950/40 p-4"
        data-testid="rescue-usb-toolbox-hidden"
      >
        <p className="text-xs text-slate-400">
          {t(
            'devDashboard.rescueUsb.toolboxHidden',
            'Developer Toolbox (USB-Auswahl) nur mit gültiger Developer Capability sichtbar.',
          )}
        </p>
      </section>
    )
  }

  return (
    <section
      className="rounded-xl border border-amber-800/40 bg-amber-950/10 p-4"
      data-testid="rescue-usb-operator-toolbox"
    >
      <div className="flex items-center gap-2">
        <HardDrive className="h-4 w-4 text-amber-300" />
        <h2 className="text-sm font-semibold text-white">
          {t('devDashboard.rescueUsb.toolboxTitle', 'Developer Toolbox — USB Operator Selection')}
        </h2>
      </div>
      <p className="mt-1 text-xs text-slate-400">
        {t(
          'devDashboard.rescueUsb.readOnlyNotice',
          'Read-only Geräteerkennung. Kein automatisches dd — nur Auswahl, Freigabe-Evidence und Operator-Befehl.',
        )}
      </p>

      <div className="mt-3 grid gap-2 text-xs md:grid-cols-2">
        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">{t('devDashboard.rescueUsb.status', 'Gate-Status')}</div>
          <ul className="mt-2 space-y-1 font-mono text-slate-300">
            <li>usb_detected: {String(compactUsbOperator?.usb_detected ?? false)}</li>
            <li>old_rescue_stick: {String(compactUsbOperator?.old_rescue_stick_detected ?? false)}</li>
            <li>selection: {compactUsbOperator?.operator_selection_present ? 'present' : 'missing'}</li>
            <li>destructive_write_allowed: {String(compactUsbOperator?.destructive_write_allowed ?? false)}</li>
          </ul>
          {compactUsbOperator?.blockers?.length ? (
            <p className="mt-2 text-amber-300 font-mono">blockers: {compactUsbOperator.blockers.join(', ')}</p>
          ) : null}
        </div>
        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">ISO</div>
          <p className="mt-2 break-all font-mono text-slate-300">{candidates?.iso_path ?? '—'}</p>
          <p className="mt-1 break-all font-mono text-slate-400">{candidates?.iso_sha256 ?? '—'}</p>
        </div>
      </div>

      {loading ? <p className="mt-3 text-xs text-slate-400">{t('common.loading', 'Laden…')}</p> : null}
      {error ? <p className="mt-3 text-xs text-red-300">{error}</p> : null}

      <div className="mt-4 space-y-2">
        {(candidates?.devices ?? []).map((device: RescueUsbCandidate) => (
          <label
            key={device.device}
            className={`block rounded border p-3 cursor-pointer ${
              device.selectable ? 'border-slate-600 hover:border-amber-700/60' : 'border-red-900/50 opacity-70'
            }`}
            data-testid={`rescue-usb-device-${device.name}`}
          >
            <div className="flex items-start gap-2">
              <input
                type="radio"
                name="rescue-usb-device"
                value={device.device}
                checked={selectedDevice === device.device}
                disabled={!device.selectable}
                onChange={() => setSelectedDevice(device.device)}
              />
              <div className="min-w-0 flex-1 text-xs font-mono text-slate-200">
                <div className="font-semibold text-white">{device.device}</div>
                <div>
                  size={device.size} model={device.model ?? '—'} serial={device.serial ?? '—'} tran=
                  {device.transport ?? '—'}
                </div>
                <div>mounts={(device.mountpoints ?? []).join(', ') || '—'}</div>
                <div>fstypes={(device.fstypes ?? []).join(', ') || '—'}</div>
                {device.setuphelfer_rescue_detected ? (
                  <div className="mt-1 flex items-center gap-1 text-amber-300">
                    <AlertTriangle className="h-3 w-3" />
                    {device.setuphelfer_rescue_warning}
                  </div>
                ) : null}
                {!device.selectable ? (
                  <div className="mt-1 text-red-300">blocked: {device.blocked_reason}</div>
                ) : null}
              </div>
            </div>
          </label>
        ))}
      </div>

      <div className="mt-4 space-y-2">
        {RESCUE_USB_REQUIRED_CONFIRMATIONS.map((key) => (
          <label key={key} className="flex items-start gap-2 text-xs text-slate-200">
            <input
              type="checkbox"
              checked={Boolean(confirmations[key])}
              onChange={(e) => setConfirmations((prev) => ({ ...prev, [key]: e.target.checked }))}
            />
            <span>{CHECKBOX_LABELS[key]}</span>
          </label>
        ))}
      </div>

      <div className="mt-4">
        <label className="block text-xs text-slate-300">
          {t('devDashboard.rescueUsb.phraseLabel', 'Textbestätigung (exakt):')}
          <input
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 font-mono text-xs text-white"
            value={confirmationPhrase}
            onChange={(e) => setConfirmationPhrase(e.target.value)}
            placeholder={RESCUE_USB_CONFIRMATION_PHRASE}
            data-testid="rescue-usb-confirmation-phrase"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded bg-amber-700/80 px-3 py-1.5 text-xs text-white disabled:opacity-40"
          disabled={!canSubmit || loading}
          onClick={() => void onSubmit()}
          data-testid="rescue-usb-submit-selection"
        >
          {t('devDashboard.rescueUsb.saveSelection', 'Auswahl speichern / Evidence erzeugen')}
        </button>
        <button type="button" className="rounded border border-slate-600 px-3 py-1.5 text-xs text-slate-200" onClick={() => void load()}>
          {t('common.refresh', 'Aktualisieren')}
        </button>
      </div>

      {selection?.generated_dd_command ? (
        <div className="mt-4 rounded border border-emerald-800/40 bg-emerald-950/20 p-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-200">
            <ShieldAlert className="h-4 w-4" />
            {t('devDashboard.rescueUsb.operatorCommand', 'Operator-Befehl (manuell im Terminal)')}
          </div>
          <pre className="mt-2 overflow-x-auto text-[11px] text-slate-200">{selection.generated_dd_command}</pre>
          <button
            type="button"
            className="mt-2 inline-flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-[11px] text-slate-200"
            onClick={() => void copyCommand()}
          >
            <ClipboardCopy className="h-3 w-3" />
            {t('common.copy', 'Kopieren')}
          </button>
        </div>
      ) : null}

      <p className="mt-3 text-[10px] text-slate-500">
        {compactUsbOperator?.next_step ??
          t('devDashboard.rescueUsb.nextStep', 'Stick auswählen, bestätigen, dann Befehl manuell ausführen.')}
      </p>
    </section>
  )
}
