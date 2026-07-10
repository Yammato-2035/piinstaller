# PI-RS-WT-004 — Working-Tree Cleanup + Full Gate

Stand: 2026-07-10  
Repo: `/home/volker/piinstaller` @ `749d21b` (vor WT-004-Doku-Commit)

## Warum Cleanup nötig war

Nach PI-RS-TEL-003 war der Working Tree mit ca. **989 Status-Zeilen** / **3181 untracked Dateien** belastet:

- Laufzeit-Evidence unter `docs/evidence/rescue/` und `docs/evidence/runtime-results/`
- **298 nicht-Evidence-Dateien** (WIP-Backend/Frontend/Scripts/Docs aus parallelen Rescue-Sprints)
- Modifizierte tracked Dateien: `ckb-next` (Submodule-Drift), PI-RS-TEL-001-Evidence-Timestamp

Vor einer Build-/Payload-Entscheidung (PI-RS-BUILD-001) war ein reproduzierbarer, sauberer Gate-Stand erforderlich.

## Backup

Pfad: siehe `docs/evidence/pi_rs_wt_004_working_tree_cleanup_full_gate/backup-path.txt`

Inhalt:

- `git-status-short.txt`, `git-status-porcelain-v2.txt`
- `tracked-working-tree.diff`
- `untracked-files.txt` (3181 Einträge)
- `untracked-files.tar.gz` / `wip-feature-and-evidence-artifacts.tar.gz` (~27 MB)
- `manual/ckb-next-snapshot/` (Submodule-Sicherung)
- `remove-failures.txt` (131 root-owned Dateien, nicht löschbar ohne sudo)

## Was revertiert wurde

| Pfad | Bewertung | Aktion |
|------|-----------|--------|
| `docs/evidence/pi_rs_tel_001_.../rescue_lab_payload_synthetic_example.redacted.json` | Reiner `created_at`-Timestamp | `git checkout --` |
| `ckb-next` | Fremdes Submodule, lokale Issue-Template-Änderungen | Snapshot + `git -C ckb-next checkout -- .` |

## Was gelöscht / ignoriert wurde

| Kategorie | Anzahl | Aktion |
|-----------|--------|--------|
| Laufzeit-Evidence `docs/evidence/rescue/` | 2139 | Nach Backup entfernt |
| Laufzeit-Evidence `docs/evidence/runtime-results/` (ohne root-owned) | ~600 | Nach Backup entfernt |
| Dev-Dashboard-Evidence, MSI/Security-Snippets, etc. | ~50 | Nach Backup entfernt |
| WIP Backend/Frontend/Scripts (data_rescue, RS003, …) | 298 | Nach Backup entfernt (im Tar archiviert) |
| Root-owned `fat32_esp_*` / `qemu_rescue_developer_autopilot_*` Remnants | 18 Verzeichnisse | **Nicht löschbar** (sudo blockiert); per `.gitignore` ausgeblendet |

**Wichtig:** WIP-Rescue-Arbeiten sind im Backup-Tar erhalten, nicht im Repo.

## Version 1.9.19.4

Bestätigt in: `VERSION`, `config/version.json`, `package.json`, `frontend/package.json`, `frontend/src-tauri/resources/setuphelfer-version.json`  
Kein `1.9.19.3` in aktiven Versionsträgern.

## Full `run-tests.sh` Ergebnis

Nach Cleanup + Gate-Fix (`cd "$ROOT"` nach Frontend-Tests; Harness ohne `PYTHONPATH`-Leak):

- DCC-VIS-001 Frontend (vitest): **18 passed**
- PI-RS-TEL-001 pytest: **23 passed**
- PI-RS-TEL-002 pytest: **34 passed**
- PI-RS-TEL-003 pytest: **19 passed**
- Safety Gates PI-RS-TEL-001/002: **ok**
- `check_version_consistency.py`: **ok**

Evidence: `docs/evidence/pi_rs_wt_004_working_tree_cleanup_full_gate/full-run-tests-final.txt`

## Safety Gates

- `check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh`: ok
- `check-pi-rs-tel-002-network-gated-telemetry-safety.sh`: ok
- `check-no-secrets.sh` / `check-no-dangerous-commands.sh`: nicht im Repo vorhanden

## Build-Freigabe

**Ja** — Working Tree ist für PI-RS-WT-004 sauber (nur WT-004-Doku/Evidence + `.gitignore`-Wartung), Version bestätigt, vollständiger `run-tests.sh` grün.

Nächster Schritt: **PI-RS-BUILD-001** (Payload-/Build-Entscheidung für MSI-Retest).

## Nicht geändert

- Kein ISO/SquashFS/Payload-Binary
- Kein Feature-Sprint-Code aus dem WIP-Backup committet
- CSE, Diagnostics, Telemetry Server unverändert
