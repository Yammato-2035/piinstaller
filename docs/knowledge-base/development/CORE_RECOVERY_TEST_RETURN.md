# Core Recovery Test Return

Governance/Runtime-Gate ist stabil (Phase 0 grün). Rückkehr zu echten Recovery-Tests **ohne** Cockpit-Features.

## Status 2026-05-15

| Bereich | Ampel | Ehrlich |
|---------|-------|---------|
| Runtime-Deploy-Gate | grün | `runtime_gate.passed`, `deploy_drift` green |
| pytest / CI Evidence | grün/gelb | 1624 passed lokal |
| Release / BR-001 | **gelb** | externes **Daten**-Backup + Verify auf `setuphelfer-back1` (2026-05-15); **Full** (`/`) noch offen |
| APT/Packaging-Pipeline | **rot** | kein produktives Update-Channel |
| Backup/Restore-Modul (Cockpit) | **gelb/rot** | Backup-Teilnachweis; Restore/Rescue rot |

## Phasen (Reihenfolge)

1. **Governance stabil** — erledigt (Runtime-Gate, Evidence konsistent, kein Fake-Grün)
2. **BR-001** — **teilvalidiert:** Daten-Backup + Verify auf `/media/gabriel/setuphelfer-back1` — siehe `docs/evidence/runtime-results/BR-001-external-validation-2026-05-15.md`
3. **Verify** — für Lauf 2026-05-15 erledigt (deep, API)
4. **Restore Preview** — Sandbox, keine Produktiv-Restore
5. **Rescue Preview** — read-only / geplant
6. **Hardware E2E** — nach Gate + BR-001-Evidence
7. **Boot-/Service-Recovery**
8. **Rescue-Stick-Ausbau** — erst nach 1–7

## Verboten in Vorbereitungsphase

Kein Backup-/Restore-Start aus Cockpit, kein HW-Test, kein apt upgrade, kein automatisches Deploy.

## Verweise

- `docs/evidence/release-gates/backup_restore_release_gate.json`
- `docs/evidence/backup-restore/BR-001.json`
- `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`
- `docs/dev-dashboard/README.md`
