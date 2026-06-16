# DCC Profile + QEMU 212528 — Phase 0 Baseline

**Datum:** 2026-06-03  
**HEAD:** `e7f0bc2`  
**Branch:** `main`

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `false` |
| Port 8000 listening | **yes** (`127.0.0.1:8000`) |
| Port 3001 listening | **yes** (`127.0.0.1:3001`, SimpleHTTP) |
| Port 8080 | **nginx**, nicht SetupHelfer-DCC |
| DCC unter release deaktiviert | **erwartbar** |

## Nicht-Ziele

Kein neuer QEMU · Kein ISO-Build · Kein USB · Kein Backup · Kein Restore

## Artefakte

- `docs/evidence/dev-dashboard/dcc_profile_and_qemu_212528_version_baseline.json`
- `docs/evidence/dev-dashboard/dcc_profile_and_qemu_212528_frontend_3001_headers.txt`
- `docs/evidence/dev-dashboard/dcc_profile_and_qemu_212528_nginx_8080_headers.txt`
