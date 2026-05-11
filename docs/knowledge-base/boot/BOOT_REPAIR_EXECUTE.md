# Boot Repair Execute

## Scope
Controlled execution layer for single boot-repair actions bound to repair session + token.

## Controls
- immutable action+target binding in session
- expiry + single-use token
- prechecks and post-check
- strict allowlist and policy blocks

## Explicit non-goals
- no batch repair
- no automatic Windows/dualboot handling
- no hidden chained actions
