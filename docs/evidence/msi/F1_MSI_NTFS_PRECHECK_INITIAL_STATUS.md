# F.1 MSI NTFS Precheck — Initial Status

**Datum:** 2026-06-16  
**HEAD:** bb9df40 → (nach Commit F.1)

## Git / Repo

| Feld | Wert |
|------|------|
| Branch | main |
| Version (Workspace) | 1.9.0.0 → 1.9.1.0 |
| Remote | PUBLIC `Yammato-2035/piinstaller` |
| Dirty Tree | untracked Evidence (alt); F.1 staged separat |

## Gates

| Gate | Ergebnis |
|------|----------|
| check-public-private-boundary.sh | **OK** (Exit 0) |
| check-module-boundaries.sh | review_required (110) |
| check-runtime-deploy-gate.sh | Legacy-Hinweis release profile |
| check-backend-version-gate.sh | Drift workspace 1.9.x vs Runtime 1.8.12.0 |

## Runtime

- CLI read-only Precheck: **erlaubt**
- API Smoke: pending bis Operator-Deploy (kein Deploy in F.1)
- `setuphelfer-backend.service`: active (Referenz)

## Private-only

Keine Treffer im Tree; Gate grün.

## F.1 Modus

`read_only` — `msi_runtime_actions_allowed: false` für Backup/Restore/Write
