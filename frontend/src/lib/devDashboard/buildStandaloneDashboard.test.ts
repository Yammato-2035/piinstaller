import { describe, expect, it } from 'vitest'
import {
  buildBlockedRuntimeGate,
  buildStandaloneDashboardFromScan,
  capabilitiesForSource,
} from './buildStandaloneDashboard'
import { buildStandaloneMetaPrompt } from './buildStandalonePrompt'
import type { WorkspaceScanResult } from './types'

const minimalScan: WorkspaceScanResult = {
  workspace_root: '/home/dev/piinstaller',
  version: { project_version: '1.7.1', release_stage: 'internal_testing' },
  frontend_package: { version: '1.7.1' },
  git: { git_head: 'abc123', git_dirty_count: 2 },
  evidence_files: {
    'backup_restore_release_gate.json': {
      path: 'docs/evidence/release-gates/backup_restore_release_gate.json',
      exists: true,
      status: 'ok',
      data: { ampel: 'rot', evidence_complete: false },
    },
  },
  matrix: { exists: true, lines: 10 },
  modules: [{ id: 'backup-restore', title: 'Backup', status: 'red', summary: 'blocked' }],
}

describe('buildStandaloneDashboard', () => {
  it('blocks runtime gate when offline', () => {
    const dash = buildStandaloneDashboardFromScan(minimalScan, 'standalone_workspace', {
      offlineReason: 'backend_api_unreachable',
    })
    const rg = dash?.runtime_gate as Record<string, unknown>
    expect(rg.passed).toBe(false)
    expect(rg.status).toBe('red')
    expect((rg.blockers as string[]) || []).toContain('backend_api_unreachable')
  })

  it('locks safe test mode', () => {
    const dash = buildStandaloneDashboardFromScan(minimalScan, 'standalone_workspace')
    const stm = dash?.safe_test_mode as Record<string, unknown>
    expect(stm.mode).toBe('LOCKED')
    expect(stm.locked).toBe(true)
    expect(stm.blocked_operations).toContain('backup')
    expect(stm.blocked_operations).toContain('hardware_tests')
  })

  it('never marks runtime api reachable in standalone', () => {
    const dash = buildStandaloneDashboardFromScan(minimalScan, 'standalone_workspace')
    const rt = dash?.runtime as Record<string, unknown>
    expect(rt.backend_api_reachable).toBe(false)
    expect(dash?.standalone_mode).toBe(true)
  })

  it('builds roadmap from scan modules', () => {
    const dash = buildStandaloneDashboardFromScan(minimalScan, 'standalone_workspace')
    const roadmap = dash?.roadmap as Record<string, unknown>
    const tabs = roadmap.tabs as Record<string, unknown[]>
    expect((tabs.blocked || []).length).toBeGreaterThan(0)
  })

  it('capabilities disable runtime tests outside runtime_api', () => {
    expect(capabilitiesForSource('runtime_api').runtimeTests).toBe(true)
    expect(capabilitiesForSource('standalone_workspace').runtimeTests).toBe(false)
    expect(capabilitiesForSource('snapshot').runtimeTests).toBe(false)
  })

  it('meta prompt mentions standalone and forbids backup', () => {
    const dash = buildStandaloneDashboardFromScan(minimalScan, 'standalone_workspace')
    const prompt = buildStandaloneMetaPrompt(dash, minimalScan.workspace_root)
    expect(prompt).toContain('STANDALONE')
    expect(prompt).toContain('backup')
    expect(prompt).toContain('runtime_gate_passed: false')
  })

  it('blocked runtime gate is never green', () => {
    const rg = buildBlockedRuntimeGate('backend_api_unreachable')
    expect(rg.passed).toBe(false)
    expect(rg.status).not.toBe('green')
  })
})
