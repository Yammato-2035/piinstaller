# USB-Rewrite-Handoff — nach Start Assistant ISO (1.7.7.0)

**Kein dd durch Agent.** Nur Operator-Anleitung.

Post-Build-Validierung: `RESCUE_START_ASSISTANT_POST_BUILD_VALIDATION_RESULT.md` — **grün**, Handoff freigegeben.

## Kanonische ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| **SHA256** | **`3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7`** |
| Größe | **683671552** bytes (~652 MiB) |
| Version | **1.7.7.0** |
| Build | `LB_EXIT=0`, UEFI post-patch `validate_exit=0` |

Vorherige Stick-ISO (Telemetrie-Automation): `80508492a8f3187e79bb700675d81eac3e19f8e5647bb5b4a84febcf6c8b32f0`

## Neu in dieser ISO (validiert)

- Setuphelfer Start Assistant (Wizard, read-only Pläne)
- Robustes WLAN-Onboarding (NetworkManager, whiptail)
- Automatische Telemetrie-Push + Retry-Timer
- Disk-Discovery + Plan-Builder
- Branding + vollständiges ISOLINUX-Boot-Menü (`MENU TITLE Setuphelfer Rettungsstick`)

## Ziel-Stick (read-only erfasst)

| Feld | Wert |
|------|------|
| Gerät | **`/dev/sdb`** |
| Modell | Ultra Line |
| Serial | `24111412110212` |
| Aktuell gemountet | `/media/gabriel/SETUPHELFER_RESCUE` |

**Nicht** `/dev/sda` (Backup-Platte) verwenden.

## Operator — Rewrite

```bash
cd /home/volker/piinstaller
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
TARGET=/dev/sdb

sha256sum "$ISO"
# Erwartung: 3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7

stat -c '%s bytes' "$ISO"
# Erwartung: 683671552 bytes

lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,FSTYPE,LABEL,MOUNTPOINTS /dev/sda /dev/sdb

udisksctl unmount -b /dev/sdb1 2>/dev/null || true
sync
sudo dd if="$ISO" of="$TARGET" bs=4M status=progress conv=fsync
sync
```

## Operator — Block-Readback SHA256

```bash
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
ISO_SIZE=$(stat -c '%s' "$ISO")
sudo python3 - <<PY
import hashlib
from pathlib import Path
size=int("$ISO_SIZE")
h=hashlib.sha256()
remaining=size
with Path("/dev/sdb").open("rb", buffering=0) as f:
    while remaining:
        chunk=f.read(min(4194304, remaining))
        if not chunk:
            break
        h.update(chunk)
        remaining -= len(chunk)
print("STICK_SHA256=", h.hexdigest())
print("EXPECTED   =", "3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7")
PY
```

Nach erfolgreichem Readback: `usb_write_sha256_verified=true` in Gate-Status setzen.

## Nach Rewrite — empfohlene Folge-Prompts

1. MSI-Boot mit **Setuphelfer Rettung starten** oder **Netzwerk-Assistent**
2. Telemetrie-Health gegen LAN-Proxy `192.168.178.140:8001`
3. Start-Assistant-Wizard smoke (read-only, keine Schreibaktionen)

## Nächster Prompt

`RESCUE_USB_REWRITE_AFTER_START_ASSISTANT_ISO_OPERATOR_RUN`

## Nicht ausgeführt (Agent)

dd, USB-Schreiben, MSI-Boot, Windows-Inspect, Backup, Restore, Push.
