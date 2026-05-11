# Boot Capability Check

## Why
A file-level restore can succeed while boot prerequisites are incomplete.
Boot Capability Check adds a defensive, read-only plausibility assessment.

## Scope
- target path readability
- fstab presence/basic syntax/UUID or PARTUUID references
- boot directory + kernel/initramfs hints
- EFI, GRUB, Raspberry Pi, Windows boot manager hints
- dualboot risk detection

## Non-goals
- no boot repair
- no bootloader changes
- no partition actions
- no write operations

## Status model
- `boot_likely`
- `boot_warning`
- `boot_failed`
- `boot_unknown`

## Integration behavior
- exposed via `POST /api/boot/capability`
- attached as `boot_capability` in `Rescue Execute`
- warnings are follow-up indicators and do not retroactively fail restore success
