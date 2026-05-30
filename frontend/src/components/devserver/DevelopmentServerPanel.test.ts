import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import type { DevServerHealth, DevServerNode, DevServerSummary } from '../../api/devServerApi'
import { DevelopmentServerPanelView } from './DevelopmentServerPanelView'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('DevelopmentServerPanelView', () => {
  it('renders disabled state when dev server is off', () => {
    const html = renderToStaticMarkup(
      React.createElement(DevelopmentServerPanelView, {
        health: { enabled: false, mode: 'disabled', ssh_allowed: false },
        summary: { node_count: 0 },
        nodes: [],
        busyNode: null,
        error: null,
        onRunAction: vi.fn(),
      }),
    )
    expect(html).toContain('development-server-panel')
    expect(html).toContain('devDashboard.devServer.disabled')
    expect(html).toContain('dev-server-disabled-message')
  })

  it('renders node list when nodes exist', () => {
    const html = renderToStaticMarkup(
      React.createElement(DevelopmentServerPanelView, {
        health: { enabled: true, mode: 'local_lab', ssh_allowed: false },
        summary: { node_count: 1, online_count: 1 },
        nodes: [
          {
            node_id: 'node-lab-1',
            display_name: 'Test VM',
            node_kind: 'vm',
            status: 'online',
            ssh: { last_check_status: 'not_configured' },
          },
        ] as DevServerNode[],
        busyNode: null,
        error: null,
        onRunAction: vi.fn(),
      }),
    )
    expect(html).toContain('dev-server-node-list')
    expect(html).toContain('dev-server-node-node-lab-1')
    expect(html).toContain('Test VM')
  })

  it('disables SSH buttons when ssh_allowed is false', () => {
    const html = renderToStaticMarkup(
      React.createElement(DevelopmentServerPanelView, {
        health: { enabled: true, mode: 'local_lab', ssh_allowed: false } as DevServerHealth,
        summary: { node_count: 1 } as DevServerSummary,
        nodes: [{ node_id: 'n1', display_name: 'N1', status: 'online', ssh: {} }] as DevServerNode[],
        busyNode: null,
        error: null,
        onRunAction: vi.fn(),
      }),
    )
    expect(html).toContain('disabled')
    expect(html).toContain('dev-server-ssh-check-n1')
    expect(html).not.toContain('devDashboard.devServer.sshAction.backup')
    expect(html).not.toContain('devDashboard.devServer.sshAction.restore')
  })

  it('shows ssh disabled as safe state', () => {
    const html = renderToStaticMarkup(
      React.createElement(DevelopmentServerPanelView, {
        health: { enabled: true, mode: 'local_lab', ssh_allowed: false, public_uploads_allowed: false, storage_ok: true } as DevServerHealth,
        summary: { node_count: 1, latest_findings: [{ report_id: 'r1', node_id: 'n1', report_type: 'rescue' }] } as DevServerSummary,
        nodes: [{ node_id: 'n1', display_name: 'N1', status: 'online', ssh: {} }] as DevServerNode[],
        busyNode: null,
        error: null,
        onRunAction: vi.fn(),
      }),
    )
    expect(html).toContain('dev-server-ssh-safe')
    expect(html).toContain('devDashboard.devServer.sshDisabledSafe')
    expect(html).toContain('devDashboard.devServer.publicUploadsDisabledSafe')
    expect(html).toContain('dev-server-latest-findings')
  })
})
