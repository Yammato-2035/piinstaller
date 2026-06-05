import { createElement } from 'react'
import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { DccCompactOverviewPanel } from '../../components/dev-dashboard/DccCompactOverviewPanel'

describe('DccCompactOverviewPanel', () => {
  it('renders compact tiles without raw dump by default', () => {
    const html = renderToStaticMarkup(
      createElement(DccCompactOverviewPanel, {
        compact: {
          install_profile: 'release',
          dcc_visible: true,
          deploy_drift_status: 'green',
          telemetry: { health_ok: true, ingest_enabled: true },
          rescue: { iso_uefi_validated: true, usb_mount_detected: true, target_boot_validated: false },
          blockers: ['RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET'],
          next_operator_action: 'USB boot on MSI laptop',
        },
      }),
    )
    expect(html).toContain('data-testid="dcc-compact-overview"')
    expect(html).toContain('UEFI ok')
    expect(html).toContain('ingest on')
    expect(html).not.toContain('data-testid="dcc-compact-raw-details"')
  })

  it('shows raw details only when provided', () => {
    const html = renderToStaticMarkup(
      createElement(DccCompactOverviewPanel, {
        compact: { install_profile: 'release' },
        rawDetailsJson: '{"compact":true}',
      }),
    )
    expect(html).toContain('data-testid="dcc-compact-raw-details"')
  })
})
