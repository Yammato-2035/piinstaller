# Parallel Agent Plan — ASUS Autonomous 007

**Campaign:** PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007  
**Workspace:** `/home/volker/piinstaller-asus-emergency-linux-telemetry-003`  
**Branch:** `pi-rs-asus-autonomous-diag-install-007`  
**Base HEAD:** `f413ff68`

## Goal

High-info TUI baseline boot (`ASUS-TUI-BASELINE-HIGHINFO`) ersetzt Single-Hypothesis-Boot-Juggling. Parallel agents deliver analysis and prep work; physical install/write remains dual-confirm gated.

## Boot profile (carrier)

| Item | Value |
|---|---|
| Profile | `ASUS-TUI-BASELINE-HIGHINFO` |
| Based on | `ASUS-TUI-BASELINE` |
| Stick payload | `1.10.5.0` until carrier update |
| Chromium | NOT auto-started |
| Xorg | controlled/isolated probe only (`setuphelfer_xorg_probe=1`) |
| NVIDIA | blacklisted by default (baseline safety) |

## Agent lanes (A–F)

| Lane | Focus | Deliverable |
|---|---|---|
| **A** | High-info profile + Phase0 evidence | Profile flags + this plan / Phase0 docs |
| **B** | Capture / telemetry schema for highinfo | What highinfo must collect vs baseline |
| **C** | Display / DRM / Xorg probe isolation | Probe contract without Chromium/kiosk |
| **D** | Hardware / driver inventory from highinfo boot | Concrete inventory + blockers |
| **E** | Install / dual-confirm safety gates | No NVMe write / no install without dual ACK |
| **F** | Carrier / stick update readiness | Gap vs 1.10.5.0; when carrier update is allowed |

## Hard rules (all lanes)

1. No internal NVMe write without explicit dual operator confirm.
2. No install without dual operator confirm.
3. Do not break existing ASUS profile names/tests; only extend `ASUS_PROFILES`.
4. Stick stays **1.10.5.0** until a documented carrier update.
5. Chromium must not autostart on HIGHINFO; Xorg probe stays isolated.

## Execution order

1. **A** lands profile + Phase0 docs (done in this change).
2. **B–D** run after (or against) one HIGHINFO physical/lab boot evidence pack.
3. **E** gates any install path design.
4. **F** only after B–E consensus that carrier update is required.

Results: `AGENT_RESULTS.md` (sections A–F).
