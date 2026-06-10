# RS-001 Physical Boot Result

**Updated:** 2026-06-10  
**HEAD:** `bc75f89`  
**Version:** `1.7.10.1`  
**RS-001 status:** **yellow**

---

## Payload-Stand (aktuell, verifiziert)

| Field | Value |
|-------|-------|
| Commit | `bc75f89` |
| Version | `1.7.10.1` |
| SquashFS on stick | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |
| Payload update | **success** |
| Verify hash gate | **success** |
| React Rescue Shell in SquashFS | **yes** |
| Launcher Fix in SquashFS | **yes** |
| Fallback TUI in SquashFS | **yes** |
| Ready for operator retest | **true** |

Evidence: `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260609_214051`

---

## Hardware observation — 1.7.10.1 retest (2026-06-10)

| Field | Value |
|-------|-------|
| Operator hardware test executed | **no** |
| UEFI Boot Path | **pending** |
| GRUB visible | **pending** |
| Kernel starts | **pending** |
| Live system | **pending** |
| Old whiptail dialog | **pending** |
| Only URL printed | **pending** |
| Usable menu visible | **pending** |
| Menu mode | **pending** |
| Live-Medium warning | **pending** |
| Network failed before menu | **pending** |
| Telemetry failed before menu | **pending** |
| wait-online failed before menu | **pending** |
| Evidence on USB | **no** |

**Reason:** Payload verified on stick; operator hardware boot with 1.7.10.1 not yet performed.

---

## Prior observation — React retest (2026-06-09, superseded)

Alter SquashFS `a54aae1d…` (1.7.10.0):

| Field | Value |
|-------|-------|
| UEFI / GRUB / Live | **reached** |
| React Rescue Shell launcher | **yes** |
| Only URL printed | **yes** |
| Graphical React menu | **no** |
| Network / wait-online / telemetry failed | **yes** |
| Photo | `IMG_31CF232F-F82B-4EF4-AAF7-4176D1539492.jpeg` |

Superseded by Payload-Update auf `0b303d3…`.

---

## Stick reference

| Field | Value |
|-------|-------|
| Device | `/dev/sdb` |
| Model / Serial | Ultra Line / `24111412110686` |
| FAT label | `SETUPHELFER` |
| GPT partition name | `SETUPHELFER_RESCUE` |
| SquashFS hash (verified read-only, 2026-06-10) | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |

---

## Assessment

- **Not green:** Kein Hardware-Retest mit 1.7.10.1-Payload durchgeführt.
- **Not red:** Payload-Update und Hash-Gate erfolgreich; Stick bootfähig laut Struktur-Verify.
- **Next:** Operator Phase-1-Boot — nutzbares Menü (Kiosk oder Fallback-TUI) beobachten und dokumentieren.
