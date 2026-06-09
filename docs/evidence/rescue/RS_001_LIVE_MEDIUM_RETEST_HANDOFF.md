# RS-001 Live-Medium Retest — Operator Handoff

**Date:** 2026-06-08  
**RS-001:** yellow (pending retest)  
**ready_for_operator_retest:** true (after squashfs with fix is on stick)

---

## Ziel

Erneuter Hardware-Boot mit **bestehendem** FAT32-ESP-Stick (`/dev/sdb`, UUID `C9C8-394A`) — Warnung „Live-Medium nicht stabil“ darf **nicht** mehr erscheinen.

---

## Nicht in diesem Retest

- kein USB neu schreiben (außer gezielter SquashFS-Austausch nach ISO-Rebuild — separater Operator-Lauf)
- kein Backup / Restore / Provisioning
- keine Reparatur / Installation starten

---

## Voraussetzung

Der Fix liegt in `setuphelfer-rescue-live-medium-check.py` **innerhalb** `live/filesystem.squashfs`.  
Der aktuelle Stick enthält noch die **alte** Squashfs-Version.

**Option A (empfohlen):** Controlled ISO rebuild → Squashfs auf Stick aktualisieren (Operator-Lauf, nicht Cursor).  
**Option B:** Einmaliger Test: aktualisierte Skripte manuell in laufendes Live-System kopieren (nur Diagnose).

---

## Operator prüft

1. UEFI-Bootmenü zeigt Stick
2. GRUB erscheint
3. Standard-Eintrag „Setuphelfer Rettung starten“ startet
4. Warnung **„Live-Medium nicht stabil“** erscheint **nicht**
5. Setuphelfer-Menü/TUI erscheint
6. Optional: `cat /run/setuphelfer-rescue/media-check.json` → `live_media_runtime_stable: true`
7. **Keine** Reparatur/Installation starten

---

## RS-001 grün nur wenn

Setuphelfer-Menü/TUI **ohne** Live-Medium-Warnung erreicht wird.

---

## Evidence liefern

- Screenshot/Foto Bootmenü + TUI
- `media-check.json` Inhalt
- Kurzbericht in `docs/evidence/rescue/RS_001_PHYSICAL_BOOT_RESULT.md` aktualisieren
