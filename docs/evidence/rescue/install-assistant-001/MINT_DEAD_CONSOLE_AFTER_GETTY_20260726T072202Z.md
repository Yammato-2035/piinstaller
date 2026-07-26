# Dead console after getty/CUPS (20260726T072202Z)

## Operator
Boot reaches getty.target + cups.service OK, but no usable login console; machine appears hung.

## Hypothesis
nomodeset + kept GRUB gfxpayload leaves VT/framebuffer unusable while systemd still reports getty started.

## Stick fix
- `set gfxpayload=text` in Mint entries
- `systemd.debug-shell=1` (Ctrl+Alt+F9 → root)
- New: Rescue-Root, Emergency bash, Text mit amdgpu
- mask lightdm/mdm/gdm
- Backup: grub.cfg.bak-before-dead-console-20260726T072202Z

## Retest order
1. Rescue-Root
2. Emergency bash
3. Text mit amdgpu
4. Default + Ctrl+Alt+F9
