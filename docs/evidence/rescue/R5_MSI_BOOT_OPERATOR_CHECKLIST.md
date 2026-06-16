# R.5 — MSI Boot Operator-Checkliste

**Gate C:** MSI-Boot nur **manuell** durch Operator. Agent/Cursor darf Erfolg nicht annehmen.

---

## Vorbereitung

- [ ] Neues ISO gebaut (Gate A) und auf Stick geschrieben (Gate B)
- [ ] `verify-fat32-esp-rescue-usb.sh` grün
- [ ] MSI interne Datenträger **nicht** angeschlossen zum Schreiben

## Boot-Schritte

1. MSI **ausschalten**
2. Setuphelfer-Rettungsstick einstecken (nur bestätigtes Ziel)
3. Bootmenü öffnen (F11/F12/DEL je nach MSI)
4. **UEFI**-USB-Stick wählen
5. Beobachten und notieren:

| Beobachtung | ja/nein | Notiz |
|-------------|---------|-------|
| Grafisches GRUB sichtbar | | |
| Setuphelfer-Logo/Theme | | |
| Fallback ISOLINUX/BIOS | | |
| Linux startet | | |
| TUI (whiptail) startet | | |
| Browser/Kiosk startet | | |
| React UI sichtbar | | |
| WLAN-Menü erreichbar | | |
| Logs auf Stick (`/setuphelfer-evidence/`) | | |

## Verboten während Test

- Keine internen Laufwerke beschreiben
- Kein Restore / Backup-Execute
- Keine Partition-Write-Aktionen

## Nach Test

1. Herunterfahren (nicht Hibernate auf interne Platte schreiben lassen)
2. Stick am **Entwicklungsrechner** einlesen
3. Evidence kopieren/auswerten → `R5_STICK_EVIDENCE_REVIEW.md`
4. Bei Bootfehler: **Fotos/Notizen** in `docs/evidence/rescue/R5_MSI_BOOT_OPERATOR_NOTES.md` (ohne PII/Secrets)

## Hilfsbefehle auf dem Stick (falls Shell erreichbar)

```bash
setuphelfer-rescue-evidence.py detect
setuphelfer-rescue-evidence.py bundle
setuphelfer-rescue-kiosk-health
```
