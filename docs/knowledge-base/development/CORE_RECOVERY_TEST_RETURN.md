# Core Recovery Test Return

Governance/Runtime-Gate ist stabil (Phase 0 grün). Rückkehr zu echten Recovery-Tests **ohne** Cockpit-Features.

## Status 2026-05-15

| Bereich | Ampel | Ehrlich |
|---------|-------|---------|
| Runtime-Deploy-Gate | grün | `runtime_gate.passed`, `deploy_drift` green |
| pytest / CI Evidence | grün/gelb | 1624 passed lokal |
| Release / BR-001 | **gelb/rot** | Daten-Backup + Verify **grün**; Full-Root: USB-Fix OK, Retry 76 min ~97 GiB dann **apt-get**-Abbruch — `BR-001-full-root-retry-controlled-2026-05-15.md` |
| APT/Packaging-Pipeline | **rot** | kein produktives Update-Channel |
| Backup/Restore-Modul (Cockpit) | **gelb/rot** | Backup-Teilnachweis; Restore/Rescue rot |

## Phasen (Reihenfolge)

1. **Governance stabil** — erledigt (Runtime-Gate, Evidence konsistent, kein Fake-Grün)
2. **BR-001 Daten** — validiert: `docs/evidence/runtime-results/BR-001-external-validation-2026-05-15.md`
3. **BR-001 Full Root** — **failed** (2 Läufe: USB-Disconnect; Retry USB-stabil, mintupdate-Kollision) — Storage: `docs/knowledge-base/storage/BR-001-external-hdd-usb-stability.md`
4. **Verify Full** — offen (kein fertiges Archiv)
5. **Restore Preview** — Sandbox, keine Produktiv-Restore
6. **Rescue Preview** — read-only / geplant
7. **Hardware E2E** — nach Gate + BR-001-Evidence
8. **Boot-/Service-Recovery**
9. **Rescue-Stick-Ausbau** — erst nach 1–8

## Verboten in Vorbereitungsphase

Kein Backup-/Restore-Start aus Cockpit, kein HW-Test, kein apt upgrade, kein automatisches Deploy.

## Verweise

- `docs/evidence/release-gates/backup_restore_release_gate.json`
- `docs/evidence/backup-restore/BR-001.json`
- `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`
- `docs/dev-dashboard/README.md`
