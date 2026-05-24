# Rescue Temp Runtime Bundle — Preview

**Status:** **ok** (Preview/Dokumentation; kein Pack-Befehl in diesem Auftrag)  
**Zweck:** Temporäres read-only Runtime-Bundle für Live-Medium-Network-Validation

## Zielstruktur

```text
setuphelfer-rescue-runtime/
├── backend/
│   ├── app.py
│   ├── core/
│   ├── deploy/
│   ├── venv/              # deploy-sealed, keine pip/apt auf Live
│   └── requirements.txt   # Referenz only
├── frontend/dist/
├── scripts/
│   ├── rescue-live/
│   │   ├── start-backend-localonly.sh
│   │   ├── start-ui-localonly.sh
│   │   └── check-localonly.sh
│   └── serve-frontend-production.py
├── config/version.json
├── VERSION
└── README_RESCUE_TEMP_RUNTIME.md
```

## Pflichtregeln

| Regel | Preview-Status |
|-------|----------------|
| Keine `.env` | **ok** — nicht im Bundle |
| Keine Secrets | **ok** |
| Keine Backups/Restore-Artefakte | **ok** |
| Keine `node_modules` | **ok** |
| Keine Dev-venv ohne Seal | **review_required** — Operator muss Deploy-venv kopieren |
| Keine `__pycache__` / `.pyc` | **ok** — beim Packen strippen |
| Keine privaten Hostpfade in Config | **ok** |
| Kein automatischer Write | **ok** — Skripte starten nur localhost |

## Enthalten / ausgeschlossen

| Inhalt | Im Bundle | Grund |
|--------|-----------|--------|
| `backend/venv` | ja | Runtime ohne apt |
| `frontend/src` | nein | nur `dist` |
| `docs/` | nein | Evidence bleibt im Dev-Repo |
| `build/rescue/` | nein | Emulation lokal |
| `.git/` | nein | — |
| `scripts/deploy-to-opt.sh` | nein | kein Deploy auf Live |

## README_RESCUE_TEMP_RUNTIME.md (Inhalt im Bundle)

- `SETUPHELFER_RESCUE_ROOT` setzen
- Zwei Terminals: Backend + UI Skripte
- `check-localonly.sh` ausführen
- Kein sudo, apt, mount, restore
- Evidence nach Runbook sammeln

## Gesamt-Preview-Status

**ok** — Struktur und Regeln definiert; physisches Packen und Live-Boot sind **separater Operator-Schritt**.
