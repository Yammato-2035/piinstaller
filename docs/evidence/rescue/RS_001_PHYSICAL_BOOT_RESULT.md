# RS-001 Physical Boot Result

**Updated:** 2026-06-09  
**HEAD (analysis):** `0bbe01b`  
**RS-001 status:** **yellow**

---

## Hardware observation (operator Phase 3 retest)

| Field | Value |
|-------|-------|
| UEFI | reached |
| GRUB | reached |
| Old dialog visible | **yes** (whiptail OK / start-assistant) |
| Modern rescue shell visible | **no** |
| Only OK dialog | yes |
| Live-Medium warning | yes (legacy flow; squashfs fix on stick) |
| Network/WLAN wizard before failure | no (wizard after OK) |
| Message „Keine WLAN-Netze gefunden“ | yes |
| systemd-networkd-wait-online failed | yes |
| setuphelfer-rescue-telemetry-push failed | yes |
| User-facing flow quality | **failed** |
| Repair/install allowed | **no** |

**Reason:** Old text UI and optional network/telemetry services break offline-first boot flow.

---

## Stick reference

| Field | Value |
|-------|-------|
| Device | `/dev/sdb` |
| FAT label | `SETUPHELFER` |
| GPT partition name | `SETUPHELFER_RESCUE` |
| FAT UUID | `C9C8-394A` |
| SquashFS hash (verified) | `ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a` |

---

## Assessment

- **Not green:** UX flow unusable; optional services surface as failures before calm main menu.
- **Not red:** UEFI → GRUB → dialog path proven; payload hash verified on stick.
- **Next:** Rebuild squashfs with React Rescue Shell foundation; hardware retest for new UI.
