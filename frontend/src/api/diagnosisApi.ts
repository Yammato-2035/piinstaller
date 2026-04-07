import { fetchApi } from '../api'
import { localDiagnosisFallback } from '../diagnosis/localInterpretFallback'
import type { DiagnosisInterpretRequest, DiagnosisRecord } from '../types/diagnosis'

export async function postDiagnosisInterpret(
  body: DiagnosisInterpretRequest,
): Promise<DiagnosisRecord> {
  try {
    const res = await fetchApi('/api/diagnosis/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      return localDiagnosisFallback(body)
    }
    try {
      return (await res.json()) as DiagnosisRecord
    } catch {
      return localDiagnosisFallback(body)
    }
  } catch {
    return localDiagnosisFallback(body)
  }
}
