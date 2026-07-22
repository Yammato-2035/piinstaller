# Capture Finalizer Contract (hardware_discovery)

## Terminal status

Every run must end with exactly one of:

- `complete`
- `partial`
- `failed`
- `cancelled`

with `terminal=true`. `running` is transitional only.

## Required artifacts (SETUP_LOGS)

- `run-status.json` / `run_status.json`
- `machine-identity.json`, `machine-binding.json`
- `bios-inventory.json`
- `nvme-identity-redacted.json`
- `nvme-smart.json`, `nvme-error-logs.json`
- `kernel-storage-findings.json`, `partition-inventory.json`
- `windows-setup-evidence-inventory.json`, `windows-setup-error-summary.json`
- `manifest.json`, `sha256sums.txt`, `capture-summary.json`
- `COMPLETED.TAG` or `PARTIAL.TAG` (or `FAILED.TAG`)

Marker is written **after** manifest and sha256sums.

## Windows logs

- Found → `complete` / `partial`
- None → `not_found` (not `failed`)
- Hibernated NTFS mount refused → `partial`

## GUI

Text hardware_discovery: `gui_status=not_applicable_for_text_hardware_discovery`.

## Safety

No BIOS flash, no storage writes, no RW NTFS mounts.
