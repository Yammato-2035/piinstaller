# Setuphelfer Rescue Live — Controlled Build Tree

- Source HEAD: 937ece3
- Bundle MANIFEST sha256: 1ad9eaef8390af939e21ee06d18766ce9f1101b9eeefee866038a03cf7ca58dd
- **real_iso_build_allowed:** false
- **usb_write_allowed:** false

## Vorbereitung (bereits erledigt durch prepare-controlled-live-build-tree.sh)

1. Temp-Runtime-Bundle unter `config/includes.chroot/opt/setuphelfer-rescue/`
2. Legacy-`rsvg`-Compat unter `config/includes.chroot/usr/local/bin/rsvg` (rsvg-convert)
3. Paketliste, systemd-networkd, local-only Services, Hooks
4. UEFI-x64: `grub-efi-amd64-bin` in `setuphelfer.list.binary`; `auto/config` nutzt `--bootloaders syslinux,grub-efi` wenn live-build es unterstützt

## UEFI-x64 nach Build (Pflicht vor USB/MSI-Test)

Wenn `validate-rescue-iso-uefi-boot.sh` auf der ISO rot ist (live-build 3.0 / nur ISOLINUX):

```bash
./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place binary.hybrid.iso
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh binary.hybrid.iso
```

## ISO-Build (NUR nach Operator-Freigabe)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
./auto/config
# NICHT automatisch:
# lb build
```

Siehe `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`.
