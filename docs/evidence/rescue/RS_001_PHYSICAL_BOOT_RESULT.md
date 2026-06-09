# RS-001 Physical Boot Result

**Updated:** 2026-06-08  
**HEAD (analysis):** `158b9da`  
**RS-001 status:** **yellow**

---

## Hardware observation (operator)

| Field | Value |
|-------|-------|
| USB Write | success |
| USB Verify | success |
| UEFI Boot Path | reached |
| GRUB visible | yes |
| Setuphelfer dialog visible | yes |
| Warning | **Live-Medium nicht stabil** |
| Repair/install allowed | **no** |

**Reason:** Physical boot reaches Setuphelfer warning dialog, but live-medium stability check blocks operation.

---

## Stick reference

| Field | Value |
|-------|-------|
| Device | `/dev/sdb` |
| FAT label | `SETUPHELFER` |
| GPT partition name | `SETUPHELFER_RESCUE` |
| FAT UUID | `C9C8-394A` |
| Evidence run | `fat32_esp_write_20260608_220511` |

---

## Assessment

- **Not green:** Warning dialog still appears; repair/install correctly blocked.
- **Not red:** UEFI → GRUB → Setuphelfer TUI path is proven on reference hardware.
- **Next:** Operator retest after live-medium check fix is baked into squashfs (see `RS_001_LIVE_MEDIUM_RETEST_HANDOFF.md`).
