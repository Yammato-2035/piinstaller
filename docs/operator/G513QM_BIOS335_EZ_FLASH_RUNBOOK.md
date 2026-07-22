# G513QM BIOS 335 EZ Flash Runbook

**Only after** Stage A justifies firmware comparison or explicit operator skip of causality.

## Allowed method

ASUS EZ Flash in UEFI using the official G513QM.335 package from the ASUS model page.

## Forbidden

- flashrom, fwupdmgr, generic Windows flashers without stable Windows
- flashing during a Windows install run
- wrong model package (e.g. G713*)

## Checklist

- Model/board = G513QM
- Installed = 331 → target = 335
- File + checksum documented
- AC connected, battery OK
- Minimal USB devices
- After flash: confirm 335, defaults if required, UEFI/TPM/Secure Boot/NVMe/isolation
