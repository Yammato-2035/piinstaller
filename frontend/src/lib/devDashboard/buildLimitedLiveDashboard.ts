import { fetchApi } from '../../api'
import type { DashboardPayload, ModuleRow } from '../../pages/DevDashboardBody'
import { DANGEROUS_TEST_OPS } from './constants'
import type { DevDashboardCapabilities, DevDashboardLoadResult } from './types'
import { capabilitiesForSource } from './buildStandaloneDashboard'
import { buildStandaloneMetaPrompt } from './buildStandalonePrompt'

export function buildLimitedRuntimeGate(offlineReason: string): Record<string, unknown> {
  const tokenIssue =
    offlineReason === 'developer_token_required' || offlineReason === 'developer_capability_not_configured'
  return {
    status: tokenIssue ? 'yellow' : 'red',
    passed: false,
    checks: [
      { id: 'backend_api_reachable', ok: true, value: true },
      { id: 'dev_dashboard_api', ok: false, value: offlineReason },
    ],
    blockers: [offlineReason],
    backend_api_reachable: true,
    phase0_hint: tokenIssue
      ? 'Developer-Token im DCC speichern (gleicher Wert wie /etc/setuphelfer/dcc_developer.token)'
      : './scripts/check-runtime-deploy-gate.sh',
  }
}

export async function buildLimitedLiveDashboardResult(
  offlineReason: string,
  workspaceRoot?: string,
): Promise<DevDashboardLoadResult> {
  let versionPayload: Record<string, unknown> = {}
  try {
    const r = await fetchApi('/api/version', { cache: 'no-store' })
    if (r.ok) versionPayload = (await r.json()) as Record<string, unknown>
  } catch {
    /* ignore */
  }

  const projectVersion = String(versionPayload.project_version || versionPayload.version || 'unknown')
  const runtimePath = String(versionPayload.backend_runtime_path || '/opt/setuphelfer/backend')
  const runtimeGate = buildLimitedRuntimeGate(offlineReason)
  const safeTestMode = {
    mode: 'LOCKED',
    locked: true,
    reason: [offlineReason],
    blocked_operations: [...DANGEROUS_TEST_OPS],
    message_key: 'devDashboard.safeTestMode.locked',
  }

  const dashboard: DashboardPayload = {
    generated_at: new Date().toISOString(),
    backend_version: projectVersion,
    backend_running: true,
    install_profile: String(versionPayload.install_profile || 'unknown'),
    app_edition: String(versionPayload.app_edition || 'unknown'),
    release_gate_status: 'unknown',
    data_source: 'limited_live',
    standalone_mode: false,
    limited_live_mode: true,
    runtime: {
      backend_api_reachable: true,
      backend_version: projectVersion,
      backend_project_version: projectVersion,
      backend_runtime_path: runtimePath,
      install_profile: versionPayload.install_profile,
      app_edition: versionPayload.app_edition,
    },
    workspace: {
      workspace_path: workspaceRoot || runtimePath.replace(/\/backend$/, ''),
      workspace_version: null,
    },
    frontend: {
      frontend_runtime_source: 'limited_live',
    },
    consistency: { status: 'yellow', warnings: [offlineReason] },
    deploy_drift: {
      status: 'yellow',
      runtime_root: runtimePath.replace(/\/backend$/, ''),
      warnings: ['limited_live_deploy_drift_deferred'],
      suggested_actions: ['developer_token_then_deploy'],
      manifest_match: null,
    },
    runtime_gate: runtimeGate,
    safe_test_mode: safeTestMode,
    package_gate: { status: 'gray', warnings: ['limited_live_mode'] },
    tests_evidence: { status: 'gray', files: {}, warnings: ['limited_live_mode'] },
    roadmap: { areas: [], summary: { overall_status: 'limited_live' }, read_only: true },
    roadmap_data_source: 'limited_live',
    structure_health: {
      status: 'yellow',
      score: 50,
      critical_findings: [],
      warnings: [
        {
          severity: 'warning',
          id: offlineReason,
          message:
            offlineReason === 'developer_token_required'
              ? 'Local API erreichbar — Developer-Token im Browser fehlt oder ist ungültig'
              : offlineReason,
        },
      ],
      recommended_next_actions: [
        'Token im DCC speichern und prüfen',
        './scripts/check-runtime-deploy-gate.sh nach Token-Freigabe',
      ],
    },
    warnings: [offlineReason, 'limited_live_mode'],
    errors: [],
    updated_at: new Date().toISOString(),
  }

  const capabilities: DevDashboardCapabilities = {
    runtimeApi: false,
    workspaceAnalysis: false,
    structureHealth: true,
    roadmap: false,
    promptExport: true,
    runtimeTests: false,
  }

  return {
    source: 'limited_live',
    dashboard,
    modules: [] as ModuleRow[],
    evidenceIndex: null,
    apiReachable: false,
    localApiReachable: true,
    offlineReason,
    workspaceRoot: workspaceRoot || runtimePath.replace(/\/backend$/, ''),
    metaPrompt: buildStandaloneMetaPrompt(dashboard, workspaceRoot || 'limited_live'),
    capabilities,
  }
}
