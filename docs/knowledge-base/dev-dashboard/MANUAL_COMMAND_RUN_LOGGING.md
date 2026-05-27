# Manual Command Run Logging (Developer Dashboard)

## Zweck

Cursor- und Operator-Läufe sollen **vollständig** nachvollziehbar sein — nicht nur als Chat-Ausschnitt.

## Ablage

- Verzeichnis: `docs/evidence/dev-dashboard/manual_command_runs/`
- Schema: `manual_command_run.schema.json`
- Eine JSON-Datei pro Lauf

## Dashboard

- Route: `GET /api/dev-dashboard/manual-command-runs` (read-only)
- Panel: Developer Dashboard → Bereich **Struktur**
- **Kein** POST, **kein** Shell, **kein** sudo aus der UI

## safety_class

| Wert | Bedeutung |
|------|-----------|
| `read_only` | Gate, curl, Tests, Doku |
| `operator_action` | Deploy-Helper, manueller Build (außerhalb Dashboard) |
| `forbidden` | dd, apt ohne Freigabe — rot im UI |

## API-Tests

| Interpreter | Ergebnis |
|-------------|----------|
| `backend/venv/bin/python3` | 34 passed, 0 skipped — **grün** |
| System-`python3` | 23 passed, 11 skipped — **gelb** (kein Produktfehler) |

## Roadmap

- Prompt `TERMINAL_A_READONLY`: **completed**
- Nächster empfohlener Prompt: `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`
- Vor Rescue-Build: Cockpit-/Roadmap-UI unter `/opt` per Deploy-Helper prüfen
