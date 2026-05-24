# Rescue Stick — Controlled ISO Preparation Gate

**Version:** 1.2
**real_iso_build_allowed:** `false` (ISO-Build-Versuch fehlgeschlagen — Operator sudo nötig)
**usb_write_allowed:** `false`

## Gate-Status (2026-05-24 — ISO Build Execution)

**ISO_BUILD_FAILED** — Validatoren grün, Tools ok, Build ohne root/sudo nicht abgeschlossen.

| # | Bedingung | Status |
|---|-----------|--------|
| 1 | Temp Runtime Bundle validiert | **pass** |
| 2 | Live-build Tree validiert | **pass** |
| 3 | Toolcheck lb/xorriso | **pass** |
| 4 | ISO gebaut + SHA256 | **fail** — chroot/root |
| 5 | Live-OS Validation | **review_required** |
| 6 | USB Write | **blocked** |
| 7 | Operator ISO-Freigabe | **pass** (Auftrag) |

## Bekannte Build-Blocker (aktualisiert)

- ~~`auto/config` ohne `noauto`~~ → **behoben**
- **`lb build` ohne `noauto`** → ruft blockiertes `auto/build` auf — **`sudo lb build noauto` verwenden**
- **Verunreinigter chroot** nach fakeroot/cache → vor Retry `chroot cache binary local .build` löschen
- **`lb build noauto`** → **root/sudo** erforderlich

## Flags

- **real_iso_build_allowed:** `false` (kein Artefakt)
- **usb_write_allowed:** `false`
- **next_gate:** Operator `sudo lb build noauto` + SHA256-Evidence

## Referenzen

- `RESCUE_CONTROLLED_ISO_BUILD_RESULT.md`
- `RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
