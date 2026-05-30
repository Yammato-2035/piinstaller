import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import type { ControlCenterSummary } from '../../api/devDashboardApi'
import { ControlCenterOverviewHeader } from './ControlCenterOverviewHeader'
import { ControlCenterSectionTabs } from './ControlCenterSectionTabs'
import { DocumentationDiagnosticsCard } from './DocumentationDiagnosticsCard'
import { RescueDeveloperPipelineCard } from './RescueDeveloperPipelineCard'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}))

const sampleSummary: ControlCenterSummary = {
  runtime: {
    runtime_gate_passed: true,
    runtime_gate_status: 'green',
    deploy_drift_status: 'green',
    version: '1.7.2',
    release_gate_status: 'rot',
  },
  roadmap: { overall_status: 'partial_green', status: 'available' },
  dev_server: {
    enabled: true,
    mode: 'local_lab',
    ssh_allowed: false,
    public_uploads_allowed: false,
    agent_status: 'report_available',
  },
  documentation: {
    docs_total: 100,
    faq_total: 10,
    kb_total: 20,
    evidence_total: 30,
    translation_pairs: { complete: 5, missing_de: [], missing_en: [] },
  },
  diagnostics: { catalog_available: true, code_count: 30, test_count: 5, kb_count: 2 },
  rescue_developer: {
    items: [
      { id: 'dev_server_mvp', label: 'Dev Server MVP', status: 'green' },
      { id: 'rescue_iso_dry_build', label: 'ISO Dry-Build', status: 'pending' },
    ],
    next_step: 'RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD',
  },
  next_prompts: [{ id: 'p1', title: 'Next prompt', status: 'recommended' }],
}

describe('ControlCenterOverview', () => {
  it('renders overview header with status grid', () => {
    const html = renderToStaticMarkup(
      React.createElement(ControlCenterOverviewHeader, { summary: sampleSummary, apiReachable: true }),
    )
    expect(html).toContain('control-center-overview-header')
    expect(html).toContain('control-center-status-grid')
    expect(html).toContain('1.7.2')
  })

  it('renders section tabs including roadmap and telemetry', () => {
    const html = renderToStaticMarkup(
      React.createElement(ControlCenterSectionTabs, {
        active: 'overview',
        onChange: vi.fn(),
        t: (k: string) => k,
      }),
    )
    expect(html).toContain('control-center-tab-roadmap')
    expect(html).toContain('control-center-tab-telemetry')
    expect(html).toContain('control-center-tab-documentation')
  })

  it('renders documentation and diagnostics card', () => {
    const html = renderToStaticMarkup(
      React.createElement(DocumentationDiagnosticsCard, { summary: sampleSummary }),
    )
    expect(html).toContain('documentation-diagnostics-card')
    expect(html).toContain('documentation-stats')
    expect(html).toContain('diagnostics-stats')
  })

  it('renders rescue pipeline without ISO green', () => {
    const html = renderToStaticMarkup(
      React.createElement(RescueDeveloperPipelineCard, { summary: sampleSummary }),
    )
    expect(html).toContain('rescue-developer-pipeline-card')
    expect(html).toContain('rescue-pipeline-rescue_iso_dry_build')
    expect(html).toContain('pending')
  })
})
