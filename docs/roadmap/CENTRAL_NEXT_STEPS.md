# Central Next Steps

Stand: 2026-07-11 (PI-RS-PAYLOAD-TELEMETRY-001)

## Empfohlene Reihenfolge

1. **PI-RS-USB-TELEMETRY-001** — USB Write + Boot Smoke mit Payload **1.10.0.13** (`filesystem.squashfs.repacked-1.10.0.13`)
2. **PI-RS-MSI-RETEST-002** — Operator Boot Retest GE63 mit neuem Payload nach USB-Write
3. **CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot + Post-Reboot-Smoke

## Abgeschlossen (Referenz)

- PI-RS-TEL-SEND-001 — Rescue Lab Send accepted (`req-fd36496e-e1f8-41c7-9cba-9dfb735ff1ca`)
- PI-RS-PAYLOAD-TELEMETRY-001 — SquashFS 1.10.0.13 lokal repacked (kein USB)

## Explizit nicht in diesem Sprint

- Produktiver Telemetry Send
- DNS/Plesk/IONOS Write
- apt upgrade / Reboot auf IONOS
