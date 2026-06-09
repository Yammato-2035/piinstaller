# RS-001 Physical Boot Result

**Updated:** 2026-06-09  
**HEAD:** `17ac7f7` (HW-Retest) → Fix `1.7.10.1`  
**RS-001 status:** **yellow**

---

## Payload-Stand (aktuell)

| Field | Value |
|-------|-------|
| Version | `1.7.10.0` |
| SquashFS on stick | `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820` |
| React Rescue Shell in SquashFS | **yes** (repack verified) |
| Payload update | **success** |
| Verify hash gate | **success** |

---

## Hardware observation — React retest (2026-06-09, Operator)

| Field | Value |
|-------|-------|
| UEFI Boot Path | **reached** |
| GRUB visible | **reached** |
| Live system | **reached** |
| React Rescue Shell launcher visible | **yes** |
| React UI URL visible | `http://127.0.0.1:8765/rescue.html` |
| Graphical React menu visible | **no** |
| Old whiptail dialog | **no** |
| Live-Medium warning | not visible in photo / verify from operator notes |
| Network onboarding failed | **yes** |
| systemd-networkd-wait-online failed | **yes** |
| telemetry-push failed | **yes** |
| Operator hardware test executed | **yes** |
| Photo evidence | `IMG_31CF232F-F82B-4EF4-AAF7-4176D1539492.jpeg` |

**Reason:** React shell reached but no browser/kiosk menu; optional network/telemetry services still fail during boot.

---

## Prior observation (pre-React payload, 2026-06-09 Phase 3)

| Field | Value |
|-------|-------|
| UEFI / GRUB | reached |
| Old whiptail dialog | yes |
| Live-Medium warning | yes |
| React shell | no (alter SquashFS) |

Superseded by React-SquashFS payload update — **neuer Retest ausstehend**.

---

## Stick reference

| Field | Value |
|-------|-------|
| Device | `/dev/sdb` |
| Model / Serial | Ultra Line / `24111412110686` |
| FAT label | `SETUPHELFER` |
| GPT partition name | `SETUPHELFER_RESCUE` |
| SquashFS hash (verified read-only) | `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820` |

---

## Assessment

- **Not green:** Grafisches React-Hauptmenü auf Hardware nicht sichtbar (nur URL auf tty1).
- **Not red:** UEFI→GRUB→Live→React-Launcher erreicht; alter whiptail-Blocker weg.
- **Fix (1.7.10.1):** Launcher Fallback-TUI + offline-first units — **Rebuild/Payload-Update ausstehend**.
- **Next:** SquashFS repack + Payload-Update + HW-Retest (nutzbares Menü, keine Boot-Fail-Units).
