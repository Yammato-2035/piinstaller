# PI-RS-MSI-RETEST-003 — Operator-Beobachtung

| Feld | Wert |
|------|------|
| Testdatum | 2026-07-12 |
| Testbeginn | ca. 22:50 UTC (Session `20260712_225043_boot`) |
| Testende | (Operator: nach ≥2 Min TUI-Nutzung, kontrolliert heruntergefahren) |
| Testgerät | MSI GE63 Raider RGB 8RF / MS-16P5 |
| Payload-Version | 1.10.0.16 |
| Payload-SHA256 | cada647ccc11a545a8b4eb6f42deb8745bdedcd5b1662e738c96d68c987621b5 |
| Bootprofil | setuphelfer_msi_compat=1 nomodeset nouveau.modeset=0 pci=noaer |
| TUI erschien nach | sichtbar nach Boot (Operator) |
| TUI mindestens 120 Sekunden stabil | **ja** (Operator-Bestätigung) |
| Visuelle Beschädigung | nein (Operator) |
| Boot-Progress über TUI sichtbar | nein (Operator) |
| GUI-Menüstatus | gesperrt / MSI-Compat Textmodus |
| GUI-Sperrmeldung | erwartetes Verhalten (Textmodus) |
| TUI nach GUI-Sperre intakt | ja (Operator) |
| Shutdown | kontrolliert (Operator) |
| Fotos | nicht im Git — lokal beim Operator |
| Gefährliche Aktionen | keine |
| Besondere Auffälligkeiten | Automatische Evidence-Erfassung auf dem Stick nach ~11 s Uptime; Timeline enthält kein `tui_mode_selected` trotz sichtbarer TUI |

**Hinweis:** Die Operator-Beobachtung widerspricht der automatisch erfassten Timeline-Lücke. Logs allein reichen für `passed` nicht aus; siehe Acceptance `review_required`.
