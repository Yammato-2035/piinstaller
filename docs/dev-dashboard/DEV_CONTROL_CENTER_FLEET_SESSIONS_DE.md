# Lab Sessions (Fleet Session Phase 1)

## Zweck

Die Kachel **Lab Sessions** im Development Control Center (Tab **Telemetry**) zeigt **Host-seitige** QEMU-/Lab-Smoke-Läufe, sobald der Wrapper startet — **ohne** zu warten, bis der Gast einen Development-Server-Report sendet.

## Abgrenzung Development Server

| Lab Sessions | Development Server |
|--------------|-------------------|
| Host-Wrapper-Lauf | Ingestierte Gast-Knoten |
| Sofort bei Start sichtbar | Erst nach Report/Registry |
| Keine SSH/Remote-Aktionen | Optional read-only SSH |

## LED-Semantik

- **Grau:** keine Session / unbekannt
- **Blau pulsierend:** laufender Smoke, frischer Heartbeat
- **Gelb:** `serial_empty`, `guest_report_missing`, verzögerter Heartbeat
- **Rot:** `timeout`, `failed`, QEMU-Fehler
- **Grün:** `success` mit Gast-Report

## Typische Befunde

- `qemu_timeout_124` — QEMU durch `timeout` beendet (Exit 124)
- `serial_empty` — `qemu-serial.log` bleibt 0 Bytes
- `guest_report_missing` — `dev_server_report_new=false`

## Aktivierung

- `SETUPHELFER_FLEET_SESSIONS_ENABLED=true` oder Dev-Modus (`PI_INSTALLER_DEV=1`)
- Backend muss Fleet-Routen enthalten (nach Deploy/Restart der Runtime)

## Kein Scope

Keine Schule-/Produktionsgeräte, kein Fernstart, keine Wiederbelebung, keine E2E-Consent-Phase (Phase 4 Roadmap).
