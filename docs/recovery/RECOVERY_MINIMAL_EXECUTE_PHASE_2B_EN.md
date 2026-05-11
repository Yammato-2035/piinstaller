# Recovery Minimal Execute Phase 2b (EN)

## Goal
First real but strictly limited single actions inside `target_path` for recovery minimal.

## Core rules
- single-use session
- token required
- no actions outside `target_path`
- no SSH enable, no useradd, no network changes
- no forbidden system calls

## Implemented actions
- write recovery notes
- prepare setuphelfer agent (local source only)
- prepare backend unit (without systemctl)
- SSH/user/network/firewall/backup recorded as plan markers only
