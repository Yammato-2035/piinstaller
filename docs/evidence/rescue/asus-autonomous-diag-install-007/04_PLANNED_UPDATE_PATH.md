# Planned official update path (no write yet)

## 1) SquashFS + VERSION/Manifest

```bash
./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target /dev/sda \
  --new-squashfs build/rescue/filesystem.squashfs.repacked-1.10.6.0 \
  --expected-sha256 4521968ef8df2e3d35bc44210e3345a0056cfe595a31472720398d95370b57ec \
  --expected-version 1.10.6.0 \
  --operator-confirm-update \
  --confirm-phrase 'UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD' \
  --execute-update
```

Preserves partition table and `SETUP_LOGS`.

## 2) GRUB → HIGHINFO default

Stick currently defaults to `ASUS-TUI-BASELINE` and has **no** HIGHINFO entry.
Payload-only update is insufficient for Boot3 HIGHINFO default.

Use official GRUB branding/update path after payload update:

```bash
./scripts/rescue-live/update-fat32-esp-grub-branding.sh \
  --target /dev/sda \
  --operator-confirm-update \
  --confirm-phrase 'UPDATE SETUPHELFER FAT32 ESP GRUB BRANDING' \
  --execute-update \
  --allow-mounted   # only if still mounted and script requires it
```

Verify default menuentry: `ASUS-TUI-BASELINE-HIGHINFO`.

## 3) Readback

- Payload `1.10.6.0`
- SquashFS SHA match
- GRUB default HIGHINFO
- `SETUP_LOGS` intact
- Status only then: `carrier_1_10_6_0_verified`
