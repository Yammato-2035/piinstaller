import React, { useEffect, useState } from 'react'

type ConnectivityStep = {
  id: string
  labelDe: string
  labelEn: string
  ok: boolean | null
}

type NetworkTelemetryStatusPanelProps = {
  language?: 'de' | 'en'
  apiBase?: string
}

export function NetworkTelemetryStatusPanel({
  language = 'de',
  apiBase = '/api/rescue',
}: NetworkTelemetryStatusPanelProps) {
  const de = language.startsWith('de')
  const [steps, setSteps] = useState<ConnectivityStep[]>([
    { id: 'lan_wlan', labelDe: 'LAN/WLAN', labelEn: 'LAN/WLAN', ok: null },
    { id: 'internet', labelDe: 'Internet (Default Route)', labelEn: 'Internet (default route)', ok: null },
    { id: 'dns', labelDe: 'DNS', labelEn: 'DNS', ok: null },
    { id: 'https', labelDe: 'HTTPS', labelEn: 'HTTPS', ok: null },
    { id: 'telemetry', labelDe: 'Telemetrie-Endpunkt', labelEn: 'Telemetry endpoint', ok: null },
  ])
  const [issueCodes, setIssueCodes] = useState<string[]>([])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const netRes = await fetch(`${apiBase}/network-connectivity-v2`)
        const telRes = await fetch(`${apiBase}/telemetry-connectivity-v1`)
        const net = netRes.ok ? await netRes.json() : null
        const tel = telRes.ok ? await telRes.json() : null
        if (cancelled) return
        const codes: string[] = [
          ...(net?.issue_codes ?? []),
          ...(tel?.issue_codes ?? []),
        ]
        setIssueCodes(codes)
        setSteps([
          {
            id: 'lan_wlan',
            labelDe: 'LAN/WLAN',
            labelEn: 'LAN/WLAN',
            ok: Boolean(net?.interfaces?.lan_link_up || net?.interfaces?.wifi_connected),
          },
          {
            id: 'internet',
            labelDe: 'Internet (Default Route)',
            labelEn: 'Internet (default route)',
            ok: net?.default_route ?? null,
          },
          { id: 'dns', labelDe: 'DNS', labelEn: 'DNS', ok: net?.dns_ok ?? null },
          { id: 'https', labelDe: 'HTTPS', labelEn: 'HTTPS', ok: net?.https_ok ?? null },
          {
            id: 'telemetry',
            labelDe: 'Telemetrie-Endpunkt',
            labelEn: 'Telemetry endpoint',
            ok: codes.some((c) => c.includes('telemetry') && c.includes('reachable')),
          },
        ])
      } catch {
        if (!cancelled) {
          setIssueCodes(['telemetry_endpoint_unreachable'])
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [apiBase])

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/80 p-4"
      data-testid="network-telemetry-status-panel"
    >
      <h2 className="text-lg font-semibold text-white mb-3">
        {de ? 'Netzwerk & Telemetrie' : 'Network & telemetry'}
      </h2>
      <ol className="space-y-2 text-sm">
        {steps.map((step) => (
          <li key={step.id} className="flex items-center justify-between text-slate-200">
            <span>{de ? step.labelDe : step.labelEn}</span>
            <span
              className={
                step.ok === true
                  ? 'text-emerald-400'
                  : step.ok === false
                    ? 'text-amber-400'
                    : 'text-slate-500'
              }
            >
              {step.ok === true ? 'OK' : step.ok === false ? (de ? 'Fehler' : 'Failed') : '…'}
            </span>
          </li>
        ))}
      </ol>
      {issueCodes.length > 0 && (
        <p className="mt-3 text-xs text-slate-400" data-testid="issue-codes">
          {de ? 'Codes: ' : 'Codes: '}
          {issueCodes.join(', ')}
        </p>
      )}
    </section>
  )
}
