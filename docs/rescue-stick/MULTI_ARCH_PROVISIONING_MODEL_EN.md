# Multi-Arch Provisioning Model — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), extended by
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](MULTI_ARCH_PROVISIONING_MODEL_DE.md) · [English](MULTI_ARCH_PROVISIONING_MODEL_EN.md) · [Français](MULTI_ARCH_PROVISIONING_MODEL_FR.md) · [Nederlands](MULTI_ARCH_PROVISIONING_MODEL_NL.md)

## Core statement

**Real operating system installations remain blocked until the next
release gate.** This phase delivers only an image catalogue, compatibility
checks, a verification preview and an installation plan — **no** write
operation.

## Modules

| Module | Purpose |
|---|---|
| `backend/provisioning/os_catalog.py` | Loads/filters/validates `data/provisioning/os_catalog.json`; enforces `download_enabled=false` |
| `backend/provisioning/os_compatibility.py` | Checks architecture/platform/target size against catalogue entry |
| `backend/provisioning/os_image_verifier.py` | SHA256 for local files, verification preview — **no** download |
| `backend/provisioning/os_install_plan.py` | Builds `OsInstallPlan` preview, `write_allowed` always `false` |

## First allowed catalogue categories

**x86_64:** Debian Stable, Ubuntu LTS, Linux Mint Stable.

**ARM/Raspberry Pi:** Raspberry Pi OS, Debian ARM64, Ubuntu Server ARM64.

Further categories are prepared only as `support_status: "future"`.

## Provisioning plan

`write_allowed` is **always `false`** in this phase —
`backend/tests/test_provisioning_os_plan_v1.py` verifies this explicitly.

## Not allowed in this phase

- no `dd` onto real target media
- no `mkfs`, `parted`, `sfdisk`, `sgdisk`, `wipefs`
- no modification of internal EFI partitions
- no automatic OS installation
- no image download (`download_enabled` stays `false`)

## Next milestone

`PI-RS-HW-ACTIVATE-002` covers signed image download and controlled OS write
exclusively onto explicitly approved test media.
