# RS-001 Live-Medium Retest — Operator Handoff

**Date:** 2026-06-09  
**RS-001:** yellow  
**ready_for_operator_retest:** **true**

---

## Voraussetzungen erfüllt

| Check | Status |
|-------|--------|
| SquashFS-Hash auf Stick | `ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a` |
| `.sqtmp` entfernt | **ja** |
| Verify mit `--expected-squashfs-sha256` | **success** |
| Live-Medium-Fix im SquashFS | **ja** |

---

## Hardware-Retest (MSI/Referenzhardware)

1. UEFI-Bootmenü zeigt Stick (`/dev/sdb`, UUID `C9C8-394A`)
2. GRUB erscheint
3. „Setuphelfer Rettung starten“ startet
4. **Keine** Warnung „Live-Medium nicht stabil“
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
- `docs/evidence/rescue/RS_001_PHYSICAL_BOOT_RESULT.md` aktualisieren
