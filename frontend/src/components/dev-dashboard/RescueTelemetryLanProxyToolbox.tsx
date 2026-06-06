import React from 'react'
import { useTranslation } from 'react-i18next'
import { ClipboardCopy, Radio } from 'lucide-react'
import type { DccCompactRescueTelemetryLanProxy } from '../../lib/devDashboard/dccCompactStatus'

export type RescueTelemetryLanProxyToolboxProps = {
  telemetryLanProxy?: DccCompactRescueTelemetryLanProxy | null
  dccVisible?: boolean
}

const REPO_ROOT = '/home/volker/piinstaller'

export const RescueTelemetryLanProxyToolbox: React.FC<RescueTelemetryLanProxyToolboxProps> = ({
  telemetryLanProxy,
  dccVisible = false,
}) => {
  const { t } = useTranslation()
  const bindHost = telemetryLanProxy?.bind_host ?? '<LAN-IP>'
  const startCmd = `cd ${REPO_ROOT}\nSETUPHELFER_RESCUE_TELEMETRY_BIND=${bindHost} ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh`
  const statusCmd = `./scripts/rescue-live/status-rescue-telemetry-lan-proxy.sh`
  const stopCmd = `./scripts/rescue-live/stop-rescue-telemetry-lan-proxy.sh`
  const healthUrl =
    telemetryLanProxy?.health_url ?? `http://${bindHost}:8001/api/rescue/telemetry/health`
  const ingestUrl =
    telemetryLanProxy?.ingest_url ?? `http://${bindHost}:8001/api/rescue/telemetry/v1/ingest`

  const copyText = async (text: string) => {
    await navigator.clipboard.writeText(text)
  }

  if (!dccVisible) {
    return (
      <section
        className="rounded-xl border border-slate-700/60 bg-slate-950/40 p-4"
        data-testid="rescue-telemetry-lan-proxy-hidden"
      >
        <p className="text-xs text-slate-400">
          {t(
            'devDashboard.rescueTelemetryLan.hidden',
            'Rescue Telemetrie LAN-Proxy nur mit sichtbarem DCC.',
          )}
        </p>
      </section>
    )
  }

  return (
    <section
      className="rounded-xl border border-cyan-800/40 bg-cyan-950/10 p-4"
      data-testid="rescue-telemetry-lan-proxy-toolbox"
    >
      <div className="flex items-center gap-2">
        <Radio className="h-4 w-4 text-cyan-300" />
        <h2 className="text-sm font-semibold text-white">
          {t('devDashboard.rescueTelemetryLan.title', 'Rescue Telemetrie LAN-Proxy (MSI)')}
        </h2>
      </div>
      <p className="mt-1 text-xs text-slate-400">
        {t(
          'devDashboard.rescueTelemetryLan.subtitle',
          'Nur /api/rescue/telemetry/health und /v1/ingest — kein volles Backend im LAN.',
        )}
      </p>

      <div className="mt-3 grid gap-2 text-xs md:grid-cols-2">
        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">{t('devDashboard.rescueTelemetryLan.status', 'Status')}</div>
          <ul className="mt-2 space-y-1 font-mono text-slate-300">
            <li>running: {String(telemetryLanProxy?.running ?? false)}</li>
            <li>backend_local_health_ok: {String(telemetryLanProxy?.backend_local_health_ok ?? false)}</li>
            <li>lan_health_ok: {String(telemetryLanProxy?.lan_health_ok ?? false)}</li>
            <li>bind: {bindHost}:{telemetryLanProxy?.bind_port ?? 8001}</li>
          </ul>
          {telemetryLanProxy?.blockers?.length ? (
            <p className="mt-2 text-amber-300 font-mono">blockers: {telemetryLanProxy.blockers.join(', ')}</p>
          ) : null}
        </div>
        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">MSI-Test-URLs</div>
          <p className="mt-2 break-all font-mono text-slate-300" data-testid="rescue-telemetry-lan-health-url">
            {healthUrl}
          </p>
          <p className="mt-1 break-all font-mono text-slate-400" data-testid="rescue-telemetry-lan-ingest-url">
            {ingestUrl}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded border border-slate-700 bg-slate-950/50 p-3">
        <div className="text-xs font-semibold text-cyan-200">
          {t('devDashboard.rescueTelemetryLan.operatorCommands', 'Operator-Befehle')}
        </div>
        <pre className="mt-2 overflow-x-auto text-[11px] text-slate-200" data-testid="rescue-telemetry-lan-start-cmd">
          {startCmd}
        </pre>
        <pre className="mt-2 overflow-x-auto text-[11px] text-slate-300" data-testid="rescue-telemetry-lan-status-cmd">
          {statusCmd}
        </pre>
        <pre className="mt-2 overflow-x-auto text-[11px] text-slate-300" data-testid="rescue-telemetry-lan-stop-cmd">
          {stopCmd}
        </pre>
        <button
          type="button"
          className="mt-2 inline-flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-[11px] text-slate-200"
          onClick={() => void copyText(startCmd)}
        >
          <ClipboardCopy className="h-3 w-3" />
          {t('common.copy', 'Kopieren')}
        </button>
      </div>

      <p className="mt-3 text-[10px] text-slate-500">
        {telemetryLanProxy?.next_step ??
          t(
            'devDashboard.rescueTelemetryLan.nextStep',
            'Proxy starten, dann MSI Live-System curl auf health-url.',
          )}
      </p>
    </section>
  )
}
