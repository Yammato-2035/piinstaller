# IST-Analyse — Development Diagnostic Export

**Stand:** 2026-06-01

## Datenquellen (vor Implementierung)

| Quelle | Ort | Typ |
|--------|-----|-----|
| Fleet Session API | `GET /api/fleet/sessions/*` | Runtime API + JSONL |
| Fleet persistiert | `docs/evidence/runtime-results/dev-dashboard/fleet_sessions_latest.json` | Workspace + `/opt` nach Deploy |
| Fleet JSONL | `fleet_sessions.jsonl` | Append-only Historie |
| QEMU Autopilot | `docs/evidence/runtime-results/rescue/qemu/{RUN_ID}/qemu_autopilot_result.json` | Workspace Evidence |
| QEMU Serial | `…/qemu-serial.log` | Workspace (kann 0 B) |
| QEMU stderr | `…/qemu-gtk-stderr.log` | Workspace |
| Devserver summary | `…/dev_server_summary_{before,after}.json` | Evidence pro Lauf |
| Devserver API | `GET /api/dev-server/summary` | Runtime (nicht pro Run persistiert außer Evidence) |
| Node registry | Devserver storage unter Backend | Runtime |
| Runtime gates | `scripts/check-*-gate.sh` | Operator-Skripte |
| Statusmatrix | `docs/roadmap/STATUS_MATRIX.md` | Doku |
| Analyse 081222 | `docs/evidence/rescue/QEMU_DEVELOPER_SMOKE_20260601_081222_ANALYSIS.md` | Doku |

## /opt vs Workspace

- Produktiv-Backend läuft unter `/opt/setuphelfer`; Fleet-JSONL kann dort aktueller sein als Workspace.
- QEMU-Evidence liegt primär im **Workspace** unter `docs/evidence/runtime-results/rescue/qemu/`.
- Export-Service liest `SETUPHELFER_REPO_ROOT` oder Workspace-Root aus `backend/core` parent.

## Runtime-only

- Live `GET /api/dev-server/summary` (aktueller Knotenstand, nicht historisch pro QEMU-Run, außer in Evidence-JSON des Laufs).

## Potenzielle Secrets

- `.env`, API-Keys, SMTP-Passwörter, private keys — **nicht** in Fleet/QEMU-Evidence erwartet; Redaction dennoch Pflicht.
- Devserver-Reports können `sensitive_field_present`-Warnings enthalten — nur gekürzte `latest_findings` im Export.

## Redaktion

- Tokens, Keys, E-Mails maskieren.
- Serial nur Head/Tail.
- Keine vollständigen 80k+ Report-JSONs.

## Lücken (vor Export)

- Kein einheitlicher Copy-Block für Cursor/ChatGPT.
- Lab UI zeigte Fleet-State, aber kein zusammengeführter JSON/Markdown-Export.
- `report_new` / `guest_found` nur implizit in `qemu_autopilot_result.json`.

## Implementierung (nach)

- `backend/core/dev_diagnostic_export.py`
- `GET /api/dev-diagnostics/*`
- `LabSessionsPanel` Copy-Buttons
