# ASUS_BIOS_335_RUNBOOK

## Status im Auftrag 006

**Plan-only / deferred.** Kritischer Pfad ist Live-Capture zuerst.

## Preflight (wenn später freigegeben)

1. `exact_match` Machine Identity
2. Exakte Modellbezeichnung G513QM
3. Aktuelle BIOS-Version (erwartet Baseline 331)
4. Offizielles BIOS-335-Paket + Hash
5. Netzteil / Akku-Gate
6. Secure-Boot/TPM/EFI Pre-State export
7. BitLocker **RO**-Status + Recovery-Risiko-Hinweis
8. Post-Flash-Retestplan (Stick-Boot, NVMe, Win11 instrumentiert)

## Flash

Bevorzugt ASUS EZ-Flash / modelldokumentierter UEFI-Weg. Keine undokumentierten Methoden.

## Nach Flash

BIOS-Version/Datum, SB/TPM, Bootorder, NVMe, GPU/VMD, Linux/Rescue/Windows-Retest inkl. neuer Live-Evidence.
