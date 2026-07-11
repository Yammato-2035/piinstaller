# Central Next Steps

Stand: 2026-07-12 (PI-RS-MSI-RETEST-002 Payload 1.10.0.13)

## Empfohlene Reihenfolge

1. **PI-RS-MSI-RETEST-002 Operator Boot** — GE63 mit Payload **1.10.0.13** booten (`docs/test-plans/PI_RS_MSI_RETEST_002_OPERATOR_BOOT_RUNBOOK.md`)
2. SETUP_LOGS importieren → Telemetry Preview (+ optional Lab Send mit Token)
3. **CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot

## Abgeschlossen (Referenz)

- PI-RS-MSI-RETEST-002 Preflight — Stick **1.10.0.13** bereit, historische Baseline importiert
- PI-RS-USB-TELEMETRY-001 — USB Payload-Update auf **1.10.0.13** (verify OK)
- PI-RS-PAYLOAD-TELEMETRY-001 — SquashFS Repack
- PI-RS-TEL-SEND-001 — Lab Send accepted (`req-fd36496e-…`)

## Offen

- Boot-Smoke + optional Lab-Telemetry vom gebooteten Stick (Token nicht im Payload)
