# OPERATOR CONFIRMATION 1 — Carrier Payload Update 1.10.6.0

**USB_WRITE_ALLOWED = false** until Confirmation 1 + identity re-read + Confirmation 2.

## TARGET (live read-only)

| Field | Value |
|-------|-------|
| Device | `/dev/sda` |
| Vendor / Model | Intenso Ultra Line |
| Capacity | 63333990400 bytes (~58.98 GiB) |
| Serial | `24111412110212` |
| Fingerprint | `ce2e34b7f5ea4e41` |
| Transport | usb, removable |
| Labels | `SETUPHELFER` + `SETUP_LOGS` |
| Mounts | `/media/volker/SETUPHELFER1`, `/media/volker/SETUP_LOGS2` |

## CURRENT → NEW

| | Current | New |
|--|---------|-----|
| Payload | **1.10.5.0** | **1.10.6.0** |
| SquashFS SHA256 | `c57c6fb8…bd5bca51` | `4521968ef8df2e3d35bc44210e3345a0056cfe595a31472720398d95370b57ec` |
| Default GRUB | `ASUS-TUI-BASELINE` | `ASUS-TUI-BASELINE-HIGHINFO` |

## Planned changes (official updater)

- SquashFS (`live/filesystem.squashfs`)
- GRUB configs (HIGHINFO default)
- VERSION / Manifest under `setuphelfer/rescue/`

## Not changed

- Internal NVMe
- Windows
- Partition table / format
- `SETUP_LOGS` content (preserved by update path)

## Required reply for Confirmation 1

Please send **all** of the following (or equivalent explicit approval naming device + versions):

```text
/dev/sda
Intenso Ultra Line
Fingerprint ce2e34b7f5ea4e41
BESTÄTIGUNG 1: Carrier 1.10.5.0 → 1.10.6.0 korrekt
```

After Confirmation 1: identity re-read → Confirmation 2 phrase required before any write.
