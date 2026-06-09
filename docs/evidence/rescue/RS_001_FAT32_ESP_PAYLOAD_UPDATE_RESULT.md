# RS-001 FAT32 ESP Live Payload Update — Result

**Datum:** 2026-06-09 (Staging-Cleanup abgeschlossen)  
**Version:** `1.7.9.5`  
**RS-001:** yellow — **ready_for_operator_retest: true**

---

## Zusammenfassung

| Feld | Wert |
|------|------|
| SquashFS auf Stick | **ac95ebc3…** (neu, verifiziert) |
| Payload kopiert | **ja** |
| Metadata geschrieben | **ja** |
| `.sqtmp` entfernt | **ja** |
| Verify mit Hash-Gate | **success** |
| Hardware-Retest | **freigegeben** |

---

## Verlauf

1. Lauf `fat32_esp_payload_update_20260609_165459`: SquashFS + Metadata OK, Verify failed wegen `.sqtmp`.
2. Staging-Cleanup: nur `/media/gabriel/SETUPHELFER/.sqtmp` entfernt (kein Re-Copy).
3. Verify erneut: `OK: filesystem.squashfs sha256 matches expected`, Exit 0.

---

## Operator — Hardware-Retest

```text
UEFI → GRUB → Setuphelfer-TUI ohne "Live-Medium nicht stabil"
```

Evidence nach Retest: `docs/evidence/rescue/RS_001_PHYSICAL_BOOT_RESULT.md`
