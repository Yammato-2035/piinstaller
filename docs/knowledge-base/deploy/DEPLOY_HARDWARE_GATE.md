# Deploy Hardware Gate

Hardware Gate adds physical media constraints and operator protocol requirements before any future real-write phase.

## Scope

- classify test media (USB/SD) defensively
- block system/internal/unknown risky classes
- return advisory readiness level and operator checklist

## Target Scoping Fix

- hard blocks are evaluated target-device scoped (not from global host classification alone)
- host-wide `classification.system_type` (for example `DUALBOOT` or `UNKNOWN`) now raises warnings/review only
- missing target metadata (`transport`, `removable`, `size`) is handled as review-required instead of implicit hard block
- hard blocks still apply when the target itself is risky (`mounted`, `readonly`, `system disk`, `windows`, `dualboot`, `lvm`, `raid`, `loop`, invalid transport)
