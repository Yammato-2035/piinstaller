# RS-001 Physical Boot Result

**Updated:** 2026-06-10  
**HEAD (Evidence):** `4aed483` → Fix `1.7.10.2`  
**RS-001 status:** **yellow**

---

## Payload-Stand (Stick, verifiziert)

| Field | Value |
|-------|-------|
| Version | `1.7.10.1` |
| SquashFS on stick | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |
| Payload update | **success** |
| Verify hash gate | **success** |

---

## Hardware observation — 1.7.10.1 retest (2026-06-10, Operator)

| Field | Value |
|-------|-------|
| UEFI Boot Path | **reached** |
| GRUB visible | **reached** |
| GRUB logo/theme visible | **no** |
| Kernel / Live system | **reached** |
| React/Kiosk UI visible | **no** |
| Fallback TUI visible | **yes** |
| Fallback TUI status action | **works** |
| Fallback TUI log export action | **works** |
| Fallback TUI network action | **crashes** |
| Old whiptail dialog | **no** |
| Live-Medium warning | **not visible** in screenshots |
| network/telemetry/wait-online failed in beginner flow | **not visible** in screenshots |
| Operator hardware test executed | **yes** |
| Photo evidence | `A2F275B8-…`, `B4095FA5-…`, `448589D2-…` |

**Reason:** Fallback-TUI erreicht; GRUB ohne Theme; React/Kiosk blockiert (kein Browser/Display im SquashFS); Netzwerk-Menü stürzt ab.

---

## Stick reference

| Field | Value |
|-------|-------|
| Device | `/dev/sdb` |
| FAT label | `SETUPHELFER` |
| GRUB theme on ESP | **no** |
| SquashFS hash | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |

---

## Assessment

- **Not green:** Kein nutzbares React-Menü; Netzwerk-Crash; GRUB ohne Branding.
- **Partial success:** Fallback-TUI sichtbar; Status + Log-Export funktionieren.
- **Fix 1.7.10.2:** GRUB-Staging, Fallback-TUI, Netzwerk crash-safe — **Rebuild/ESP-Update ausstehend**.
