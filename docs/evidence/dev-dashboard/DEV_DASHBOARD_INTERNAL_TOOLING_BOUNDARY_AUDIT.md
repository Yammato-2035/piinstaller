# Dev Dashboard Internal Tooling Boundary Audit

Datum: 2026-05-28  
Modus: statische Analyse (Phase-0-Gate war nicht grün)

## Ergebnis

- Developer Dashboard ist als internes Expert-/Governance-Tool ausgelegt.
- Es gibt read-only Command-Run-Logging (`manual_command_runs`) ohne Shell-Execution.
- Es existiert keine freie Shell-Eingabe und keine generische Terminal-Emulation im Dashboard.
- Es gibt jedoch API-Routen im Rescue-Kontext, die als Operator-Command-Handoff oder Schritt-Trigger fungieren und klar vom zukünftigen Controlled Runner getrennt werden müssen.

## Geprüfte Quellen

- Frontend: `frontend/src/pages/ExternalDevelopmentControlCenter.tsx`, `frontend/src/pages/DevelopmentDashboard.tsx`, `frontend/src/components/dev-dashboard/`, `frontend/src/lib/devDashboard/`, `frontend/src/locales/de.json`, `frontend/src/locales/en.json`
- Backend: `backend/core/dev_dashboard.py`, `backend/core/dev_dashboard_manual_command_runs.py`, `backend/app.py`
- Doku/Roadmap/Evidence: `docs/dev-dashboard/`, `docs/knowledge-base/dev-dashboard/`, `docs/faq/dev_dashboard_faq.md`, `docs/roadmap/setuphelfer_roadmap.json`, `docs/roadmap/setuphelfer_next_prompts.json`, `docs/evidence/dev-dashboard/manual_command_runs/`

## Befunde

1. **Interne Positionierung vorhanden**
   - Dashboard-Texte enthalten bereits Hinweise wie "expert only", "read only", "no execution from dashboard".
2. **Read-only Command Runs vorhanden**
   - `backend/core/dev_dashboard_manual_command_runs.py` liest JSON-Evidence und setzt `execution_allowed=false`.
3. **Keine generische Execute-Route für Command Runs**
   - Es gibt `GET /api/dev-dashboard/manual-command-runs`; `POST` dafür ist nicht vorgesehen.
4. **Abgrenzungsrisiko in Modulnähe**
   - Im Rescue-Bereich existieren `POST`-Routen für Schritt-/Operator-Kommandostrukturen. Diese dürfen nicht als allgemeiner Command Runner interpretiert werden.
5. **Governance-Risiko**
   - Ohne explizites Boundary-Dokument kann die interne Tooling-Schicht fälschlich als Produktfeature gelesen werden.

## Empfohlene Boundary-Regeln

1. Dev Dashboard bleibt internes Tooling (`internal_tooling_only=true`).
2. Kein User-Facing-Produktfeature und keine Produktnavigation für normale Nutzer.
3. Keine freie Shell, kein freier Command-String, keine Terminal-Eingabe aus der UI.
4. Kein `sudo` aus Dashboard-Execution.
5. Controlled Runner nur allowlist-basiert per `command_id` + `argv`.
6. `forbidden`-Klasse wird nie ausgeführt, nur klassifiziert und dokumentiert.
7. Jeder Lauf erzeugt Evidence (JSON + stdout/stderr-Logdateien).
8. Roadmap-Status nur über Evidence und Review, nicht per Auto-Green.
9. Operator-Handoffs sind erlaubt, ersetzen aber keine Operator-Terminal-Aktionen.
10. Rescue/Backup/Restore/Hardware/USB-Schreibaktionen bleiben außerhalb des Dashboard-Runners.
