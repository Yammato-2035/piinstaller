# RS-001 Physical Boot Result

**Updated:** 2026-06-10  
**HEAD:** `01ffba3`  
**Version:** `1.7.11.0`  
**RS-001 status:** **yellow**

---

## Payload-Stand (Stick, verifiziert)

| Field | Value |
|-------|-------|
| Version | `1.7.11.0` |
| SquashFS on stick | `a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d` |
| Stick Acceptance | **ok** (L1–4) |
| Hardware Retest Allowed | **true** |
| Payload update | **success** |
| GRUB branding update | **success** |
| Verify hash gate | **success** |

---

## Level 6 Hardware observation — 1.7.11.0 (pending)

| Field | Value |
|-------|-------|
| Operator hardware test executed | **no** (this run) |
| UEFI Boot Path | **pending** |
| GRUB visible | **pending** |
| GRUB logo/theme visible | **pending** |
| Kernel / Live system | **pending** |
| React/Kiosk UI visible | **pending** |
| Fallback TUI visible | **pending** |
| Status / Log export / Network | **pending** |
| Evidence on USB | **no** (pre-retest readback) |

**Reason:** Phase 0 passed; physical boot requires operator on MSI hardware.

---

## Prior observation — 1.7.10.1 retest (2026-06-10)

| Field | Value |
|-------|-------|
| UEFI / GRUB / Live | **reached** |
| GRUB theme | **no** |
| Fallback TUI | **yes** (Status/Logs OK) |
| Network | **crashes** |
| React/Kiosk | **no** |
| Photo evidence | `A2F275B8-…`, `B4095FA5-…`, `448589D2-…` |

---

## Stick reference

| Field | Value |
|-------|-------|
| Device | `/dev/sdb` |
| FAT label | `SETUPHELFER` |
| GRUB theme on ESP (host verify) | **yes** |
| SquashFS hash | `a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d` |

---

## Assessment

- **Not green:** Level 6 hardware retest with 1.7.11.0 not yet executed.
- **Ready:** Stick acceptance ok; operator may boot.
- **Next:** Operator Phase 1 → USB log export → status decision.
