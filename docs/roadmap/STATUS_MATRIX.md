# Setuphelfer – Statusmatrix (Ampel)

**Stand:** 2026-05-13 — **CI:** Run **25751304968** success. **BR-001:** blocked — produktives Backend nicht auf Workspace-Stand (`sudo`); strategischer Doku-Pfad **`/media/setuphelfer/setuphelfer-back`**; externe Priorität in Doku/FAQ/i18n. **Release** rot.  
**Regel:** Grün nur mit Testnachweis, Doku und Evidence-Datei (siehe `docs/evidence/README.md`).

## Ampeldefinition

| Ampel   | Bedeutung |
|---------|-----------|
| Grün    | umgesetzt, getestet, dokumentiert, reproduzierbar, Evidence vorhanden |
| Gelb    | teilweise umgesetzt oder vorbereitet, noch nicht vollständig validiert |
| Rot     | geplant, offen oder fehlerhaft, keine belastbare Abnahme |
| Schwarz | bewusst geparkt, nicht Teil dieser Arbeitsphase |

## Gesamtüberblick

| Bereich | Ampel | Kurzinfo | Evidence / Anker |
|---------|-------|----------|------------------|
| Phase 0 Arbeitsmodus | Gelb | Struktur & Matrizen angelegt, GitHub Project manuell | `docs/evidence/release-gates/feature_freeze.json` |
| Phase 1 Bestandsaufnahme | Gelb | Testinventar + **Pytest Snapshot** (0× fail, 1526× pass, lokal); CI-/HW-Evidence separat | `test_inventory.json`, `current_failures.json`, `pytest_failures_summary_2026-05-11.txt` |
| Backup | Rot | BR-001 blocked — `/opt`≠Workspace (Deploy: sudo); Doku externe Zielpriorität + strategischer Pfad | `BR-001.json`, `BR-001_backend_deploy_status_2026-05-12.md`, `docs/backup/BACKUP_TARGET_POLICY_DE.md` |
| Verify | Rot | BR-004/BR-005 blocked — nur zulässig gegen BR-001-Archiv (BR-001 nicht passed) | `BR-004.json`, `BR-005.json` |
| Restore | Rot | kontrollierte HW-Abnahmen ausstehend | `docs/evidence/backup-restore/` |
| Hardwaretests | Rot | Matrix vorbereitet | `docs/testing/HARDWARE_TEST_MATRIX.md`, `docs/evidence/hardware/` |
| Rescue Stick | Gelb | viel Deploy-/Rescue-Testcode; echter Read-only-Stick offen | `docs/testing/RESCUE_STICK_TEST_MATRIX.md` |
| Monolith-Audit | Rot | DOMAIN_BOUNDARIES Stub | `docs/architecture/DOMAIN_BOUNDARIES.md` |
| Website-Transparenz | Gelb | Markdown-Basis im Repo | `docs/roadmap/PUBLIC_STATUS_PAGE.md`, `docs/testing/WEBSITE_TRANSPARENCY_TEST_MATRIX.md` |
| Affiliate / Monetarisierung | Gelb | Policies als Markdown | `docs/monetization/` |
| Release Gate UG-Start | Rot | Gates nicht grün | `docs/roadmap/RELEASE_READINESS_CHECKLIST.md` |
| Cloudserver Edition | Schwarz | nach Modularisierung | — |

## Phasen-ToDos (Kurz)

| Phase | Ampel | Nächster Schritt |
|-------|-------|------------------|
| P0 | Gelb | GitHub Project anlegen, Issues aus Matrizen |
| P1 | Gelb | Lokal dokumentiert; **GitHub-CI-Ergebnis** separat vergleichen und verlinken |
| P2 | Rot | BR-Tests auf Hardware ausführen, Evidence |
| P3 | Rot | HW-001ff. ausführen |
| P4 | Rot | Rescue Evidence RS-001ff. |
| P5 | Rot | Monolith-Scan aus Prompt 6 |
| P6–P8 | Rot / Gelb | Website, Affiliate, Release-Gates |

## Blocker-Raster (Prompt 2 – klassifiziert)

Vollständiges Inventar: **`docs/evidence/release-gates/blocker_inventory.json`** · Kurzbericht: **`docs/evidence/release-gates/prompt02_abschlussbericht.md`** · Cursor-Prompt: **`docs/cursor/PROMPT_02_BLOCKER_INVENTORY.md`**

### P0 (blockiert Backup/Restore/Hardwaretest)

| ID | Thema | Nächster Schritt |
|----|-------|------------------|
| P0-HW-E2E | Kein dokumentierter HW-Nachweis Backup→Verify→Restore→Boot | `HARDWARE_TEST_MATRIX.md` + `HW-*.json` |

### P1 (blockiert Rescue/Release-Vertrauen)

| ID | Thema | Nächster Schritt |
|----|-------|------------------|
| P1-PYTEST | Lokale Suite **grün** (0 failures, Snapshot 2026-05-11); **CI-Lauf in Evidence** weiterhin offen | `current_failures.json`, `blocker_inventory.json` → `pytest_local_followup` |
| P1-CI | GitHub CI rot (Run 25687412698); kein grüner Lauf | Fix13-Pytest vs. CI; danach erneuter Lauf, URL/Conclusion in `ci_evidence.json` |
| P1-RESCUE | Rescue-Stick / RS-* Evidence (Unit-Tests phase3 + Bundle lokal grün) | `RESCUE_STICK_TEST_MATRIX.md`, `docs/evidence/rescue-stick/` |

### P2 (Website/Transparenz/Recht)

| ID | Thema | Nächster Schritt |
|----|-------|------------------|
| P2-WEB | Live-Site vs. WT-* offen | Statusseite veröffentlichen, `github_status_link.json` |
| P2-LEGAL | Recht/Affiliate ohne Abnahme | `legal_release_gate.md` |

### P3 (später / niedriger)

| ID | Thema |
|----|-------|
| P3-DEBUG | Support-Bundle / Instrumentation (lokal grün; Priorität niedrig wenn Regression) |
| P3-MONOLITH | DOMAIN_BOUNDARIES-Stubs → Prompt 5 |
| P3-CLOUD | Cloudserver – **schwarz** |

### Legacy-Konflikt-Raster

| ID | Priorität | Thema | Status |
|----|-----------|-------|--------|
| B-LEGACY | P1 | pi-installer / PI_INSTALLER_* / npm-Name | `legacy_inventory.json` |
| B-PORTS | P2 | 8000 / 3001 / 5173 / 8010 (Rescue-Doku) | `runtime_inventory.json` |
| B-MOUNT | P2 | Mount/Permission/HW-Varianten | `storage_permission_inventory.json` |
| B-LEGAL | P2 | Impressum/Datenschutz/Affiliate | siehe P2-LEGAL |

*Pytest-Detail:* `docs/evidence/release-gates/current_failures.json` (enthält Verweis auf `blocker_inventory.json` über gemeinsames Release-Gate-Set).*

## Phasen-Checkliste (IDs aus Arbeitsplan)

### Phase 0 – Arbeitsmodus

| ID | Aufgabe | Status |
|----|---------|--------|
| P0-001 | Feature-Freeze | Erledigt (Evidence: `feature_freeze.json`, Ampel Gelb bis formale Abnahme) |
| P0-002 | Baustellen inventarisiert | Laufend (`STATUS_MATRIX`, Blocker) |
| P0-003 | Ampeldefinition im Repo | Erledigt (oben + `PUBLIC_STATUS_PAGE.md`) |
| P0-004 | Evidence-Struktur | Erledigt (`docs/evidence/README.md` + Unterordner) |
| P0-005 | GitHub Project-Felder | Doku erledigt (`GITHUB_PROJECT_SETUP.md`); **Project in GitHub anlegen** |
| P0-006 | Release-Gate-Regeln | Erledigt (`RELEASE_READINESS_CHECKLIST.md`) |

### Phase 1 – Bestandsaufnahme

| ID | Aufgabe | Status |
|----|---------|--------|
| P1-001 | Tests erfasst | Erledigt (`test_inventory.json`, 190 Dateien) |
| P1-002 | Testfehler gesammelt | Erledigt (`current_failures.json`, 0 offene Failures im Snapshot 2026-05-11 Nachlauf) |
| P1-003 | Legacy pi-installer/setuphelfer | Teilweise (`legacy_inventory.json`) |
| P1-004 | Services/Ports/Pfade | Teilweise (`runtime_inventory.json`) |
| P1-005 | Mount/Permission | Teilweise (`storage_permission_inventory.json`) |
| P1-006 | Build/Version | Teilweise (`version_inventory.json`) |
| P1-007 | Blocker P0–P3 | Erledigt (`blocker_inventory.json` + Blocker-Raster oben) |

### Phase 2–8 (Kurz)

| Phase | Ampel | Evidence-Anker |
|-------|-------|----------------|
| P2 Backup/Restore | Rot | `docs/evidence/backup-restore/BR-*.json` |
| P3 Hardware | Rot | `docs/evidence/hardware/HW-*.json` |
| P4 Rescue | Rot/Gelb | `docs/evidence/rescue-stick/` |
| P5 Monolith | Rot | `DOMAIN_BOUNDARIES.md`, `dangerous_couplings.json` |
| P6 Website | Gelb | `WT-*.json`, `PUBLIC_STATUS_PAGE.md` |
| P7 Affiliate | Gelb | `AT-*.json`, `docs/monetization/` |
| P8 Release | Rot | `release_readiness_gate.json` |
