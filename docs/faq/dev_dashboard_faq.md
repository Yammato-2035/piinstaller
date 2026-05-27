# Developer Dashboard — FAQ

## Warum war der Roadmap-Bereich nicht sichtbar?

Oft wurde das **Governance-Cockpit** (`CockpitApp`) genutzt statt der Seite **Developer Dashboard** (`dev-dashboard`). Das Cockpit hatte bis 2026-05-27 nur die Governance-Matrix, keinen Roadmap-Registry-Block. Die API lieferte Roadmap-Daten trotzdem.

## Welche Quelle nutzt der Roadmap-Bereich?

- Live: Backend-Registry (`/api/dev-dashboard/roadmap`, eingebettet in `/status`)
- Offline: Snapshot oder STATUS_MATRIX-Ableitung (mit Hinweis „Offline/Snapshot“)

## Was bedeutet Offline-/Snapshot-Roadmap?

Teilweise Einträge aus der Ampel-Matrix — **kein** vollständiges Meilenstein-Bundle. Kein Fake-Green.

## Warum werden rote Blocker weiterhin angezeigt?

Release-Gate, Backup, Rescue und Packaging bleiben rot/gelb ohne Evidence — absichtlich.

## Warum erscheint „grün“ nur mit Evidence?

Die Sektion **Bereit / stabil** und OK-Badges beziehen sich nur auf Gates mit `passed=true` bzw. `deploy_drift.status=green`. Farben ändern keine Backend-Logik.

## Warum reicht ein Chat-Ausschnitt nicht als Log?

Nachweise gehören als strukturierte JSON-Datei unter `docs/evidence/dev-dashboard/manual_command_runs/` mit Zweck, Exit-Code und idealerweise `full_log_path`. Nur Chat-Ausschnitte erzeugen im Dashboard eine **Gelb-Warnung** (excerpt only).

## Warum führt das Dashboard keine Befehle aus?

Sicherheitsgrenze: read-only Observability. Es gibt **keine** Execute-Buttons, kein Terminal, kein `sudo` aus der UI — nur `GET /api/dev-dashboard/manual-command-runs`.

## Was ist ein read-only Command Run?

Ein dokumentierter manueller Lauf (Operator/Cursor) mit `commands[]`, `safety_class` und `summary.status` — importiert aus JSON, nicht live ausgeführt.

## Warum bleiben skipped API-Tests gelb?

`python3` ohne `fastapi` skippt `TestDevDashboardApiV1` (11 Tests). Mit `backend/venv/bin/python3` laufen alle 34 Tests. Siehe `docs/evidence/dev-dashboard/DEV_DASHBOARD_API_TEST_SKIP_TRIAGE.md`.

## Ist TERMINAL_A_READONLY erledigt?

Ja — Status **completed** in der Prompt-Registry (5786eb3). Read-only Command Runs über JSON-Evidence und `GET /api/dev-dashboard/manual-command-runs`, ohne Shell aus dem UI.

## Warum ist http://127.0.0.1:5173 nicht erreichbar?

Port **5173** ist nur aktiv, wenn der Vite-Dev-Server läuft (`npm --prefix frontend run dev` oder `npm run dev:cockpit`). Produktiv: gebautes Frontend über Setuphelfer-Backend (Port **8000**) oder Tauri — nicht 5173 ohne laufenden Dev-Server.
