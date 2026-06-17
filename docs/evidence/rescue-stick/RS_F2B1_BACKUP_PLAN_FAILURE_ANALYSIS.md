# RS-F2B.1 Backup Plan Failure Analysis

## Pflichtfragen

| # | Frage | Antwort |
|---|-------|---------|
| 1 | Quelle erkannt? | unbekannt im Wizard (`disk_discovery: null`) |
| 2 | Quelle eindeutig? | nein (Wizard nicht ausgeführt) |
| 3 | Windows/NTFS erkannt? | unbekannt |
| 4 | BitLocker erkannt? | unbekannt |
| 5 | Backupziel erkannt? | nein im Wizard |
| 6 | Externe HDD angeschlossen? | unbekannt (kein Discovery-Log) |
| 7 | Externe HDD beschreibbar? | unbekannt |
| 8 | Externe HDD groß genug? | unbekannt |
| 9 | UI Cloud statt HDD? | unbekannt |
| 10 | WLAN blockiert HDD-Plan fälschlich? | **möglich** (network_ok=false im start-assistant) |
| 11 | Operator-Bestätigungen fehlen? | wahrscheinlich |
| 12 | Plan-Contract im Stick-Backend fehlte? | **ja** (RS-F2S hatte nur Preflight) |
| 13 | API nicht erreichbar? | unbekannt |
| 14 | Version/Payload-Mismatch? | Spot-checks fehlgeschlagen, Squashfs-Hash OK |
| 15 | Rechneridentität blockiert? | unbekannt |
| 16 | ASUS/MSI-Gate? | unbekannt |
| 17 | SETUP_LOGS als Ziel verwechselt? | unbekannt |
| 18 | Externe HDD mit Stick verwechselt? | unbekannt |

## Konkrete Codes (nach Fix)

- `api_unreachable` / `source_missing` / `target_missing` — wenn Discovery nicht lief
- `wifi_missing_but_not_required` — HDD-Modus
- `operator_confirmation_missing` — Bestätigungen fehlen
- `payload_capability_missing` — Spot-check-Failures (Pfade im Squashfs-Check)

## Root Cause (primär)

**Kein Backup-Plan-Contract + Wizard disk_discovery null** — UI zeigte nur „kein Plan“ ohne Fehlercode.

## Fix RS-F2B.1

- `POST /api/rescue/backup/plan` + `rescue_backup_plan_contract.py`
- `RescueBackupPanel` zeigt Ursache, Code, nächsten Schritt
- `execute_allowed=false` bleibt
