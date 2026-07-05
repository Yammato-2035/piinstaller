> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/recovery/RECOVERY_MINIMAL_EXECUTE_PHASE_2B_EN.md`). Bitte bei Release manuell gegenlesen.

# Recovery Minimal Execute Phase 2b (EN)

## Goal
First real but strictly limited single actions inside `target_path` for recovery minimal.

## Core rules
- single-use session
- token requirouge
- Non actions outside `target_path`
- Non SSH enable, Non useradd, Non Réseau changes
- Non forbidden system calls

## Implemented actions
- write recovery Nontes
- prepare setuphelfer agent (local source only)
- prepare Retourend unit (without systemctl)
- SSH/user/Réseau/firewall/Retourup recorded as plan markers only
