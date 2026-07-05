> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/safety/WRITE_SAFETY_EN.md`). Bitte bei Release manuell gegenlesen.

# Write safety (EN)

## Purpose

Protects future write paths (Herstel, Deploy, Partitieing) using **alleen-lezen** evaluation of existing Inspect data. **Nee** write operations and **Nee** override workflow in this phase.

## Modules

- `Terugend/safety/write_guard.py` — `evaluate_write_target(Apparaat, inspect_result)`, `build_write_safety_summary(inspect_result)`
- API: `GET /api/safety/targets` — per disk: `Apparaat`, `size`, `classification` (`allowed`|`Waarschuwing`|`geblokkeerd`), `write_allowed`, `reason_code`
- Inspect: optional field `write_safety_summary` (targets include extra evaluation fields)

## Reason codes

| Code | Short meaning |
|------|----------------|
| `SAFETY_SYSTEM_DISK` | System disk / root mount |
| `SAFETY_LIVE_SYSTEM` | Live/install medium |
| `SAFETY_Onbekend_Apparaat` | Apparaat missing or ambiguous |
| `SAFETY_Windows_DETECTED` | NTFS-centric layout without clear Terugup pattern |
| `SAFETY_DUALBOOT` | NTFS and Linux FS on the same disk |
| `SAFETY_EMPTY_DISK` | Empty / unPartitieed (defensive allow) |
| `SAFETY_TerugUP_TARGET_OK` | All Partities marked `Terugup_candidate` |

## Limits

- Nee Microsoft-path probing; NTFS-only does **Neet** grant writes (`SAFETY_Windows_DETECTED` keeps writes geblokkeerd).
- `requires_override` is informational only — **Nee** bypass UI in phase 1.

## Volgende phase

Wire into Herstel/Deploy flows; still Nee silent writes.
