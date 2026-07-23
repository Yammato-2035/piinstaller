# BIOS_CHANGE_CONTRACT

Every change requires: change_id, old/new/rollback, write_method, `bitlocker_mutation=false`, and `bitlocker_recovery_risk` when SB/TPM/EFI trust may change.

One setting per run. Unsupported writes use guided firmware-UI checklist + postcheck capture.

BIOS 335 flash remains a separate firmware run with full preflight — not implied by missing Panther.
