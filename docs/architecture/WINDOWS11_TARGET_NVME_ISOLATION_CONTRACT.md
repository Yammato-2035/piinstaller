# WINDOWS11_TARGET_NVME_ISOLATION_CONTRACT

## Goal

Ensure the Linux NVMe cannot be partitioned, formatted, or used as EFI target during Windows Setup.

## Protection order

1. **Physical remove** (preferred)
2. **UEFI disable** (if G513QM supports it)
3. **WinPE offline** via stable identity (`diskpart offline disk` or equivalent) — last resort

## Binding fields

Windows and Linux targets must differ in:

- `nvme_identity_hash`
- `eui` (when present)
- `pci_path`
- `serial_hash`

Never bind by `/dev/nvme0n1` / Disk 0 / identical size alone.

## Failure

If identity is ambiguous → `blocked_linux_nvme_isolation`.
