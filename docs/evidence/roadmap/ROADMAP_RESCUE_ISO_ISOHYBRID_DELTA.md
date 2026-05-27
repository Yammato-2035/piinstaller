# Roadmap Delta — Rescue ISO isohybrid (2026-05-27)

## Blocker-Status

| Code | Status |
|------|--------|
| RESCUE-BUILD-RSVG-001 | **resolved** (Chroot-Wrapper + prepare) |
| RESCUE-BUILD-BOOTLOGO-001 | **resolved** (Seed bootlogo + auto/clean) |
| RESCUE-BUILD-ISOHYBRID-001 | **open** — Binary-Stage `syslinux-utils` |

## Rescue ISO Build Track

- **yellow / blocked** — kein full-green (kein Boot-/USB-Nachweis)
- Operator-Build erreichte genisoimage (~452 MB), scheiterte an `isohybrid` im Chroot

## Nächster Prompt

`RESCUE_ISO_OPERATOR_RETRY_CONTROLLED_BUILD_AFTER_ISOHYBRID_FIX`

JSON: `roadmap_rescue_iso_isohybrid_delta_latest.json`
