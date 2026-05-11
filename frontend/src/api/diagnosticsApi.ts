import { fetchApi } from '../api'
import type { DiagnosticsAnalyzeRequest, DiagnosticsAnalyzeResponse } from '../types/diagnostics'

export async function postDiagnosticsAnalyze(
  body: DiagnosticsAnalyzeRequest,
): Promise<DiagnosticsAnalyzeResponse | null> {
  try {
    const res = await fetchApi('/api/diagnostics/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return null
    return (await res.json()) as DiagnosticsAnalyzeResponse
  } catch {
    return null
  }
}
