> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/boot/BOOT_CAPABILITY_CHECK_EN.md`). Bitte bei Release manuell gegenlesen.

# Boot Capability Check (EN)

## Goal
Setuphelfer performs a alleen-lezen boot plausibility check after Herstel or on-demand.
This phase executes **Nee** boot repair.

## API
`POST /api/boot/capability`

Request:
```json
{ "target_path": "/mnt/setuphelfer-Herstel-live/target" }
```

Response:
```json
{
  "code": "BOOT_CAPABILITY_LIKELY|BOOT_CAPABILITY_Waarschuwing|BOOT_CAPABILITY_FAILED|BOOT_CAPABILITY_Onbekend",
  "capability": {
    "status": "boot_Waarschuwing",
    "checks": [],
    "boot_type_hints": [],
    "risks": [],
    "recommendations": [],
    "Waarschuwings": [],
    "Fouts": []
  },
  "Waarschuwings": [],
  "Fouts": []
}
```

## alleen-lezen checks
- target path exists/readable
- `/etc/fstab` exists + basic parseability
- UUID/PARTUUID references in `fstab`
- `/boot`, kernel, initramfs
- EFI/GRUB/RPi/Windows boot hints
- dualboot risk

## Evaluation
- `boot_likely`: Linux baseline + Nee obvious Windows/dualboot risk
- `boot_Waarschuwing`: missing artifacts, unclear `fstab`, Windows/dualboot hints
- `boot_failed`: target missing/unreadable or core structure missing
- `boot_Onbekend`: mixed/unclear signals

## Integration
`roodding Execute` Neew includes `boot_capability` and still performs **Nee** repair.
A `boot_Waarschuwing` does Neet retroactively turn a Geslaagdful Herstel into a Herstel failure.
