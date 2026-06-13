# R.3 — Rescue Stick Persistence Design Evidence

**Status:** Implementiert (Workspace)  
**Modul:** `backend/core/rescue_persistence.py`  
**Tests:** `backend/tests/test_rescue_persistence_r3.py` (4 Tests, OK)

## Designentscheidungen

| Thema | Entscheidung |
|-------|--------------|
| Evidence-Root | `<mount>/setuphelfer-evidence` |
| Fallback | `/tmp/setuphelfer-evidence` + `warning` im JSON |
| Stick-Labels | `SETUPHELFER*`-Familie |
| Interne Disks | `_reject_internal_system_source` via `safe_device` |
| Storage-Reuse | `discover_findmnt_mounts_flat`, kein neues lsblk-Duplikat |

## Schreib-API

- `write_rescue_json_evidence(subdir, filename, payload)` — validiert Dateinamen (kein `..`)
- `write_rescue_text_evidence(subdir, filename, text)`
- Jeder Write liefert `{path, status, fallback, warning?}`

## Diagnose

`build_rescue_persistence_diagnostics()` exportiert Version, Public Functions, letzte Detection-Snapshot-Felder.

## Verifikation

```bash
python3 -m py_compile backend/core/rescue_persistence.py
python3 -m unittest backend.tests.test_rescue_persistence_r3 -v
```

## Offen für R.4

- Telemetrie-Push-Skript an Spool anbinden
- Boundary-Guards für neue Module in `check-module-boundaries.sh`
