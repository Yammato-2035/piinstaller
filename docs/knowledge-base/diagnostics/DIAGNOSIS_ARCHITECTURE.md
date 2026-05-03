# Diagnosis Architecture

Der Diagnosekern ist jetzt getrennt in `backend/core/diagnostics/` implementiert:

- `models.py`: typisiertes Diagnosemodell und API-Vertrag.
- `registry.py`: strukturierter Diagnosekatalog (stabile IDs als Source of Truth).
- `matcher.py`: deterministische Zuordnung (harte Signale zuerst, dann Pattern).
- `runner.py`: Priorisierung, Ausgabeformat, Evidence.
- `severity.py`, `sources.py`, `formatters.py`: Hilfslogik.

API:

- `POST /api/diagnostics/analyze`
- `GET /api/diagnostics/catalog`
- `GET /api/diagnostics/{id}`
- `GET /api/diagnostics/evidence/schema`
- `GET /api/diagnostics/evidence/sample`

Der bestehende Endpoint `POST /api/diagnosis/interpret` bleibt bestehen (Legacy/Transition), die neue API liefert den strukturierten Diagnosekatalog-basierten Output.

DIAG-1.1 Rueckkopplung:

- EvidenceRecords unter `data/diagnostics/evidence/*.json`
- SystemProfile unter `data/diagnostics/profiles/*.json`
- Katalogantworten werden mit Evidence-Zaehlern und Kontexten angereichert.

## Betriebsdiagnose (Status-Ampeln)

Zusatzlich zum Diagnosekatalog gibt es eine operative Zustandsachse ueber:

- `GET /api/system/status` (Backup/Restore/Security/Updates)
- `GET /api/system/network` (LAN-Erkennung inkl. Warnings/Source)
- `GET /api/monitoring/status` (Prometheus/Grafana/Node Exporter)

Diese Signale werden in Dashboard/Companion gespiegelt und dienen als "first-level diagnosis" fuer Einsteiger:

- Security nicht mehr pauschal gelb, sondern policy-basiert (`green/yellow/red`)
- Updates policy-basiert (`green/yellow/red` nach Kategorien)
- Netzwerk liefert bei fehlender LAN-IP explizit lokalen Zustand statt leerem Feld

Damit ist Diagnose im UI nicht nur textuell, sondern auch als konsistenter Lampenzustand nachvollziehbar.
