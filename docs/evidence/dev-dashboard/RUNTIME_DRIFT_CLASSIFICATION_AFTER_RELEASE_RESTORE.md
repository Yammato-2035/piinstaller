# Runtime-Drift — Klassifikation nach Release-Restore

**Stand:** 2026-06-02  
**Workspace HEAD:** `9438901` (nur Evidence/Doku in diesem Commit)

## Klassifikation

| Klasse | Wert |
|--------|------|
| **runtime_code_drift** | **yellow** (`runtime_code_drift_yellow`) |
| **evidence_only_drift** | **yes** |

## Methode

SHA256-Vergleich Workspace vs. `/opt/setuphelfer` für produktionsrelevante Pfade, **ohne** `venv`, `tests`, `__pycache__`, `cache`, `target`, `dist`, `node_modules`.

## Kritische Pfade (Match)

| Pfad | Status |
|------|--------|
| `backend/app.py` | **match** |
| `backend/rescue_agent/routers.py` | **match** |
| `scripts/rescue-live/fleet-session-api.sh` | **match** (`55b7bce`) |
| `config/version.json` | **match** |

→ Fleet-/Rescue-Backend-Runtime **nicht** durch Workspace-Code blockiert.

## Nicht-kritische Abweichungen (4 Dateien)

| Pfad | Art |
|------|-----|
| `scripts/rescue-live/clean-controlled-live-build-tree.sh` | Build-Hilfsskript |
| `frontend/src/pages/Documentation.tsx` | UI-Text, nicht Backend |
| `frontend/src/pages/RaspberryPiConfig.tsx` | UI-Text, nicht Backend |
| `frontend/src/lib/sudoUserMessages.ts` | UI-Messages, nicht Backend |

## Rohzählung (ungefiltert)

Ungeschützter Scan inkl. `backend/venv` → tausende Treffer — **nicht** als Deploy-Blocker gewertet.

## Entscheidung

- **Kein** `runtime_code_drift_red` für Ingest/ISO-Precheck-Freigabe.
- Commit `9438901` allein erzeugt **keinen** harten Runtime-Blocker (`evidence_only_drift`).
