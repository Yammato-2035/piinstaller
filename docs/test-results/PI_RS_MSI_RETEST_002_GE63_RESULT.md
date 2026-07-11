# PI-RS-MSI-RETEST-002 GE63 Result

Stand: 2026-07-12

## Status

**`operator_action_required`**

Der physische Boot-Retest am MSI GE63 Raider mit Payload **1.10.0.13** wurde in diesem Sprint **nicht** durchgeführt.
Stick-Bereitschaft verifiziert (SETUPHELFER read-only); SETUP_LOGS enthält keinen Post-Update-Boot-Nachweis.

## Payload

| Feld | Wert |
|------|------|
| Workspace version | 1.9.19.5 |
| Stick/Payload version | **1.10.0.13** |
| Payload SHA256 | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |
| USB verify | success (PI-RS-USB-TELEMETRY-001) |
| Drift akzeptiert | ja (Workspace vs Payload-Track) |

## Boot

| Check | Ergebnis |
|-------|----------|
| Boot menu visible | *nicht geprüft — Operator erforderlich* |
| TUI visible | *nicht geprüft* |
| GUI result | *nicht geprüft* |
| Backend/API result | *nicht geprüft* (Referenz 1.10.0.12: HTTP 200) |
| Shutdown result | *nicht geprüft* |

## Hardware

| Check | Ergebnis |
|-------|----------|
| MSI GE63 Raider confirmed | *nicht geprüft (letzter SETUP_LOGS-Lauf: GE63 Raider RGB 8RF / MS-16P5)* |
| Storage detected | *nicht geprüft* |
| WLAN Intel AC9560 | *nicht geprüft* |
| Killer E2500 | *nicht geprüft* |
| PCIe/AER warnings | *nicht geprüft* |

## Telemetry

| Check | Ergebnis |
|-------|----------|
| Preview vom gebooteten Stick | **nein** |
| Lab Send vom gebooteten Stick | **nein** |
| Erwartung ohne Token | `blocked_missing_auth` |

## Evidence

| Feld | Wert |
|------|------|
| Sprint doc | `docs/rescue-stick/PI_RS_MSI_RETEST_002_GE63_PAYLOAD_1_10_0_13.md` |
| Evidence dir | `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/` |
| Import dir | historische Baseline (5 Dateien, Payload 1.10.0.12) |
| Stick preflight | `stick-readiness-preflight.txt` |

## Safety

| Check | Ergebnis |
|-------|----------|
| productive telemetry send | **nein** |
| lab send from stick | **nein** |
| remote commands | **nein** |
| auto-remediation | **nein** |
| repair action | **nein** |
| USB write | **nein** |
| backup/restore/wipe | **nein** |

## Decision

| Feld | Wert |
|------|------|
| Retest accepted | *ausstehend — Operator Boot mit 1.10.0.13 erforderlich* |
| Repack needed | **nein** |
| USB update needed | **nein** |
| Follow-up | Operator MSI-Boot → SETUP_LOGS import → Ergebnis aktualisieren |
