# Boot Capability Check (DE)

## Ziel
Setuphelfer prüft nach Restore oder auf Anfrage rein lesend, ob ein Zielsystem bootfähig wirkt.
Diese Phase führt **keine** Boot-Reparatur aus.

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

## Prüflogik (read-only)
- Zielpfad vorhanden/lesbar
- `/etc/fstab` vorhanden + grob parsebar
- UUID/PARTUUID-Hinweise aus `fstab`
- `/boot`, Kernel, Initramfs
- EFI/GRUB/RPi/Windows-Boot-Hinweise
- Dualboot-Risiko

## Bewertung
- `boot_likely`: Linux-Basis + keine offensichtlichen Windows/Dualboot-Risiken
- `boot_warning`: fehlende Artefakte, unklare `fstab`, Windows/Dualboot-Hinweise
- `boot_failed`: Ziel fehlt/nicht lesbar oder Kernstruktur fehlt
- `boot_unknown`: gemischte/uneindeutige Signale

## Integration
`Rescue Execute` liefert zusätzlich `boot_capability`, startet aber **keine** Reparatur.
Ein `boot_warning` markiert den Restore nicht rückwirkend als fehlgeschlagen.
