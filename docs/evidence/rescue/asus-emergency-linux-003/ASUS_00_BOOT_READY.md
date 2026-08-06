# ASUS-00 Bootpaket — Bereitschaft

## Status

Carrier verifiziert. **ASUS-00 FORENSIC TUI SAFE** ist Default-Menüeintrag (Index 0).

## Notizen

| Feld | Wert |
|------|------|
| Carrier-Version (ESP) | 1.10.2.0 |
| Payload SquashFS | 1.10.2.0 / Module inkl. Sentinels+Spooler |
| Build-ID | `asus-carrier-004-20260806T195318Z` |
| ISO-SHA256 | `ce3258f945ea2f973414ed6bdca29f884be9415f66e06a0e9110e6d6b0f87473` |
| ASUS-RECOVERY | im Menü sichtbar |
| SETUP_LOGS | Partition vorhanden, Label `SETUP_LOGS`, beschreibbar nach Mount |
| Telemetrie-Consent | Bootparameter `setuphelfer_telemetry_opt_in=1` (Offline-Spool im Image) |
| Intern NVMe | keine Schreibaktionen vorbereitet |

## Operator-Boot

1. Stick sicher aushängen (falls noch gemountet).
2. Am ASUS ROG im UEFI den USB-Stick wählen.
3. Nur **ASUS-00** booten — keine weiteren Profile ohne neuen Auftrag.
4. Run-ID am Gerät notieren; Evidence unter SETUP_LOGS sichern.

ASUS-00 bleibt: **FORENSIC TUI SAFE**.
