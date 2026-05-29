# Rescue ISO — Visual Live System Functional Test Plan

## Sicherer QEMU-Befehl (erlaubt)

```bash
cd /home/volker/piinstaller
export VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1
ISO_PATH="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"

qemu-system-x86_64 \
  -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -no-reboot
```

## Verboten

`-hda`, `-drive`, `/dev/sd*`, USB-Passthrough, Host-Mount, Installation, Restore.

## Operator-Checkliste (im Live-System)

1. Bootloader / Kernel / Live sichtbar?
2. Login **user** / **live**?
3. `hostname` → `setuphelfer-rescue`?
4. DE-Tastatur (`/etc/default/keyboard`, `/etc/vconsole.conf`)?
5. `ls /opt/setuphelfer-rescue`
6. `systemctl status setuphelfer-backend.service`
7. `curl -sS http://127.0.0.1:8000/api/version`

**Nicht** auf dem Host `volker-ROG-Strix` prüfen — nur in der VM.

JSON: `rescue_iso_visual_live_system_functional_test_plan_latest.json`
