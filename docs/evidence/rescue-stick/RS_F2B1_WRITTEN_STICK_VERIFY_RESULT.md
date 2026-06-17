# RS-F2B.1 Written Stick Verify

| Prüfung | Ergebnis |
|---------|----------|
| EFI/BOOT/BOOTX64.EFI | OK |
| live/filesystem.squashfs | OK |
| Squashfs SHA256 | OK (3cbfca…) |
| SETUP_LOGS Partition | vorhanden (`/dev/sda2`) |
| SETUPHELFER ESP | OK (`/dev/sda1`) |
| Marker/Capability | RS_F2B1 im Workspace-Payload |
| Evidence/Telemetry-Fähigkeit | Code im neuen Squashfs; Runtime-Test folgt RS-F2B.2 |

Verify: `./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sda`
