# Abschlussbericht — G513QM Hybrid Graphics Rebuild

## 1. Workspace
- Path/Git-Root: `/tmp/piinstaller-install-assistant-001`
- Repository: `Yammato-2035/piinstaller`

## 2. Branch
- Branch: `pi-rs-install-assistant-001`
- HEAD before work: `9325415c`
- origin/main: `b8651d33`
- Runtime gate: exit 14 (version drift) — no live telemetry claims

## 3. Ausgangsfehler
`install-from-rescue.sh --mode ubiquity` → short CLI → black screen → no console → no installer UI.

## 4. Ursachenbewertung
| Cause | Rating |
|-------|--------|
| X11 handoff (startx as root) | probable |
| VT switch (`openvt -s`) | probable |
| nomodeset/amdgpu.modeset=0 vs GUI | possible/probable interaction |
| missing AMD in image | **excluded** (amdgpu+firmware present) |
| NVIDIA proprietary missing in live | possible for other paths; **not** confirmed for this failure (pack not applied before ubiquity) |
| Secure Boot NVIDIA block | insufficient_evidence |
| Installer process failure | possible (no logs) |

## 5. Grafikstack
- Live: Mint 22.2 / kernel 6.14.0-29-generic
- AMD: module+firmware **passed** in image
- NVIDIA live proprietary vermagic: **blocked** (headers unavailable)
- Nouveau: present in live
- Offline pack: single ABI **580** slim debs on stick

## 6. GRUB
Default **Hybrid Auto**; AMD Safe; NVIDIA diag; Nouveau; Emergency nomodeset; Capture-only.

## 7. Capture/Telemetrie
Capture scripts + `setuphelfer_capture=1`; upload status only `queued_offline` / not_configured — never claimed accepted.

## 8. Stick
Identity-gated Intenso Ultra Line update; pack+GRUB written.

## 9. Tests
7 hybrid/GRUB contract tests passed.

## 10. Sicherheit
Windows-NVMe / BitLocker / EFI / Secure Boot / BIOS / auto-install: **nicht verändert / nicht ausgeführt**.

## 11. Endstatus
```text
implemented_with_remaining_build_blockers
```
Remaining: proprietary NVIDIA modules for exact live kernel 6.14.0-29 (headers/prebuilt missing).

Ready for physical retest of **AMD Hybrid Auto / AMD Safe** installer path — not claiming physical_capture_passed.

## 12. Operator next run
1. First GRUB: **G513QM Rescue Hybrid Auto (AMD display)**
2. If black: **AMD Safe Display**, then **Basic Graphics Emergency**
3. Wait for capture; Run-ID under `SETUP_LOGS/setuphelfer/runs/`
4. `bash .../install-from-rescue.sh --mode inspect`
5. `bash .../install-from-rescue.sh --mode graphics-preflight`
6. `bash .../install-from-rescue.sh --mode start-desktop` (only if no nomodeset)
7. `bash .../install-from-rescue.sh --mode installer-preflight`
8. Only if green: `--mode ubiquity` (no Windows disk)
9. Do **not** claim install success until separate freigegebener Installationslauf
