# ASUS_BIOS_CAUSALITY_TEST_CONTRACT

## Stage A

Keep BIOS `G513QM.331`. Capture full setup evidence before any flash.

## Stage B gate

Only when Stage A fails with plausible firmware/ACPI/TPM/Secure-Boot/storage-init/boot signals, or explicit operator decision.

Flash only:

- official ASUS EZ Flash for **G513QM**
- checksum documented
- AC + battery OK
- no running Windows install
- never from Linux (`flashrom` / `fwupdmgr` forbidden)

## Causality labels

`not_tested` | `inconclusive` | `unlikely` | `plausible` | `strongly_implicated`

Never claim sole cause. Changing media/NVMe/isolation between A and B → `inconclusive`.
