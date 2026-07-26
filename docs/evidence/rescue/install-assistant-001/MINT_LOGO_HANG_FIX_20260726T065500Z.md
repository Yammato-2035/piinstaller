# Mint logo hang fix (20260726T065500Z)

## Symptom
Stick hangs at Mint Plymouth logo on Gabriel ASUS ROG G513QM (hybrid GPU).

## Cause
Default casper GRUB entry used `quiet splash` without `nomodeset`/`noplymouth`.

## Fix
- Removed `quiet splash` from Mint casper + ISO-loopback entries
- Added `pci=noaer modprobe.blacklist=nouveau nouveau.modeset=0 nomodeset noplymouth`
- Added `live-media-timeout=30` and `fsck.mode=skip`
- Added menuentry "... — Text/Debug"

## Stick write
- Device: /dev/sda1 SETUPHELFER
- Backup: grub.cfg.bak-before-nosplash-20260726T065500Z
- New default still: Linux Mint 22.2 Installer (direkt vom Stick)

Applied: yes (20260726T065500Z)
