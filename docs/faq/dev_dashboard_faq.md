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

## Welche URL hat das Development Control Center lokal?

Der Port kommt vom **laufenden Vite-Prozess**, nicht aus einer festen Konstante:

- `npm run dev:cockpit` → Standard **3001**; bei belegtem Port Fallback (z. B. **3002**). Die Zeile `Local: http://127.0.0.1:…` im Terminal ist maßgeblich.
- `npm run dev:tauri` → **5173** (`--strictPort`).
- Cockpit-Pfad: `/?window=cockpit` (Beispiel: `http://127.0.0.1:3002/?window=cockpit`).
- Backend-API bleibt **8000**.

## Warum ist http://127.0.0.1:5173 nicht erreichbar?

Port **5173** lauscht nur, wenn **Tauri/Vite** mit `dev:tauri` (oder vergleichbar) dort startet. Das Browser-Cockpit (`dev:cockpit`) nutzt **3001/3002**, nicht 5173. Produktiv: gebautes Frontend über Setuphelfer-Backend (**8000**) unter `/opt/setuphelfer`.

## Warum ist das Phase-0-Gate rot (Exit 14)?

`deploy_drift_backend_files`: Workspace-Backend (z. B. `backend/app.py` nach `5786eb3`) weicht von `/opt/setuphelfer` ab. Behebung: Deploy-Helper-Sync durch den Operator, dann `./scripts/check-runtime-deploy-gate.sh` → Exit **0**. Kein Fake-Green in der Roadmap.
