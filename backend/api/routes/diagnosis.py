"""
Diagnose-Interpreter API (lokal, ohne Remote-Session-Zwang).

POST /api/diagnosis/interpret — strukturierte Einordnung für Companion-UI.
Ersetzt keine Backup/Restore-Endpunkte; nur Interpretation.
"""

from fastapi import APIRouter

from diagnosis.interpret_v1 import interpret_v1
from models.diagnosis import DiagnosisInterpretRequest, DiagnosisRecord

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])


@router.post("/interpret", response_model=DiagnosisRecord)
async def post_interpret(body: DiagnosisInterpretRequest) -> DiagnosisRecord:
    return interpret_v1(body)
