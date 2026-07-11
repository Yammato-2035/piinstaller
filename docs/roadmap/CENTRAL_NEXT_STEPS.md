# Central Next Steps

Stand: 2026-07-11 (PI-RS-USB-TELEMETRY-001)

## Empfohlene Reihenfolge

1. **Operator Boot Smoke** — Stick mit Payload **1.10.0.13** booten (Checkliste in `docs/evidence/pi_rs_usb_telemetry_001_usb_write_boot_smoke/boot-smoke-operator-required.txt`)
2. **PI-RS-MSI-RETEST-002** — GE63 Operator Boot Retest mit **1.10.0.13**
3. **CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot

## Abgeschlossen (Referenz)

- PI-RS-USB-TELEMETRY-001 — USB Payload-Update auf **1.10.0.13** (verify OK)
- PI-RS-PAYLOAD-TELEMETRY-001 — SquashFS Repack
- PI-RS-TEL-SEND-001 — Lab Send accepted (`req-fd36496e-…`)

## Offen

- Boot-Smoke + optional Lab-Telemetry vom gebooteten Stick (Token nicht im Payload)
