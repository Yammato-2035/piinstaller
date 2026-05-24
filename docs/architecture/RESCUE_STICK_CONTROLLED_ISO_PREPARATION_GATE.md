# Rescue Stick — Controlled ISO Preparation Gate

**Version:** 1.1
**real_iso_build_allowed:** `false`
**usb_write_allowed:** `false`

## Zweck

Definiert Voraussetzungen für **ISO-Vorbereitung** und **Controlled Live Build Tree** — **kein** automatischer ISO-Build.

## Gate-Status (2026-05-24 — Controlled Live Build Tree)

**ISO_BUILD_PREP_REVIEW_REQUIRED**

| # | Bedingung | Status |
|---|-----------|--------|
| 1 | Temp Runtime Bundle validiert | **pass** |
| 2 | Live-build Tree validiert | **pass** — Validator Exit 0 |
| 3 | Paketliste + systemd-networkd + Services | **pass** — versioniert im Tree |
| 4 | auto/build blockiert | **pass** — Exit 20 |
| 5 | Toolcheck (`lb`, xorriso) | **fail** — fehlen auf Host |
| 6 | Live-Medium Network Validation green | **fail/review** — kein Live-Boot |
| 7 | Keine Build-Artefakte (ISO/squashfs) | **pass** |
| 8 | Runbooks ISO + USB Gate | **pass** |
| 9 | Operator ISO-Freigabe | **fail** |
| 10 | Operator USB-Write-Freigabe | **fail** |

## Controlled ISO Build Prep

| Status | Bedeutung |
|--------|-----------|
| **ISO_BUILD_PREP_REVIEW_REQUIRED** | Tree ready; Tools fehlen; Live-OS offen |
| ISO_BUILD_PREP_READY | Alle Validatoren + Tools + Evidence (noch nicht) |
| ISO_BUILD_PREP_BLOCKED | Secrets/verbotene Artefakte (nicht der Fall) |

## Flags

- **real_iso_build_allowed:** `false`
- **usb_write_allowed:** `false`
- **next_gate:** Operator installiert `live-build` → Freigabe → `lb build` (Runbook)

## Freigabe-Workflow

1. Toolcheck grün (`RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md`)
2. Build-Tree Validator Exit 0
3. Operator schriftliche ISO-Build-Freigabe
4. `RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md` — **manuell** `lb build`
5. USB separat: `RESCUE_USB_WRITE_GATE_RUNBOOK.md`

## Referenzen

- `RESCUE_CONTROLLED_ISO_BUILD_PREP_RESULT.md`
- `RESCUE_BIG_STEP_STATUS_PLAN.md`
- `RESCUE_STICK_READONLY_BUILD_GATE.md`
