# STRICT MODE – CI + Backup/Verify Evidence Run

**Ausgeführt:** 2026-05-11T22:00:00Z  
**Scope:** keine Features, kein Refactor, kein Restore, kein Schreiben auf interne Produktionsziele, kein sudo, keine Cloud-/Website-/Affiliate-Arbeit.

## CI-Status

- Artefakt: `docs/evidence/release-gates/ci_evidence.json`
- Abfrage: `gh run list -R Yammato-2035/piinstaller --workflow ci.yml` — letzte Einträge **conclusion: failure** (neuester Lauf 2026-05-10, URL in JSON).
- Lokal: `pytest tests/` **1526 passed / 0 failed** (bereits in `current_failures.json`); Ruff/Bandit im verwendeten venv nicht installiert → keine lokale 1:1-Spiegelung der CI-Schritte außer Pytest.

## BR-001 Status

- **blocked** — `POST /api/backup/create` (`type=full`, `target=local`, Ziel unter `/tmp/setuphelfer-test/...`) → `backup.path_invalid`, **STORAGE-PROTECTION-001** (Schreibzugriff auf Systemplatte nicht erlaubt).
- Kein externes/freigegebenes Mount in dieser Umgebung für den Nachweis genutzt.

## BR-004 Status

- **ok (API)** — `POST /api/backup/verify` `mode=basic` auf Archiv unter `docs/evidence/backup-restore/samples/br-verify-sample.tar.gz` (Allowlist `/home`, Manifest per `embed_manifest_in_tar_gz`).
- Matrix-Ampel **gelb**: BR-001-Kette nicht erfüllt; Archiv ist Referenznachweis, kein Produktions-Full-Backup.

## BR-005 Status

- **ok (API)** — `mode=deep`, gleiches Archiv, `backup.verify_success`.
- Matrix-Ampel **gelb** — wie BR-004.

## Geänderte / neue Dateien

- `docs/evidence/release-gates/ci_evidence.json` (neu)
- `docs/evidence/release-gates/STRICT_CI_BR_GATE_RUN_REPORT_2026-05-11.md` (neu)
- `docs/evidence/backup-restore/samples/br-verify-sample.tar.gz` (neu, kleines Referenzarchiv)
- `docs/evidence/backup-restore/BR-001.json`
- `docs/evidence/backup-restore/BR-004.json`
- `docs/evidence/backup-restore/BR-005.json`
- `docs/evidence/release-gates/backup_restore_release_gate.json`
- `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`
- `docs/roadmap/STATUS_MATRIX.md`
- `docs/evidence/release-gates/runtime_inventory.json`
- `docs/evidence/release-gates/blocker_inventory.json`
- `docs/evidence/release-gates/release_readiness_report.md`
- `docs/evidence/release-gates/release_readiness_gate.json`

## Offene Blocker

- P0: Hardware-E2E Backup→Verify→Restore→Boot (unverändert).
- P1: CI grün + reproduzierbar (`ci_evidence.json`).
- BR-001: externes/freigegebenes Backup-Ziel + ggf. betriebskonform dokumentiertes sudo nur bei Bedarf.

## Nächster empfohlener Test

1. **BR-001** auf **freigegebenem externen Medium** (Mount unter `/media`/`/run/media` mit Block-Device-Klassifikation) oder freigegebenem Schreibpräfix laut Betrieb — danach dieselbe Archivdatei für BR-004/BR-005 erneut verifizieren und Ampel auf Grün heben.  
2. Parallel: **CI-Failure** des neuesten `ci.yml`-Runs analysieren und erneut laufen lassen, URL/Conclusion in `ci_evidence.json` aktualisieren.
