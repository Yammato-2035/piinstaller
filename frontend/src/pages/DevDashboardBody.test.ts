import React from 'react'
import { describe, expect, it, vi, beforeAll } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { I18nextProvider } from 'react-i18next'
import i18n from '../i18n'
import { DevDashboardBody, type DashboardPayload, type ModuleRow } from './DevDashboardBody'

beforeAll(async () => {
  await i18n.changeLanguage('de')
})

function renderMarkup(el: React.ReactElement) {
  return renderToStaticMarkup(el)
}

const baseDashboard: DashboardPayload = {
  release_gate_status: 'rot',
  release_gate_path: 'docs/evidence/release-gates/backup_restore_release_gate.json',
  backend_version: '9.9.9-test',
  install_profile: 'dev',
  app_edition: 'test',
  active_backup_jobs: [],
  mount_summary: [],
  runtime: {
    backend_api_reachable: true,
    backend_version: '9.9.9-test',
    backend_project_version: '9.9.9-test',
    backend_runtime_path: '/opt/setuphelfer/backend',
  },
  workspace: {
    workspace_path: '/home/dev/piinstaller',
    workspace_version: '9.9.9-test',
    git_head: 'c0ffee',
    git_branch: 'main',
    git_dirty_count: 0,
    git_unpushed_count: null,
  },
  frontend: {
    frontend_build_version: '9.9.9-test',
    frontend_runtime_source: 'build',
    frontend_version_matches_backend: true,
  },
  consistency: {
    status: 'green',
    warnings: [],
    backend_workspace_match: true,
    frontend_backend_match: true,
  },
  deploy_drift: {
    status: 'green',
    workspace_root: '/home/dev/piinstaller',
    runtime_root: '/opt/setuphelfer',
    checked_files: [],
    matching_files_count: 8,
    differing_files_count: 0,
    missing_runtime_files: [],
    missing_workspace_files: [],
    warnings: [],
    suggested_actions: ['none'],
  },
}

const backupModule: ModuleRow = {
  id: 'backup-restore',
  title: 'Backup & Restore',
  area: 'backup',
  status: 'yellow',
  summary: 'Summary backup',
  next_steps: ['Step A'],
  blockers: ['B1'],
  evidence_files: ['docs/evidence/x.json'],
  prompt_files: ['docs/dev-dashboard/prompts/placeholder.md'],
  report_files: [],
  docs: ['docs/backup/BACKUP_PROFILES_DE.md', 'docs/missing-for-test.md'],
  faq: [],
  knowledge_base: [],
  i18n: [],
  tests: [],
  children: [
    { id: 'br-018', title: 'BR-018 Progress UI', area: 'backup', status: 'yellow', summary: 'UI-Teil' },
  ],
  artifact_status: [
    { path: 'docs/evidence/x.json', exists: false, kind: 'evidence' },
    { path: 'docs/backup/BACKUP_PROFILES_DE.md', exists: true, kind: 'doc' },
    { path: 'docs/missing-for-test.md', exists: false, kind: 'doc' },
  ],
}

const otherModule: ModuleRow = {
  id: 'other-yellow',
  title: 'Gelbes Modul nur Filtertest',
  area: 'backup',
  status: 'yellow',
  summary: 'Nur sichtbar wenn Filter passt',
  next_steps: [],
  blockers: [],
  evidence_files: [],
  prompt_files: [],
  report_files: [],
  docs: [],
  faq: [],
  knowledge_base: [],
  i18n: [],
  tests: [],
}

const redModule: ModuleRow = {
  id: 'red-only',
  title: 'Rotes Modul',
  area: 'backup',
  status: 'red',
  summary: 'Rot',
  next_steps: [],
  blockers: ['x'],
  evidence_files: [],
  prompt_files: [],
  report_files: [],
  docs: [],
  faq: [],
  knowledge_base: [],
  i18n: [],
  tests: [],
}

function wrap(
  bodyProps: Partial<React.ComponentProps<typeof DevDashboardBody>> &
    Pick<React.ComponentProps<typeof DevDashboardBody>, 'filter' | 'expanded' | 'selectedId'>,
) {
  const postActionSpy = bodyProps.postAction ?? vi.fn()
  const t = i18n.getFixedT('de')
  const el = React.createElement(
    I18nextProvider,
    { i18n },
    React.createElement(DevDashboardBody, {
      t,
      loading: bodyProps.loading ?? false,
      dashboard: bodyProps.dashboard ?? baseDashboard,
      modules: bodyProps.modules ?? [backupModule, otherModule, redModule],
      evidenceIndex: bodyProps.evidenceIndex ?? { buckets: [] },
      filter: bodyProps.filter,
      onFilterChange: bodyProps.onFilterChange ?? vi.fn(),
      expanded: bodyProps.expanded ?? {},
      onToggleModule: bodyProps.onToggleModule ?? vi.fn(),
      selectedId: bodyProps.selectedId ?? null,
      onSelectModuleId: bodyProps.onSelectModuleId ?? vi.fn(),
      onRefresh: bodyProps.onRefresh ?? vi.fn(),
      postAction: postActionSpy,
      apiBaseDisplay: bodyProps.apiBaseDisplay ?? 'http://127.0.0.1:8000',
    }),
  )
  return { html: renderMarkup(el as React.ReactElement), postAction: postActionSpy }
}

describe('DevDashboardBody', () => {
  it('rendert ohne Crash und zeigt Statuskarten (Gate, Version, Jobs)', () => {
    const { html } = wrap({ filter: 'all', expanded: {}, selectedId: 'backup-restore' })
    expect(html).toContain('data-testid="dev-dashboard-status-cards"')
    expect(html).toContain('data-testid="dev-dashboard-gate-value"')
    expect(html).toContain('rot')
    expect(html).toContain('data-testid="dev-dashboard-backend-version"')
    expect(html).toContain('9.9.9-test')
    expect(html).toContain('data-testid="dev-dashboard-job-count"')
    expect(html).toContain('Development Cockpit')
  })

  it('Filter Rot blendet nicht-rote Top-Level-Module aus', () => {
    const { html } = wrap({ filter: 'red', expanded: {}, selectedId: 'red-only' })
    expect(html).toContain('data-testid="dev-dashboard-mod-red-only"')
    expect(html).not.toContain('data-testid="dev-dashboard-mod-backup-restore"')
    expect(html).not.toContain('Gelbes Modul nur Filtertest')
  })

  it('aufgeklapptes Modul zeigt Kinder (BR-018)', () => {
    const { html } = wrap({ filter: 'all', expanded: { 'backup-restore': true }, selectedId: 'backup-restore' })
    expect(html).toContain('data-testid="dev-dashboard-mod-expanded-backup-restore"')
    expect(html).toContain('BR-018 Progress UI')
  })

  it('Detailpanel listet Evidence/Prompts und fehlende Artefakte ohne Exception', () => {
    const { html } = wrap({ filter: 'all', expanded: {}, selectedId: 'backup-restore' })
    expect(html).toContain('data-testid="dev-dashboard-detail-panel"')
    expect(html).toContain('data-testid="dev-dashboard-artifact-evidence"')
    expect(html).toContain('data-testid="dev-dashboard-artifact-prompts"')
    expect(html).toContain('docs/evidence/x.json')
    expect(html).toContain('docs/missing-for-test.md')
    expect(html).toContain('text-slate-500')
  })

  it('zeigt Runtime-vs-Workspace-Karte mit Ampel', () => {
    const { html } = wrap({ filter: 'all', expanded: {}, selectedId: 'backup-restore' })
    expect(html).toContain('data-testid="dev-dashboard-runtime-workspace-card"')
    expect(html).toContain('Runtime vs. Workspace')
    expect(html).toContain('Grün')
  })

  it('warnt bei veraltetem Frontend-Build (Ampel Gelb)', () => {
    const dash: DashboardPayload = {
      ...baseDashboard,
      frontend: {
        frontend_build_version: '1.5.0.0',
        frontend_runtime_source: 'build',
        frontend_version_matches_backend: false,
      },
      consistency: {
        status: 'yellow',
        warnings: ['frontend_build_outdated'],
        backend_workspace_match: true,
        frontend_backend_match: false,
      },
    }
    const { html } = wrap({ filter: 'all', expanded: {}, selectedId: 'backup-restore', dashboard: dash })
    expect(html).toContain('Gelb')
    expect(html).toContain('Frontend-Build weicht')
  })

  it('zeigt Deploy-Drift-Karte mit Vorschlägen', () => {
    const dash: DashboardPayload = {
      ...baseDashboard,
      deploy_drift: {
        status: 'yellow',
        workspace_root: '/ws',
        runtime_root: '/opt/setuphelfer',
        checked_files: [
          {
            relative_path: 'frontend/package.json',
            matches: false,
            reason: 'sha256_mismatch',
          },
        ],
        matching_files_count: 0,
        differing_files_count: 1,
        missing_runtime_files: [],
        missing_workspace_files: [],
        warnings: [],
        suggested_actions: ['rebuild_frontend'],
      },
    }
    const { html } = wrap({ filter: 'all', expanded: {}, selectedId: 'backup-restore', dashboard: dash })
    expect(html).toContain('data-testid="dev-dashboard-deploy-drift-card"')
    expect(html).toContain('Deploy-Drift')
    expect(html).toContain('Frontend neu bauen')
  })

  it('Restart-Primary ist disabled; Probes rufen postAction nur bei Klick (hier nicht geklickt)', () => {
    const postAction = vi.fn()
    const { html } = wrap({ filter: 'all', expanded: {}, selectedId: 'backup-restore', postAction })
    expect(html).toContain('data-testid="dev-dashboard-restart-disabled"')
    expect(html).toContain('disabled')
    expect(postAction).not.toHaveBeenCalled()
  })
})
