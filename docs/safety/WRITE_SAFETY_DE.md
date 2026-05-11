# Write-Safety (DE)

## Zweck

Schützt zukünftige Schreibpfade (Restore, Deploy, Partitionierung) durch eine **reine Auswertung** bestehender Inspect-Daten. **Keine** Schreiboperation, **kein** Override in dieser Phase.

## Module

- `backend/safety/write_guard.py` – `evaluate_write_target(device, inspect_result)`, `build_write_safety_summary(inspect_result)`
- API: `GET /api/safety/targets` – je Disk: `device`, `size`, `classification` (`allowed`|`warning`|`blocked`), `write_allowed`, `reason_code`
- Inspect: optionales Feld `write_safety_summary` (gleiche Zieliste erweitert um Bewertungsfelder)

## Reason Codes

| Code | Bedeutung (kurz) |
|------|------------------|
| `SAFETY_SYSTEM_DISK` | Systemplatte / Root-Mount erkannt |
| `SAFETY_LIVE_SYSTEM` | Live-Medium (squashfs/iso/overlay) |
| `SAFETY_UNKNOWN_DEVICE` | Gerät nicht gefunden oder zu unsicher |
| `SAFETY_WINDOWS_DETECTED` | NTFS-Zwang ohne klares Backup-Muster |
| `SAFETY_DUALBOOT` | NTFS und Linux-FS auf derselben Disk |
| `SAFETY_EMPTY_DISK` | Leer / unpartitioniert (defensiv erlaubt) |
| `SAFETY_BACKUP_TARGET_OK` | Alle Partitionen als `backup_candidate` |

## Grenzen

- Keine Microsoft-Pfadprüfung; NTFS allein ist **kein** Freigabegrund (`SAFETY_WINDOWS_DETECTED` blockiert Schreiben).
- Override (`requires_override`) ist nur dokumentiert; **keine** UI zum Umgehen in Phase 1.

## Nächste Phase

Verknüpfung mit konkreten Restore-/Deploy-Wizards; weiterhin keine blinden Schreibzugriffe ohne Nutzerbestätigung außerhalb dieses Dokuments.
