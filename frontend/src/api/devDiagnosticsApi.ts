import { fetchApi } from '../api'

export type DiagnosticClassification = {
  primary?: string
  secondary?: string[]
  confidence?: string
}

export type DiagnosticExport = {
  export_id?: string
  created_at?: string
  redacted?: boolean
  scope?: string
  sharing_warning?: string
  run_id?: string
  session_id?: string
  classification?: DiagnosticClassification
  runtime?: Record<string, unknown>
  fleet_session?: Record<string, unknown>
  qemu_smoke?: Record<string, unknown>
  devserver_ingest?: {
    report_new?: boolean
    guest_found?: boolean
    reports_last_24h?: number
    latest_findings?: unknown[]
  }
  evidence?: {
    paths?: { path?: string; size_bytes?: number; exists?: boolean }[]
    missing_paths?: string[]
    bundle_available?: boolean
    run_dir?: string
  }
  redaction?: Record<string, unknown>
}

export type DiagnosticExportResponse = {
  code?: string
  export?: DiagnosticExport
  summary_text?: string
}

export type EvidenceIndexResponse = {
  code?: string
  index?: {
    paths?: { path?: string; size_bytes?: number; exists?: boolean }[]
    missing_paths?: string[]
    bundle_available?: boolean
  }
}

export async function fetchQemuSmokeDiagnosticExport(
  runId: string
): Promise<DiagnosticExportResponse | null> {
  try {
    const res = await fetchApi(
      `/api/dev-diagnostics/qemu-smokes/${encodeURIComponent(runId)}/export`
    )
    if (!res.ok) return null
    return (await res.json()) as DiagnosticExportResponse
  } catch {
    return null
  }
}

export async function fetchFleetSessionDiagnosticExport(
  sessionId: string
): Promise<DiagnosticExportResponse | null> {
  try {
    const res = await fetchApi(
      `/api/dev-diagnostics/fleet-sessions/${encodeURIComponent(sessionId)}/export`
    )
    if (!res.ok) return null
    return (await res.json()) as DiagnosticExportResponse
  } catch {
    return null
  }
}

export async function fetchQemuSmokeMarkdownReport(runId: string): Promise<string | null> {
  try {
    const res = await fetchApi(
      `/api/dev-diagnostics/qemu-smokes/${encodeURIComponent(runId)}/markdown`
    )
    if (!res.ok) return null
    return await res.text()
  } catch {
    return null
  }
}

export async function fetchEvidenceIndex(runId: string): Promise<EvidenceIndexResponse | null> {
  try {
    const res = await fetchApi(
      `/api/dev-diagnostics/qemu-smokes/${encodeURIComponent(runId)}/evidence-index`
    )
    if (!res.ok) return null
    return (await res.json()) as EvidenceIndexResponse
  } catch {
    return null
  }
}

export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (!text) return false
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    /* fallback below */
  }
  return false
}
