# R.5B — Target Safety Check

**Datum:** 2026-06-13  
**Status:** Vorbereitet — **Write nicht ausgeführt** (Gate blockiert)

## Skripte

| Skript | Rolle |
|--------|-------|
| `scripts/rescue-live/write-fat32-esp-rescue-usb.sh` | Writer (default **dry-run**) |
| `scripts/rescue-live/verify-fat32-esp-rescue-usb.sh` | Read-only Verify |

## Safety-Regeln (Writer + Verify)

| Check | Regel |
|-------|-------|
| Ziel existiert | Blockdevice unter `/dev/` |
| Interne NVMe | **verify** blockiert `nvme*` (Exit 27) |
| `/dev/sda` | **verify** explizit verboten (Exit 27) — Backup-Risiko auf diesem Host |
| Root-Disk | `nvme*n*p*` mit `/` mount → **niemals** |
| Backup-Ziel | `sda1` ext4 Label Backup gemountet → **verboten** |
| Automatische Zielwahl | **verboten** |

## Geplanter Ablauf (Operator, nach Gate)

### 1. Dry-Run

```bash
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_TARGET" \
  --expected-iso-sha256 f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143 \
  --dry-run
```

Erwartung: `write_executed=false`, `safety.blocked=false` für gültiges USB-Ziel.

### 2. Destructive Write (nur Operator-TTY)

```bash
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_TARGET" \
  --expected-iso-sha256 f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143 \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB" \
  --execute-write
```

### 3. Verify

```bash
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target "$USB_TARGET"
```

## Erwartetes Stick-Layout

- GPT, EFI System Partition (FAT32)
- Label `SETUPHELFER` / `SETUPHELFER_RESCUE` (per `fat32_esp_label_spec`)
- `EFI/BOOT/BOOTX64.EFI`, `boot/grub/*`, `live/filesystem.squashfs`
- `setuphelfer-evidence/` vorbereitet

## Bewertung (aktuell)

| Feld | Wert |
|------|------|
| Safety Check ausgeführt | **nein** (kein `USB_TARGET` gesetzt) |
| Write freigegeben | **nein** |
| Interne Datenträger geschrieben | **nein** |
