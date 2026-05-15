import type { DashboardPayload, ModuleRow } from '../../pages/DevDashboardBody'
import { DANGEROUS_TEST_OPS } from './constants'
import type { DevDashboardCapabilities, DevDashboardDataSource, WorkspaceScanResult } from './types'

function normalizeAmpel(raw: string | undefined): string {
  const s = String(raw || '').toLowerCase()
  const map: Record<string, string> = {
    grün: 'green',
    gruen: 'green',
    green: 'green',
    gelb: 'yellow',
    yellow: 'yellow',
    rot: 'red',
    red: 'red',
    gray: 'gray',
    grey: 'gray',
    blocked: 'red',
    failed: 'red',
  }
  return map[s] || 'unknown'
}

function parseMatrixRows(text: string): Array<Record<string, unknown>> {
  const items: Array<Record<string, unknown>> = []
  const rowRe = /^\|\s*\*\*(.+?)\*\*\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|/
  for (const line of text.split('\n')) {
    const m = rowRe.exec(line.trim())
    if (!m) continue
    const ampel = normalizeAmpel(m[2].trim())
    let category = 'planned'
    if (ampel === 'green') category = 'created'
    else if (ampel === 'yellow') category = 'in_progress'
    else if (ampel === 'red' || ampel === 'unknown') category = 'blocked'
    items.push({
      title: m[1].trim(),
      status: ampel,
      category,
      source: 'docs/roadmap/STATUS_MATRIX.md',
      summary: m[3].trim().slice(0, 400),
      evidence_refs: [],
    })
  }
  return items
}

function buildRoadmapFromScan(scan: WorkspaceScanResult, matrixText?: string): Record<string, unknown> {
  const tabs: Record<string, Array<Record<string, unknown>>> = {
    created: [],
    in_progress: [],
    planned: [],
    blocked: [],
  }
  if (matrixText) {
    for (const it of parseMatrixRows(matrixText)) {
      const cat = String(it.category || 'planned')
      if (tabs[cat]) tabs[cat].push(it)
      else tabs.planned.push(it)
    }
  }
  for (const mod of scan.modules || []) {
    const st = normalizeAmpel(String(mod.status || 'gray'))
    let category = 'in_progress'
    if (st === 'green') category = 'created'
    else if (st === 'red') category = 'blocked'
    else if (st === 'yellow') category = 'in_progress'
    else category = 'planned'
    tabs[category].push({
      title: String(mod.title || mod.id || 'module'),
      status: st,
      category,
      source: String(mod.source || ''),
      summary: String(mod.summary || '').slice(0, 400),
      evidence_refs: Array.isArray(mod.evidence_files) ? mod.evidence_files : [],
    })
  }
  return {
    tabs,
    counts: Object.fromEntries(Object.entries(tabs).map(([k, v]) => [k, v.length])),
    changed_to_green: {
      available: false,
      message: 'Keine belastbare Änderungshistorie (Standalone)',
      items: [],
    },
    green_without_evidence: [],
    missing_matrix_entries: scan.matrix?.exists ? [] : ['docs/roadmap/STATUS_MATRIX.md'],
    warnings: scan.warnings || [],
  }
}

function buildTestsEvidence(scan: WorkspaceScanResult): Record<string, unknown> {
  const files: Record<string, unknown> = {}
  let overall = 'green'
  for (const [name, meta] of Object.entries(scan.evidence_files || {})) {
    const data = meta.data as Record<string, unknown> | undefined
    const ampel = data ? normalizeAmpel(String(data.ampel || data.status || '')) : 'unknown'
    files[name] = {
      path: meta.path || `docs/evidence/release-gates/${name}`,
      exists: meta.exists === true,
      status: meta.status || (meta.exists ? 'ok' : 'missing'),
      ampel,
      evidence_complete: data?.evidence_complete,
    }
    if (ampel === 'red') overall = 'red'
    else if (ampel === 'yellow' && overall === 'green') overall = 'yellow'
  }
  return { status: overall, files, warnings: [] }
}

function buildStructureHealth(
  scan: WorkspaceScanResult,
  runtimeGate: Record<string, unknown>,
): Record<string, unknown> {
  const critical: Array<Record<string, unknown>> = []
  const warnings: Array<Record<string, unknown>> = []
  if (!runtimeGate.passed) {
    critical.push({
      severity: 'critical',
      id: 'runtime_gate_failed',
      message: 'Runtime-Gate nicht bestanden — Phase-0 blockiert (API offline)',
      blockers: runtimeGate.blockers,
    })
  }
  if ((scan.git?.git_dirty_count as number | null) != null && Number(scan.git?.git_dirty_count) > 0) {
    warnings.push({
      severity: 'warning',
      id: 'workspace_dirty',
      message: `Workspace dirty (${scan.git?.git_dirty_count} Dateien)`,
    })
  }
  for (const [, meta] of Object.entries(scan.evidence_files || {})) {
    const data = meta.data as Record<string, unknown> | undefined
    if (data && data.evidence_complete === false) {
      warnings.push({
        severity: 'warning',
        id: 'evidence_incomplete',
        message: `Evidence unvollständig: ${meta.path}`,
      })
    }
  }
  let score = 100 - critical.length * 25 - warnings.length * 8
  score = Math.max(0, Math.min(100, score))
  const status = critical.length ? 'red' : warnings.length ? 'yellow' : 'green'
  return {
    status,
    score,
    critical_findings: critical,
    warnings,
    recommended_next_actions: [
      './scripts/check-runtime-deploy-gate.sh ausführen, sobald setuphelfer-backend läuft',
    ],
    git_hygiene: {
      dirty_count: scan.git?.git_dirty_count ?? null,
      untracked_count: null,
      forbidden_matches: [],
      add_all_risk: false,
    },
    docs_consistency: { matrix_exists: scan.matrix?.exists === true },
    packaging_consistency: { deploy_drift_status: 'unavailable' },
  }
}

export function buildBlockedRuntimeGate(reason: string): Record<string, unknown> {
  return {
    status: 'red',
    passed: false,
    checks: [
      { id: 'backend_api_reachable', ok: false, value: false },
      { id: 'setuphelfer_backend_service', ok: false, value: { is_active: 'unknown' } },
    ],
    blockers: [reason],
    workspace_version: null,
    runtime_version: null,
    deploy_drift_status: 'unavailable',
    manifest_match: null,
    phase0_hint: './scripts/check-runtime-deploy-gate.sh',
  }
}

export function buildStandaloneDashboardFromScan(
  scan: WorkspaceScanResult,
  source: DevDashboardDataSource,
  opts?: { matrixText?: string; offlineReason?: string },
): DashboardPayload {
  const wsVersion = scan.version?.project_version as string | undefined
  const feVersion = scan.frontend_package?.version as string | undefined
  const runtimeGate = buildBlockedRuntimeGate(opts?.offlineReason || 'backend_api_unreachable')
  const safeTestMode = {
    mode: 'LOCKED',
    locked: true,
    reason: runtimeGate.blockers,
    blocked_operations: [...DANGEROUS_TEST_OPS],
    message_key: 'devDashboard.safeTestMode.locked',
  }

  const dashboard: DashboardPayload = {
    generated_at: new Date().toISOString(),
    backend_version: null,
    backend_running: false,
    install_profile: 'standalone',
    app_edition: 'repo',
    release_gate_status: 'unknown',
    data_source: source,
    standalone_mode: true,
    runtime: {
      backend_api_reachable: false,
      backend_version: null,
      backend_project_version: null,
      backend_runtime_path: null,
      install_profile: 'standalone',
      app_edition: 'repo',
    },
    workspace: {
      workspace_path: scan.workspace_root,
      workspace_version: wsVersion ?? null,
      workspace_release_stage: scan.version?.release_stage ?? null,
      workspace_version_track: scan.version?.version_track ?? null,
      git_head: scan.git?.git_head ?? null,
      git_branch: scan.git?.git_branch ?? null,
      git_dirty_count: scan.git?.git_dirty_count ?? null,
      git_unpushed_count: null,
    },
    frontend: {
      frontend_build_version: feVersion ?? null,
      frontend_runtime_source: 'standalone',
      frontend_version_matches_backend: null,
    },
    consistency: {
      backend_workspace_match: null,
      frontend_backend_match: null,
      status: 'gray',
      warnings: ['standalone_no_runtime_api'],
    },
    deploy_drift: {
      status: 'gray',
      workspace_root: scan.workspace_root,
      runtime_root: null,
      warnings: ['standalone_deploy_drift_unavailable'],
      suggested_actions: ['none'],
      manifest_match: null,
    },
    runtime_gate: runtimeGate,
    safe_test_mode: safeTestMode,
    package_gate: {
      status: 'gray',
      deb_installed: null,
      runtime_tree_present: null,
      warnings: ['standalone_package_gate_unavailable'],
      forbidden_actions: ['apt_install', 'apt_upgrade', 'automatic_package_update'],
    },
    tests_evidence: buildTestsEvidence(scan),
    roadmap: buildRoadmapFromScan(scan, opts?.matrixText),
    structure_health: buildStructureHealth(scan, runtimeGate),
    warnings: [
      ...(scan.warnings || []),
      'standalone_mode_active',
      opts?.offlineReason || 'backend_api_unreachable',
    ],
    errors: [],
    updated_at: new Date().toISOString(),
  }
  return dashboard
}

export function modulesFromScan(scan: WorkspaceScanResult): ModuleRow[] {
  return (scan.modules || []).map((m) => ({
    id: String(m.id || m.title || 'module'),
    title: String(m.title || m.id || 'module'),
    area: String(m.area || ''),
    status: normalizeAmpel(String(m.status || 'gray')),
    summary: String(m.summary || ''),
    next_steps: Array.isArray(m.next_steps) ? (m.next_steps as string[]) : [],
    blockers: Array.isArray(m.blockers) ? (m.blockers as string[]) : [],
    evidence_files: Array.isArray(m.evidence_files) ? (m.evidence_files as string[]) : [],
    prompt_files: Array.isArray(m.prompt_files) ? (m.prompt_files as string[]) : [],
    report_files: Array.isArray(m.report_files) ? (m.report_files as string[]) : [],
    children: Array.isArray(m.children) ? (m.children as ModuleRow[]) : [],
  }))
}

export function capabilitiesForSource(source: DevDashboardDataSource): DevDashboardCapabilities {
  const standalone = source === 'standalone_workspace' || source === 'snapshot'
  return {
    runtimeApi: source === 'runtime_api',
    workspaceAnalysis: standalone,
    structureHealth: standalone || source === 'runtime_api',
    roadmap: standalone || source === 'runtime_api',
    promptExport: true,
    runtimeTests: source === 'runtime_api',
  }
}

export function buildMinimalUnavailableDashboard(reason: string): DashboardPayload {
  const scan: WorkspaceScanResult = {
    workspace_root: '(unavailable)',
    warnings: [reason],
    git: {},
    evidence_files: {},
    matrix: { exists: false },
    modules: [],
  }
  return buildStandaloneDashboardFromScan(scan, 'unavailable', { offlineReason: reason })
}
