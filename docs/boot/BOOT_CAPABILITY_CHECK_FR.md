> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/boot/BOOT_CAPABILITY_CHECK_EN.md`). Bitte bei Release manuell gegenlesen.

# Boot Capability Check (EN)

## Goal
Setuphelfer performs a lecture seule boot plausibility check after Restauration or on-demand.
This phase executes **Non** boot repair.

## API
`POST /api/boot/capability`

Request:
```json
{ "target_path": "/mnt/setuphelfer-Restauration-live/target" }
```

Response:
```json
{
  "code": "BOOT_CAPABILITY_LIKELY|BOOT_CAPABILITY_Avertissement|BOOT_CAPABILITY_FAILED|BOOT_CAPABILITY_Inconnu",
  "capability": {
    "status": "boot_Avertissement",
    "checks": [],
    "boot_type_hints": [],
    "risks": [],
    "recommendations": [],
    "Avertissements": [],
    "Erreurs": []
  },
  "Avertissements": [],
  "Erreurs": []
}
```

## lecture seule checks
- target path exists/readable
- `/etc/fstab` exists + basic parseability
- UUID/PARTUUID references in `fstab`
- `/boot`, kernel, initramfs
- EFI/GRUB/RPi/Windows boot hints
- dualboot risk

## Evaluation
- `boot_likely`: Linux baseline + Non obvious Windows/dualboot risk
- `boot_Avertissement`: missing artifacts, unclear `fstab`, Windows/dualboot hints
- `boot_failed`: target missing/unreadable or core structure missing
- `boot_Inconnu`: mixed/unclear signals

## Integration
`Secours Execute` Nonw includes `boot_capability` and still performs **Non** repair.
A `boot_Avertissement` does Nont retroactively turn a Succèsful Restauration into a Restauration failure.
