# 02 Carrier Update Build Result

**Status:** `ready_for_carrier_update`  
**Build-ID:** `asus006-tui-baseline-20260807_201650`  
**Branch:** `pi-rs-asus-rootcause-telemetry-006`  
**Git HEAD (workspace, uncommitted 006 changes present):** `b425097ba06b8a889ab95a2feb1ebcf5525ff7fa`  
**Payload Version:** `1.10.3.0`

## Artefakte

| Item | SHA256 |
|---|---|
| Neu SquashFS | `4629ca614c98a290626508d835c905246739b55f90fe02c393ab93b7641d7866` |
| Alt SquashFS (Stick) | `a68baa316413e66bbb56602536f0cf268249c98993d437ca07f2a6a44b692fcd` |
| Neu GRUB | `15497518ea3632eeb728f4e417ee629b9d69f0e89e0ab884ee25a257d38c9d66` |
| Alt GRUB (Stick) | `a58b572170dbb4ad3249e48ddc3978f8eda7df3c7395010f8d56f91c8a793a4b` |

## Zielträger (read-only)

| Feld | Wert |
|---|---|
| Device | `/dev/sda` |
| Fingerprint | `ce2e34b7f5ea4e41` |
| Serial | `24111412110212` |
| Labels | SETUPHELFER + SETUP_LOGS |

## Tests

- targeted 006 / ASUS / FAT32: **118 passed**
- hardware/baseline/rescue slice: **99 passed**
- frontend build: **ok**
- runtime/module/version gates: preexisting drift (kein neuer 006-Blocker für USB-Payload)

## GRUB Default

`ASUS-TUI-BASELINE` (`set default=0`) — kein GUI-/Chromium-Autostart.

## Update-Plan (noch nicht ausgeführt)

1. SquashFS → ESP `live/filesystem.squashfs`
2. GRUB → `boot/grub/grub.cfg` (+ ggf. EFI-Kopie falls vorhanden)
3. SETUP_LOGS unverändert

**Xorg-Test:** verboten bis 2× TUI-Baseline bestanden.

## Nächster Schritt

OPERATOR CONFIRMATION 1 + 2 erforderlich vor Write.
