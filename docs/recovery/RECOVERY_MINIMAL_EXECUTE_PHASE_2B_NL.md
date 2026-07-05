> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/recovery/RECOVERY_MINIMAL_EXECUTE_PHASE_2B_EN.md`). Bitte bei Release manuell gegenlesen.

# Recovery Minimal Execute Phase 2b (EN)

## Goal
First real but strictly limited single actions inside `target_path` for recovery minimal.

## Core rules
- single-use session
- token requirood
- Nee actions outside `target_path`
- Nee SSH enable, Nee useradd, Nee Netwerk changes
- Nee forbidden system calls

## Implemented actions
- write recovery Neetes
- prepare setuphelfer agent (local source only)
- prepare Terugend unit (without systemctl)
- SSH/user/Netwerk/firewall/Terugup recorded as plan markers only
