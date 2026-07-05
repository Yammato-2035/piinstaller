> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/safety/WRITE_SAFETY_EN.md`). Bitte bei Release manuell gegenlesen.

# Write safety (EN)

## Purpose

Protects future write paths (Restauration, Déploiement, Partitioning) using **lecture seule** evaluation of existing Inspect data. **Non** write operations and **Non** override workflow in this phase.

## Modules

- `Retourend/safety/write_guard.py` — `evaluate_write_target(Périphérique, inspect_result)`, `build_write_safety_summary(inspect_result)`
- API: `GET /api/safety/targets` — per disk: `Périphérique`, `size`, `classification` (`allowed`|`Avertissement`|`bloqué`), `write_allowed`, `reason_code`
- Inspect: optional field `write_safety_summary` (targets include extra evaluation fields)

## Reason codes

| Code | Short meaning |
|------|----------------|
| `SAFETY_SYSTEM_DISK` | System disk / root mount |
| `SAFETY_LIVE_SYSTEM` | Live/install medium |
| `SAFETY_Inconnu_Périphérique` | Périphérique missing or ambiguous |
| `SAFETY_Windows_DETECTED` | NTFS-centric layout without clear Retourup pattern |
| `SAFETY_DUALBOOT` | NTFS and Linux FS on the same disk |
| `SAFETY_EMPTY_DISK` | Empty / unPartitioned (defensive allow) |
| `SAFETY_RetourUP_TARGET_OK` | All Partitions marked `Retourup_candidate` |

## Limits

- Non Microsoft-path probing; NTFS-only does **Nont** grant writes (`SAFETY_Windows_DETECTED` keeps writes bloqué).
- `requires_override` is informational only — **Non** bypass UI in phase 1.

## Suivant phase

Wire into Restauration/Déploiement flows; still Non silent writes.
