import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { StandaloneModeBanner } from './StandaloneModeBanner'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('StandaloneModeBanner', () => {
  it('shows hanging backend title when timeout reason is present', () => {
    const html = renderToStaticMarkup(
      React.createElement(StandaloneModeBanner, {
        source: 'snapshot',
        apiReachable: false,
        capabilities: {
          runtimeApi: false,
          workspaceAnalysis: true,
          structureHealth: true,
          roadmap: true,
          promptExport: true,
          runtimeTests: false,
        },
        offlineReason: 'backend_hanging_timeout',
      }),
    )
    expect(html).toContain('devDashboard.standalone.backendHangTitle')
    expect(html).toContain('devDashboard.standalone.detectedState')
  })
})
