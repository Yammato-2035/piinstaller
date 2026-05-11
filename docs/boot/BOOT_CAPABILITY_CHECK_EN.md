# Boot Capability Check (EN)

## Goal
Setuphelfer performs a read-only boot plausibility check after restore or on-demand.
This phase executes **no** boot repair.

## API
`POST /api/boot/capability`

Request:
```json
{ "target_path": "/mnt/setuphelfer-restore-live/target" }
```

Response:
```json
{
  "code": "BOOT_CAPABILITY_LIKELY|BOOT_CAPABILITY_WARNING|BOOT_CAPABILITY_FAILED|BOOT_CAPABILITY_UNKNOWN",
  "capability": {
    "status": "boot_warning",
    "checks": [],
    "boot_type_hints": [],
    "risks": [],
    "recommendations": [],
    "warnings": [],
    "errors": []
  },
  "warnings": [],
  "errors": []
}
```

## Read-only checks
- target path exists/readable
- `/etc/fstab` exists + basic parseability
- UUID/PARTUUID references in `fstab`
- `/boot`, kernel, initramfs
- EFI/GRUB/RPi/Windows boot hints
- dualboot risk

## Evaluation
- `boot_likely`: Linux baseline + no obvious Windows/dualboot risk
- `boot_warning`: missing artifacts, unclear `fstab`, Windows/dualboot hints
- `boot_failed`: target missing/unreadable or core structure missing
- `boot_unknown`: mixed/unclear signals

## Integration
`Rescue Execute` now includes `boot_capability` and still performs **no** repair.
A `boot_warning` does not retroactively turn a successful restore into a restore failure.
