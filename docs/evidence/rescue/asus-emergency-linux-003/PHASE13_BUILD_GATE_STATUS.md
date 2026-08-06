# PHASE 13 – Build-/Carrier-Gate-Status

Stand: 2026-08-06  
Branch: `pi-rs-asus-emergency-linux-telemetry-003` @ `182a53c1`  
Workspace: `/tmp/piinstaller-asus-emergency-linux-telemetry-003`  
(**Hinweis:** `/tmp`-Worktree — bei System-Cleanup gefährdet; Branch ist nach Origin gepusht.)

## Gates

| Gate | Ergebnis |
|------|----------|
| `check-runtime-deploy-gate.sh` | Exit 0 (Legacy/Profil-Hinweis; kein Live-`/opt`-Deploy-Erfolg behauptet) |
| `check-module-boundaries.sh` | Exit 0, Status `review_required` (vorbestehend; keine neuen ASUS-Hits) |
| Version-Consistency | `ok=True` (`project_version` 1.10.1.0) |
| USB_WRITE_ALLOWED (Phase 2) | `true` nach Remediation |
| Sentinel-Unit-Tests | 14 passed |

## Build-Artefakte in diesem Worktree

- `build/rescue/filesystem.squashfs.repacked-*`: **nicht vorhanden**
- Controlled live-build ISO: **nicht vorhanden**
- Payload-SoT weiterhin `rescue_payload_version` **1.10.0.16** (älter als Projekt **1.10.1.0**)

## Blocker für sofortigen USB-Write

1. Kein verifiziertes Build-/Payload-Artefakt mit ASUS-Sentinel-/Profil-Inhalt in diesem Worktree.
2. Physische Zielidentität (64-GB-Stick) und doppelte Operatorbestätigung fehlen (Phase 14–15).
3. ASUS-Bootprofile/Sentinels sind im Code, aber noch nicht in ein signiertes Carrier-Image eingebacken.

## Erlaubter nächster Build-Pfad (Operator)

Option A — Repack aus vorhandenem SquashFS-Quellartefakt (wenn auf dem Host vorhanden):

```bash
# nur nach Preflight / UI-Smoke; kein Blind-Write
bash scripts/rescue-live/repack-rescue-squashfs-react-shell.sh
```

Option B — Controlled ISO-Build (lang, sudo/clean ggf. nötig):

```bash
bash scripts/rescue-live/preflight-developer-controlled-iso-build.sh
# danach prepare + run-controlled-iso-build-with-logging.sh gemäß Runbook
```

Danach offizieller Writer:

`scripts/rescue-live/write-fat32-esp-rescue-usb.sh`  
mit Zielidentität ≠ interne NVMe, zwei Bestätigungen, Verify-Skript.

## Status

`implemented_pending_carrier_build_and_physical_usb_identity`

Kein `physical_carrier_written_and_verified`.
