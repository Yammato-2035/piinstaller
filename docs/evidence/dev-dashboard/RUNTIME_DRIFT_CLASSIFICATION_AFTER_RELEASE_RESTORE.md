# Runtime-Drift — Klassifikation nach Release-Restore

**Stand:** 2026-06-02  
**Workspace HEAD:** `050d119`  
**Ingest:** read-only nach Operator-Release-Restore

## Klassifikation

| Klasse | Wert |
|--------|------|
| **runtime_code_drift** | **`runtime_code_drift_yellow`** |
| **evidence_only_drift** | **yes** |

## Methode

SHA256 Workspace vs. `/opt/setuphelfer` für produktionsrelevante Pfade:

- `backend/`, `scripts/`, `packaging/systemd/`, `frontend/src/`, `frontend/package.json`, `config/version.json`
- **Ausgeschlossen:** `venv`, `tests`, `__pycache__`, `cache`, `target`, `dist`, `node_modules`

## Ergebnis

| Metrik | Wert |
|--------|------|
| `production_runtime_drift_count` | **4** |
| Kritische Backend-Pfade | **0 Abweichungen** |

### Kritische Pfade (Match)

| Pfad | Status |
|------|--------|
| `backend/app.py` | match |
| `backend/rescue_agent/routers.py` | match |
| `scripts/rescue-live/fleet-session-api.sh` | match (`55b7bce`) |
| `config/version.json` | match |

### Nicht-kritische Abweichungen (4)

| Pfad | Art |
|------|-----|
| `scripts/rescue-live/clean-controlled-live-build-tree.sh` | Build-Hilfsskript |
| `frontend/src/pages/Documentation.tsx` | UI-Text |
| `frontend/src/pages/RaspberryPiConfig.tsx` | UI-Text |
| `frontend/src/lib/sudoUserMessages.ts` | UI-Messages |

## Entscheidung

- **Nicht** `runtime_code_drift_red` — Rescue-Agent-Ingest **nicht** blockiert.
- Neuere Evidence/Doku-Commits in HEAD (`050d119`, `9438901`, …) allein = **`evidence_only_drift`**.
