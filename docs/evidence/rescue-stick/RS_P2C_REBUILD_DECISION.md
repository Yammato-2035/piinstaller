# RS-P2C Rebuild Decision

| Entscheidung | Wert | Begründung |
|--------------|------|------------|
| squashfs_update_required | true | Entrypoint, TUI, Watchdog, Backend-Contracts |
| grub_esp_update_required | true | Neues Plain-GRUB-Menü, neue Kernel-Parameter |
| squashfs_update_sufficient | false | GRUB liegt auf ESP, nicht nur Squashfs |
| full_usb_rewrite_required | false | ESP-GRUB + Payload-Update reicht (kanonische Skripte) |

## Kanonische Pfade

- Squashfs: `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh`
- GRUB ESP: `scripts/rescue-live/update-fat32-esp-grub-branding.sh`
- Payload: `scripts/rescue-live/update-fat32-esp-live-payload.sh`

## Neuer Squashfs

- Version: 1.9.5.2
- SHA256: `843d93b2fabbcd59b5d5c6cc7c36e192b3cd8bb1c543d98aae1441829e8bfc26`

## Stick-Update

`/dev/sda` beim Build-Lauf **nicht angeschlossen** — ESP/Payload-Update ausstehend (Operator, RS-P2D-Vorbereitung).
