# RESCUE_ISO_UEFI_VALIDATOR_FAILURE_TRIAGE

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_ISO_UEFI_AND_NETWORKMANAGER_FAILURE_TRIAGE_FIX`

## Preflight

| Feld | Wert |
|------|------|
| HEAD vorher | `ff2106d` |
| Version vorher | `1.7.4.4` |
| ISO SHA256 (vor Fix-Rebuild) | `dc35138768ee659273ac0949a26b468d911a9dac3ca2e0c854b01481609041f8` |
| UEFI Validator | Exit **34** / `RESCUE-UEFI-003` (`isolinux_only_iso`) |

## Root Cause UEFI

1. **`lb build` erzeugt nur ISOLINUX-Hybrid**, obwohl `auto/config` `--bootloaders syslinux,grub-efi` setzt.
2. Build-Log: `lb_binary_grub` / `lb_binary_grub2` / `lb_binary_syslinux` — **kein** erfolgreicher grub-efi-Stage-Output auf der ISO.
3. `grub-efi-amd64-bin` landet nur im **ISO-Pool** (`setuphelfer.list.binary`), nicht als `EFI/BOOT/BOOTX64.EFI` oder `boot/grub/efi.img`.
4. Der dokumentierte Post-Patch (`patch-rescue-iso-uefi-x64.sh`) war **nicht** in `run-controlled-iso-build-with-logging.sh` integriert — ISO `dc351387…` wurde ungepatcht gebaut (früher war Stick `09b9482a…` per Operator-Patch UEFI-grün).

## Workspace-Fix

- `run-controlled-iso-build-with-logging.sh`: nach `LB_EXIT=0` automatisch `validate-rescue-iso-uefi-boot.sh`; bei Fehler `patch-rescue-iso-uefi-x64.sh --in-place`, danach Re-Validate.

## ISO-Rebuild

**Nein** (Operator-sudo erforderlich). Gate `iso_uefi_validated` bleibt **false** bis Rebuild.

## Nicht ausgeführt

USB-dd, MSI-Retest, Windows-Inspect, Deploy, Push.
