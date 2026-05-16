# Core Recovery Test Return

Governance/Runtime-Gate ist stabil (Phase 0 grün). Rückkehr zu echten Recovery-Tests **ohne** Cockpit-Features.

## Status 2026-05-16 (BR-001 Full Root + Verify Deep — Versuch)

| Bereich | Ampel | Ehrlich |
|---------|-------|---------|
| Runtime-Deploy-Gate | grün | Phase 0: `./scripts/check-runtime-deploy-gate.sh` Exit 0; Cockpit-API `runtime_gate.passed`, `deploy_drift` green, `safe_test_mode` UNLOCKED |
| pytest / CI Evidence | grün/gelb | wie zuvor; auf diesem Runner oft kein `pytest`-Modul installiert |
| Release / BR-001 Full Root + Verify Deep | **rot (blockiert)** | Ausführungsrezept: **`BR001_operator_final_execution_handoff.md`**; weiterhin kein fertiges externes Archiv/Verify bis Betreiber **`/media/setuphelfer/<label>`** + Lauf; ältere Evidence: `BR001_full_root_validation_attempt_2026-05-16.json`, `BR001_final_full_root_execution_preflight_2026-05-16.json` |
| APT/Packaging-Pipeline | **rot** | kein produktives Update-Channel |
| Backup/Restore-Modul (Cockpit) | **gelb/rot** | Restore/Rescue unverändert rot |

### Blocker (ehrlich, kein Fake-Grün)

1. **Externes Ziel vs. Dienstbenutzer:** USB ist unter `/media/gabriel/Backup` gemountet (**0700** `gabriel:gabriel`). Der Backend-Dienst läuft als **`User=setuphelfer`** und kann diesen Pfad **nicht** lesen/schreiben → API-`POST /api/backup/create` mit externem Medium scheitert hier ohne Betreiber-Anpassung (ACL/Gruppe/eigenes Mount unter `/mnt/setuphelfer/…`).
2. **Default `backup_dir`:** `/mnt/setuphelfer/backups` liegt auf **/** (internes NVMe) — für diesen STRICT-Lauf **kein** Ersatz für „externes Medium“.
3. **Package-Freeze:** `systemctl stop` der apt-Timer in dieser Session **nicht** ausgeführt (interaktives `sudo`-Passwort nötig). Vor einem echten Lauf wie in der Runbook-Vorgabe mit `pkexec`/Konsole nachholen.
4. **Zielrechte / systemd (2026-05-16):** Architektur und API-Diagnosen **`BACKUP-TARGET-*`** dokumentiert und implementiert; **`ReadWritePaths`** im Repo auf **`/media/setuphelfer`** vereinheitlicht (ohne `/media/gabriel/…`). Betreiber: Verzeichnis anlegen + Dienst neu starten — siehe KB `external-backup-target-architecture.md`.
5. **BR-001 Final Full Root (2026-05-16):** **nicht ausgeführt** — Host ohne angelegtes **`/media/setuphelfer/<label>`**; kein interaktives `sudo` in der Agent-Session; `target-check` auf Planpfad liefert **`STORAGE-PROTECTION-001`** (Ziel nicht als externes Block-FS valide / nicht vorhanden). Evidence: `docs/evidence/runtime-results/handoff/BR001_final_full_root_execution_preflight_2026-05-16.json`.
6. **Operator-Handoff (2026-05-16):** Vollständige Copy/Paste-Sequenz liegt unter **`docs/evidence/runtime-results/handoff/BR001_operator_final_execution_handoff.md`** — BR-001 bleibt fachlich **offen**, bis der Betreiber die Schritte ausführt und Evidence schreibt.

## Phasen (Reihenfolge)

1. **Governance stabil** — erledigt (Runtime-Gate, Evidence konsistent, kein Fake-Grün)
2. **BR-001 Daten** — validiert: `docs/evidence/runtime-results/BR-001-external-validation-2026-05-15.md`
3. **BR-001 Full Root** — **failed** (2 Läufe: USB-Disconnect; Retry USB-stabil, mintupdate-Kollision) — Storage: `docs/knowledge-base/storage/BR-001-external-hdd-usb-stability.md`; **2026-05-16:** erneuter Final-Versuch **blockiert** (Mount-Rechte + Freeze nicht automatisierbar)
4. **Verify Full** — offen (kein fertiges externes Full-Root-Archiv aus diesem Lauf)
5. **Restore Preview** — Sandbox, keine Produktiv-Restore
6. **Rescue Preview** — read-only / geplant
7. **Hardware E2E** — nach Gate + BR-001-Evidence
8. **Boot-/Service-Recovery**
9. **Rescue-Stick-Ausbau** — erst nach 1–8

## Verboten in Vorbereitungsphase

Kein Backup-/Restore-Start aus Cockpit, kein HW-Test, kein apt upgrade, kein automatisches Deploy.

## Verweise

- `docs/evidence/runtime-results/handoff/BR001_operator_final_execution_handoff.md` — **finaler Operator-Handoff** (copy/paste Befehle, kein Backup-Start aus dem Repo heraus)
- `docs/evidence/release-gates/backup_restore_release_gate.json`
- `docs/evidence/backup-restore/BR-001.json`
- `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`
- `docs/dev-dashboard/README.md`
