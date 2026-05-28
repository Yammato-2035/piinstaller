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

## Ist das Developer Dashboard ein Produktfeature für normale Nutzer?

Nein. Es ist internes Developer-/Operator-/Governance-Tooling und nicht Teil normaler Nutzerflows.

## Darf das Developer Dashboard ein freies Terminal bereitstellen?

Nein. Keine freie Shell, keine freie Kommandoeingabe, keine Terminal-Emulation mit Eingabe.

## Was ist der geplante Controlled Command Runner?

Ein streng allowlist-basierter interner Runner mit Safety-Klassen, Exit-Code-Auswertung, stdout/stderr-Logs und Evidence-Dateien. Kein freier Command-String, kein sudo aus dem Dashboard, keine gefährlichen Systemaktionen.

## Dürfen damit Operator-Aktionen ersetzt werden?

Nein. Operator-Handoffs sind erlaubt, aber echte Operator-Terminal-Aktionen bleiben getrennt und manuell.

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

## Phase-0-Gate und Deploy-Helper

Stand **2026-05-27**: Gate Exit **0**, `deploy_drift` green, `safe_test_mode` **UNLOCKED**. `/opt` enthält `manual-command-runs` und aktuelles `backend/app.py`.

Bei erneutem Drift (Exit **14**): nur `setuphelfer-deploy-helper.service` nach Operator-Freigabe — kein manuelles Kopieren nach `/opt`.

## Warum konnte der Agent den Deploy-Helper nicht starten?

`sudo systemctl start setuphelfer-deploy-helper.service` benötigt ein TTY-Passwort. Der Operator kann den Helper lokal starten; ein bereits synchrones `/opt` liefert trotzdem Gate **0**.

## Duerfen Cursor-Laeufe Background-Tasks oder Auto-Ketten starten?

Nein. Keine Background-Tasks, keine Auto-Efficiency-/Ingest-Ketten und keine automatischen Commit-/Push-Ketten.  
Jeder Lauf endet synchron mit Schlussbericht. Falls Operatorrechte noetig sind, wird nur ein Operator-Handoff dokumentiert.

## Warum reicht "Port 8000 lauscht" nicht?

Weil ein Backend haengen kann: Prozess aktiv, Port offen, aber HTTP-Endpunkte antworten nicht.  
Erst `/health` und `/api/version` mit HTTP 200 zeigen echte Verfuegbarkeit.

## Was bedeutet Backend-Hang?

`setuphelfer-backend.service` ist aktiv und `:8000` LISTEN, aber `/health` oder `/api/version` laufen in Timeout.  
Dieser Zustand ist ein harter Blocker (`backend_hanging`), kein tolerierbarer Offline-Fall.

## Warum zeigt das Control Center einen roten Backend-Fehler statt leerer Daten?

Damit der Fehler sichtbar und reparierbar bleibt. Leere Panels ohne klare Ursache fuehren zu Fehlbedienung.  
Bei Hang/Offline wird der Zustand explizit angezeigt und Snapshot/Fallback klar als nicht-live markiert.

## Warum darf Rescue bei Backend-Hang nicht weiterlaufen?

Rescue/Backup/Restore brauchen eine belastbare Runtime mit funktionierenden API-Gates.  
Bei `backend_hanging` ist das Runtime-Gate blockiert; Weiterarbeit wuerde Fake-Green und inkonsistente Evidence riskieren.

## Was soll der Operator bei Backend-Hang tun?

Runbook ausfuehren: `systemctl status`, `journalctl`, kontrollierter `restart`, danach `/health`, `/api/version` und Runtime-Gate erneut pruefen.  
Siehe `docs/operations/BACKEND_RUNTIME_RECOVERY_RUNBOOK.md`.
