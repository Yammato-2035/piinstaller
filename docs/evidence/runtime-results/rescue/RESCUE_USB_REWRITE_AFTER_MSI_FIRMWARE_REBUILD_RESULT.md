# RESCUE_USB_REWRITE_AFTER_MSI_FIRMWARE_REBUILD_RESULT

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_USB_REWRITE_READBACK_AND_GATE_COMPLETION` (nach Operator-dd)  
**HEAD:** `5c6d5fe` · **Version:** `1.7.4.5`

## Ergebnis

**USB-Write vom Operator bestätigt; Read-only-Verifikation teilweise grün.**

| Prüfung | Ergebnis |
|---------|----------|
| Preflight `/dev/sdb` | Ultra Line, 59G, USB, Serial `24111412110212` ✓ |
| `/dev/sdb1` Größe | **592M** (vorher 533M — neues ISO) ✓ |
| Operator-`dd` (Terminal) | **620756992 Bytes** kopiert (= ISO-Größe) ✓ |
| Block-Readback SHA256 | **Nicht ausgeführt** (Agent: `sudo` Passwort erforderlich; `/dev/sdb` nur root/disk) |
| Boot-Artefakte ro-Mount | **OK** — alle drei Pfade `present` |
| Boot-Artefakt `cmp` ISO↔Stick | **byte-identisch** (`BOOTX64.EFI`, `efi.img`, `isolinux.bin`) |

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 620756992 bytes (592 MiB) |
| SHA256 | `9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a` |

## Zielgerät

| Feld | Wert |
|------|------|
| Device | `/dev/sdb` |
| Modell | Ultra Line |
| Serial | `24111412110212` |
| Transport | usb |
| Partition | `/dev/sdb1` 592M iso9660 `SETUPHELFER_RESCUE` |
| Nicht verwendet | `/dev/sda` (HGST Backup), `/dev/nvme*` |

## Operator-dd (Terminal-Ingest)

```text
148+0 Datensätze ein
148+0 Datensätze aus
620756992 Bytes (621 MB, 592 MiB) kopiert
lsblk: sdb1 592M (nach dd; vorher 533M)
```

## Readback SHA256

```text
Agent-Versuch: sudo python3 block-read auf /dev/sdb → Passwort erforderlich
Erwartet: 9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a
Tatsächlich gemessen: nicht ausgeführt
```

**Sekundäre Verifikation (ohne Block-Readback):**

- `dd`-Bytecount Operator = ISO-Größe (620756992)
- Boot-Dateien auf Stick byte-identisch zur ISO (xorriso-Extract vs. ro-Mount)

## Bootartefakte (ro-Mount 2026-06-07)

```text
BOOTX64.EFI=present  (cmp ISO=identical)
efi.img=present      (cmp ISO=identical)
isolinux.bin=present (cmp ISO=identical)
```

## Gate (ehrlich — kein Fake-Green für Block-Readback)

```text
iso_uefi_validated: true
usb_stick_written: yes
usb_write_sha256_verified: false
usb_block_readback_sha256: null
usb_mount_boot_artifacts_verified: true
usb_write_verification_method: operator_dd_exact_byte_count_and_boot_artifact_cmp
target_laptop_booted_from_stick: false
windows_inspect_executable: false
```

## Resolved Blocker

- `RESCUE_USB_REWRITE_REQUIRED_AFTER_NEW_ISO`
- `RESCUE_STICK_NOT_WRITTEN`
- `RESCUE_USB_REWRITE_DD_BLOCKED_SUDO`

## Aktive Blocker

- `RESCUE_USB_BLOCK_READBACK_SHA256_PENDING` (optional Operator-One-Liner mit sudo)
- `RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET`
- `RESCUE_TARGET_NETWORK_TELEMETRY_NOT_VALIDATED`
- `WINDOWS_INSPECT_BLOCKED_UNTIL_LIVE_NETWORK_VALIDATED`

## Optional: Block-Readback abschließen

```bash
cd /home/volker/piinstaller
ISO_SIZE=620756992
sudo python3 - <<'PY'
import hashlib
from pathlib import Path
size = 620756992
h = hashlib.sha256()
remaining = size
with Path("/dev/sdb").open("rb", buffering=0) as f:
    while remaining > 0:
        chunk = f.read(min(4 * 1024 * 1024, remaining))
        if not chunk: break
        h.update(chunk); remaining -= len(chunk)
print(h.hexdigest())
PY
# Erwartet: 9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a
```

## Next Prompt

**`RESCUE_USB_MSI_UEFI_BOOT_NETWORK_TELEMETRY_OPERATOR_RUN`**

(Boot-Artefakte und Write-Bytecount belegt; MSI-UEFI-Boot als nächster Validierungsschritt.)

Bei Readback-Abweichung: **`RESCUE_USB_REWRITE_READBACK_HASH_MISMATCH_TRIAGE`**

## Nicht ausgeführt

Erneutes dd, MSI-Retest (dieser Lauf), Windows-Inspect, Backup, Restore, Deploy, Push.
