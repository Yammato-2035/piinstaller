# Mint hang after ASUS HID / black screen (20260726T070737Z)

## Operator report
1. Default GRUB: kernel text → black screen → hung; cold start.
2. Text/Debug: hung at ASUS M-Key HID line (`0003:0B05:1866.0001`); power off.

## Root causes addressed
1. `live-media-timeout=30` without `live-media=` **delays** casper autodetection for 30s (silent).
2. Autodetect then scans all block devices including Windows NVMe — can hang/probe forever.
3. ASUS ROG M-Key (`hid_asus`) / hybrid GPU blanking after early console.

## Fix written to stick SETUPHELFER (/dev/sdb1)
- `live-media=/dev/disk/by-uuid/9BC7-3950` (SETUP_LOGS)
- `live-media-path=mint-live` (no leading slash)
- removed `live-media-timeout`
- blacklist `hid_asus,asus_nb_wmi,asus_wmi` (+ nouveau)
- `amdgpu.modeset=0 radeon.modeset=0 nomodeset noplymouth console=tty0`
- `systemd.unit=multi-user.target` (text console, avoid Cinnamon black screen)
- Backup: grub.cfg.bak-before-livemedia-pin-20260726T070737Z

## Retest
Boot default or Text/Debug. Expect casper messages soon after HID lines, then text login (not blank GUI).
Squashfs load (~2.5G) can take 1–3 min on USB — kernel text should keep moving.
