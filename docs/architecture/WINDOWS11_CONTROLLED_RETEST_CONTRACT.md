# WINDOWS11_CONTROLLED_RETEST_CONTRACT

**Task:** PI-RS-ASUS-WIN11-RETEST-005  
**Module:** `backend/core/rescue_windows11_controlled_retest.py`

## Purpose

Controlled two-stage Windows 11 retest on `asus_rog_gabriel` (G513QM):

- **Stage A:** BIOS `G513QM.331` + full WinPE/Setup log collection  
- **Stage B:** BIOS `G513QM.335` only after justified gate, otherwise identical constants

## Hard rules

- No Windows install without machine + NVMe identity binding.
- No device selection by disk number or capacity alone.
- Linux NVMe must be isolated before Setup wipe.
- No BIOS flash in Stage A; no Linux flash tools.
- No fake-green for “installer started”.
- Linux remains locked until Windows postcheck passes.

## Endstatuses

See `ENDSTATUSES` in the module. Physical Stage A pending → `ready_for_windows_retest_bios331`.
