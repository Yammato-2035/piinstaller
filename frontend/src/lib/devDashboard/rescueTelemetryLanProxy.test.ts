import { createElement } from 'react'
import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { DccCompactOverviewPanel } from '../../components/dev-dashboard/DccCompactOverviewPanel'
import { RescueTelemetryLanProxyToolbox } from '../../components/dev-dashboard/RescueTelemetryLanProxyToolbox'

describe('DccCompactOverviewPanel rescue telemetry LAN tile', () => {
  it('shows green when proxy running and lan health ok', () => {
    const html = renderToStaticMarkup(
      createElement(DccCompactOverviewPanel, {
        compact: {
          telemetry: { health_ok: true, ingest_enabled: true },
          rescue: {
            telemetry_lan_proxy: {
              running: true,
              lan_health_ok: true,
              backend_local_health_ok: true,
            },
          },
        },
      }),
    )
    expect(html).toContain('Rescue Telemetrie LAN')
    expect(html).toContain('LAN ok')
  })

  it('shows yellow when proxy not started', () => {
    const html = renderToStaticMarkup(
      createElement(DccCompactOverviewPanel, {
        compact: {
          telemetry: { health_ok: true, ingest_enabled: true },
          rescue: {
            telemetry_lan_proxy: {
              running: false,
              lan_health_ok: false,
              backend_local_health_ok: true,
            },
          },
        },
      }),
    )
    expect(html).toContain('nicht gestartet')
  })

  it('shows red when backend telemetry health failed', () => {
    const html = renderToStaticMarkup(
      createElement(DccCompactOverviewPanel, {
        compact: {
          telemetry: { health_ok: false, ingest_enabled: false },
          rescue: {
            telemetry_lan_proxy: {
              running: true,
              lan_health_ok: false,
            },
          },
        },
      }),
    )
    expect(html).toContain('Backend kaputt')
  })
})

describe('RescueTelemetryLanProxyToolbox', () => {
  it('renders operator commands and MSI URLs when DCC visible', () => {
    const html = renderToStaticMarkup(
      createElement(RescueTelemetryLanProxyToolbox, {
        dccVisible: true,
        telemetryLanProxy: {
          bind_host: '192.168.178.140',
          bind_port: 8001,
          health_url: 'http://192.168.178.140:8001/api/rescue/telemetry/health',
          ingest_url: 'http://192.168.178.140:8001/api/rescue/telemetry/v1/ingest',
        },
      }),
    )
    expect(html).toContain('data-testid="rescue-telemetry-lan-proxy-toolbox"')
    expect(html).toContain('setuphelfer-rescue-network-onboarding')
    expect(html).toContain('setuphelfer-rescue-telemetry-push')
    expect(html).toContain('status-rescue-telemetry-lan-proxy.sh')
    expect(html).toContain('stop-rescue-telemetry-lan-proxy.sh')
    expect(html).toContain('192.168.178.140:8001/api/rescue/telemetry/health')
  })

  it('hides toolbox when DCC not visible', () => {
    const html = renderToStaticMarkup(
      createElement(RescueTelemetryLanProxyToolbox, {
        dccVisible: false,
      }),
    )
    expect(html).toContain('data-testid="rescue-telemetry-lan-proxy-hidden"')
  })
})
