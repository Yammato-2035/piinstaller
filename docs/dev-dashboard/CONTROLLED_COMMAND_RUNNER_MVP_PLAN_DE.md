# Controlled Command Runner MVP-Plan (DE)

## MVP-0

- Doku, Schema, Allowlist-Design
- keine Ausführung

## MVP-1

- Backend liest Allowlist
- `GET /api/dev-dashboard/controlled-command-runs`
- `GET /api/dev-dashboard/controlled-command-allowlist`
- keine POST-Ausführung

## MVP-2

- POST nur für `read_only`/`test_only`-`command_id`
- kein freier Command-String
- nur allowlist-`argv`
- Timeout + stdout/stderr-Logs
- Evidence-JSON pro Run
- kein `sudo`/`apt`/`dd`/`mkfs`/Mount-Write

## MVP-3

- Runbook Runner für definierte Sequenzen
- Roadmap-Delta-Vorschläge
- keine automatische Statusänderung ohne Review

## MVP-4

- Operator-Handoff-Import
- Operator lädt manuelle Logs/Evidence
- Dashboard wertet aus
