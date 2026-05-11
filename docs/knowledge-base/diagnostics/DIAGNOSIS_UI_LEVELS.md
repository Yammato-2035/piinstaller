# Diagnosis UI Levels

Frontend nutzt drei Stufen:

- **Beginner**: klare Handlung, wenig Technik, Risikohinweis.
- **Advanced**: Diagnoseweg + priorisierte Checks.
- **Expert**: kompakte technische Zusammenfassung und Evidenz.

Aktuell integriert:

- `DiagnosisPanel` (bestehende Interpretation)
- `DiagnosticsAssistantPanel` (neue strukturierte Analyse aus `/api/diagnostics/analyze`)

Beispiel in `BackupRestore`:

- Verifikationsfehler loest weiterhin `POST /api/diagnosis/interpret` aus.
- Parallel wird `POST /api/diagnostics/analyze` aufgerufen und nach Nutzerstufe gerendert.
