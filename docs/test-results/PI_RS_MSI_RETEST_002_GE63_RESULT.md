# PI-RS-MSI-RETEST-002 GE63 Result

Stand: 2026-07-12 (Operator-Boot durchgeführt)

## Status

**`partial_fail`** — Boot mit Payload **1.10.0.13** am MSI GE63 bestätigt; TUI durch PCIe-AER-Flut nahezu unbrauchbar; GUI-Start fehlgeschlagen.

## Payload

| Feld | Wert |
|------|------|
| Workspace version | 1.9.19.5 |
| Stick/Payload version | **1.10.0.13** |
| Payload SHA256 | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |
| Boot-Session SETUP_LOGS | `20260712_002439` |
| USB verify | success (PI-RS-USB-TELEMETRY-001) |

## Boot

| Check | Ergebnis |
|-------|----------|
| Boot erfolgreich | **ja** (GE63 Raider RGB 8RF / MS-16P5) |
| GRUB-Eintrag | Default „sicherer Textmodus“ **ohne** `pci=noaer` / MSI-Compat |
| TUI visible | **ja, aber nahezu unbrauchbar** (Operator + ~428 AER-Zeilen) |
| Schwarzer Bildschirm | **nein** |
| GUI result | **fehlgeschlagen** — `startx_not_started`, openvt VT2-Fehler |
| Backend/API result | *nicht separat geprüft* (disk-discovery: TypeError) |
| SETUP_LOGS beschreibbar | **ja** (Diagnostics persistiert) |

## Hardware / PCIe

| Check | Ergebnis |
|-------|----------|
| MSI GE63 Raider confirmed | **ja** (dmidecode/meta) |
| Killer E2500 @ 05:00.0 | **ja** (Treiber alx) |
| PCIe/AER warnings | **ja — massiv** (~428 Journal-Zeilen, BadDLLP/BadTLP/Timeout) |
| WLAN Intel | Treiber geladen (iwlwifi) |
| Kritische Fehler (fatal) | **nein** (nur Corrected AER) |

## GUI-Start-Kette (SETUP_LOGS)

```
gui-watchdog.json: gui_failed=true, code=startx_not_started
rescue-ui-status.json: status=failed, reason=startx_not_started
gui-start.log: openvt „Konsole 2 konnte nicht freigegeben werden“, Kiosk-PID Exit nach 4s
```

## Telemetry

| Check | Ergebnis |
|-------|----------|
| Preview vom gebooteten Stick | **nein** |
| Lab Send vom gebooteten Stick | **nein** |

## Root Cause (vorläufig)

Default-GRUB-Eintrag auf dem Stick enthält **keine** MSI-Mitigation (`pci=noaer`, `setuphelfer_msi_compat=1`). Separater Menüpunkt „MSI/NVIDIA Kompatibilitätsmodus (Text)“ existiert, wurde aber offenbar nicht gewählt.

Evidence: `stick-grub-boot-entry-analysis.txt`

## Evidence

| Feld | Wert |
|------|------|
| Sprint doc | `docs/rescue-stick/PI_RS_MSI_RETEST_002_GE63_PAYLOAD_1_10_0_13.md` |
| Evidence dir | `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/` |
| Boot import | `imported-setup-logs/20260712-msi-boot/` |
| Operator feedback | `operator-feedback-20260712.txt` |

## Safety

| Check | Ergebnis |
|-------|----------|
| backup/restore/wipe | **nein** |
| lab send | **nein** |
| USB write | **nein** |

## Nächster Schritt

1. **MSI erneut booten** mit Menüpunkt „Setuphelfer MSI/NVIDIA Kompatibilitätsmodus (Text)“
2. TUI-Bedienbarkeit + optional GUI erneut prüfen
3. GRUB-Default auf Stick an MSI-Compat anpassen (separater Fix-Sprint, kein USB-Write ohne Freigabe)
