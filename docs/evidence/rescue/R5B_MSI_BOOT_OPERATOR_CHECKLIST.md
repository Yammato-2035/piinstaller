# R.5B — MSI Boot Operator Checklist

**Ziel:** Rescue-Stick am MSI-Laptop validieren (nach erfolgreichem R.5B USB-Write).  
**Regel:** Keine Backup-/Restore-/Partition-Schreibaktionen.

## Vorbereitung

- [ ] R.5B USB-Write + Verify abgeschlossen
- [ ] ISO SHA256 auf Stick dokumentiert: `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143`
- [ ] MSI ausgeschaltet, kein anderes Boot-Medium

## Boot-Schritte

1. [ ] MSI **ausschalten**
2. [ ] Rescue-**Stick einstecken** (USB-Port direkt, kein Hub wenn vermeidbar)
3. [ ] **Bootmenü** öffnen (z. B. F11/F12/DEL — modellabhängig)
4. [ ] **UEFI:** Eintrag **SETUPHELFER** / **SETUPHELFER_RESCUE** / USB-EFI wählen
5. [ ] **Nicht** interne Windows/Linux-Disk booten

## Sichtprüfung Boot

| Check | Erwartung | Ist | Ampel |
|-------|-----------|-----|-------|
| Grafisches GRUB sichtbar | optional (yellow in R.5A) | | |
| Setuphelfer-Logo / Theme | PNG sichtbar wenn Theme aktiv | | |
| Fallback-Menü (ISOLINUX/GRUB text) | Rescue-Menüeintrag | | |
| Linux startet | Live-System lädt | | |
| TUI / Start-Assistant | TTY1 erreichbar | | |
| Browser / Kiosk | chromium-Kiosk oder TUI-Fallback | | |
| React Rescue UI | rescue.html im Browser | | |
| WLAN-Menü | network-onboarding erreichbar (read-only test) | | |
| Logs auf Stick | `/setuphelfer-evidence/` wächst | | |

## Verboten während Test

- [ ] **Kein** Backup starten
- [ ] **Kein** Restore / Partition-Write
- [ ] **Kein** `dd` / `mkfs` / `parted` am MSI-Zielsystem

## Abschluss

8. [ ] Nach Test **sauber herunterfahren** (`poweroff`)
9. [ ] Stick zurück an **Entwicklungsrechner**
10. [ ] `/setuphelfer-evidence/` auswerten → **R.5C MSI Boot Evidence Review**

## Evidence-Ziele (R.5C)

- Fotos/Screenshots nur ohne Secrets
- `kiosk_report_latest.json`, `rescue-ui-status.json` vom Stick
- Testmatrix R.4 Ampeln aus Runtime
