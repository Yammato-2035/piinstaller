import { fetchApi } from '../api'
import type { DiagnosisInterpretRequest, DiagnosisRecord } from '../types/diagnosis'

export async function postDiagnosisInterpret(
  body: DiagnosisInterpretRequest,
): Promise<DiagnosisRecord | null> {
  try {
    const res = await fetchApi('/api/diagnosis/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return null
    return (await res.json()) as DiagnosisRecord
  } catch {
    return null
  }
}
