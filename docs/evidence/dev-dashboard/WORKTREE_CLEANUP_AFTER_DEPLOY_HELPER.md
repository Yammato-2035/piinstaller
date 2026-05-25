# Worktree Cleanup After Deploy Helper

**Datum:** 2026-05-25
**HEAD bei Analyse:** `677c2e5`
**Branch:** `main`
**Runtime-Gate:** `./scripts/check-runtime-deploy-gate.sh` -> Exit `0`
**Dirty-Tree-Eintraege vor Cleanup:** `49`

## Ergebnis

Nach dem erfolgreichen Deploy-/Dashboard-Commit `677c2e5` bleibt ein thematisch gemischter Dirty-Tree zurueck.
Fuer diesen Lauf wurde **kein** weiterer Rescue-/ISO-/Packaging-/Frontend-Code blind mitcommittet.
Ziel dieses Dokuments ist die saubere Trennung in:

- **spaeter bewusst als Themen-Commit moeglich**
- **nur dokumentieren / nicht stagen**
- **review-beduerftig**
- **niemals als Build-Artefakt mitnehmen**

## Build-Artefakt-Schutz

Geprueft wurden die Muster:

- `*.iso`
- `*.img`
- `*.qcow2`
- `filesystem.squashfs`
- `initrd*`
- `vmlinuz*`
- `SHA256SUMS`

Befund:

- aktuelle Suche ergab **keine Treffer**
- im Dirty-Tree taucht aus dem generischen Schutzfilter nur `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot` auf
- dieser Pfad ist **kein Build-Artefakt**, sondern eine versionierte Quell-Datei im Live-Build-Tree
- daraus folgt: **kein Artefakt-STOP**, aber der Pfad bleibt ein separater Rescue-ISO-Review-Kandidat

## Handoff-JSONs

Gezielt geprueft:

- `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json`
- `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json`

Befund:

- beide Dateien enthalten neue Timestamps, neue Hashes und lokal laufzeitabhaengige Bewertungswerte
- die Aenderungen spiegeln vor allem lokale Test-/Runtime-Zustaende wider
- diese Dateien sind daher **nicht** fuer einen Cleanup- oder Doku-Commit dieses Laufs geeignet

Empfehlung:

- **ignore_do_not_stage**
- falls spaeter als echte Evidence benoetigt: nur in einem **separaten Evidence-Commit** mit klarer Begruendung

## Rescue-/ISO-Restbefund

Der wichtigste noch offene Quellpfad ist:

- `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot`

Aktuelle Aenderung:

- Entfernt `lsblk`

Einordnung:

- letzter Commit auf diesem Pfad: `e7e2e07` (`Prepare controlled rescue ISO build tree`)
- parallel dazu gibt es zusammenhaengende Aenderungen in:
  - `scripts/rescue-live/prepare-controlled-live-build-tree.sh`
  - `scripts/rescue-live/validate-controlled-live-build-tree.sh`
  - `build/rescue/live-build/setuphelfer-rescue-live/auto/clean`
  - `build/rescue/live-build/setuphelfer-rescue-live/auto/config`
- `util-linux` bleibt in der Package-Liste enthalten; `lsblk` wirkt daher eher redundant als zwingend fehlend

Empfehlung:

- **nicht jetzt mit Cleanup-Doku vermischen**
- als eigener Kandidat **"Rescue ISO package list cleanup"** bzw. Rescue-Build-Tree-Commit spaeter separat reviewen

## Statusmatrix-Konsistenz

Geprueft wurden:

- `docs/roadmap/STATUS_MATRIX.md`
- `docs/evidence/dev-dashboard/DEPLOY_HELPER_INTEGRATION_RESULT.md`
- `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md`

Befund:

- Deploy Helper steht bereits auf **gruen**
- Backend-Version-Gate steht bereits auf **gruen**
- Rescue-ISO-Build ist bereits als `review_required` / operatorabhaengig eingeordnet
- USB-Write bleibt blockiert

Empfehlung:

- **keine weitere Aenderung an `STATUS_MATRIX.md` in diesem Lauf noetig**

## Dirty-Tree-Inventar

| Datei/Pfad | Status | Kategorie | Empfehlung | Begründung |
|---|---|---|---|---|
| `backend/tests/test_deploy_runner_rescue_stick_readonly_build_emulation_v1.py` | `M` | Backend Tests | `commit_later` | Test-Fix fuer Rescue-Readonly-Emulation; gehoert zu einem separaten Rescue-Test-/Build-Tree-Thema, nicht zu diesem Cleanup-Report. |
| `backend/tests/test_dev_dashboard_rescue_build_status_v1.py` | `M` | Backend Tests | `commit_later` | Kleine Testhaertung fuer Secret-Redaction; thematisch Rescue-/Dashboard-nah, aber nicht Teil des Deploy-Helper-Cleanup-Reports. |
| `build/rescue/live-build/setuphelfer-rescue-live/README_SETUPHELFER_RESCUE_LIVE.md` | `M` | Rescue ISO / Build Tree | `commit_later` | Doku im Live-Build-Tree; nur sinnvoll zusammen mit den uebrigen Rescue-Build-Tree-Aenderungen. |
| `build/rescue/live-build/setuphelfer-rescue-live/auto/clean` | `M` | Rescue ISO / Build Tree | `commit_later` | Rekursives `lb clean` wurde ersetzt; sinnvoll nur im Rescue-Build-Tree-Buendel. |
| `build/rescue/live-build/setuphelfer-rescue-live/auto/config` | `M` | Rescue ISO / Build Tree | `commit_later` | `noauto`-/Security-/Firmware-Flags gehoeren zu einer eigenen Rescue-ISO-Konfigurationsaenderung. |
| `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot` | `M` | Rescue ISO / Build Tree | `needs_review` | Entfernt `lsblk`; zusammen mit Generator-/Validator-Skripten zu bewerten, nicht isoliert in diesem Cleanup-Lauf. |
| `ckb-next` | `m` | ckb-next | `ignore_do_not_stage` | Externer Teilbaum/Submodul-Status, klar ausserhalb des Deploy-/Rescue-Cleanup-Scopes. |
| `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json` | `M` | Lab Acceptance | `needs_review` | Lab-Acceptance-Evidence ist nicht Teil des Deploy-Helper-Abschlusses; ohne separaten Kontext nicht committen. |
| `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md` | `M` | Lab Acceptance | `needs_review` | Wie oben; thematisch getrennt halten. |
| `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md` | `M` | Lab Acceptance | `needs_review` | Wie oben; kein Blind-Commit. |
| `docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md` | `M` | Rescue Evidence / Handoff | `commit_later` | Rescue-Evidence gehoert in einen dedizierten Rescue-ISO-/Evidence-Commit. |
| `docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md` | `M` | Rescue Evidence / Handoff | `commit_later` | Zusammenhaengende Rescue-Toolcheck-Evidence, nicht mit Cleanup-Report mischen. |
| `docs/evidence/rescue/RESCUE_LIVE_PACKAGE_LIST_DECISION.md` | `M` | Rescue Evidence / Handoff | `commit_later` | Gehoert zu Package-List-/Build-Tree-Thema. |
| `docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json` | `M` | Runtime Results | `ignore_do_not_stage` | Laufzeit-/Inventar-Datei ohne direkten Bezug zum Deploy-Helper-Cleanup. |
| `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json` | `M` | Runtime Results | `ignore_do_not_stage` | Testbedingt neu generierte Hashes/Timestamps und lokaler Verboten-Artefakt-Befund. |
| `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json` | `M` | Runtime Results | `ignore_do_not_stage` | Testbedingt neu generierte Gate-Werte; nicht mit Cleanup vermischen. |
| `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md` | `M` | Rescue Evidence / Handoff | `commit_later` | Rescue-Runbook nur zusammen mit Rescue-Build-Tree-/Evidence-Paket committen. |
| `frontend/src/lib/sudoUserMessages.ts` | `M` | Frontend / Dashboard | `needs_review` | Frontend-Messaging ausserhalb des abgeschlossenen Deploy-/Dashboard-Runtime-Scopes. |
| `frontend/src/pages/Documentation.tsx` | `M` | Frontend / Dashboard | `needs_review` | Unabhaengige Frontend-Aenderung; ohne Review nicht mit Cleanup-Report vermischen. |
| `frontend/src/pages/RaspberryPiConfig.tsx` | `M` | Frontend / Dashboard | `needs_review` | Unabhaengige Frontend-Aenderung; aktuell kein belegbarer Zusammenhang zum Deploy-Helper-Cleanup. |
| `packaging/helpers/setuphelfer-backup-starter.py` | `M` | Packaging | `needs_review` | Packaging-/Backup-Helfer ausserhalb des aktuellen Scopes. |
| `packaging/systemd/setuphelfer-backend.dev-workspace.conf.example` | `M` | Packaging | `needs_review` | Unabhaengige Packaging-/systemd-Aenderung; separat behandeln. |
| `packaging/systemd/setuphelfer-backend.service.d/notification-env.conf.example` | `M` | Packaging | `needs_review` | Wie oben; nicht mit Cleanup-Doku committen. |
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | `M` | Rescue ISO / Build Tree | `commit_later` | Generator-Skript fuer den Live-Build-Tree; gehoert zu einer eigenen Rescue-ISO-Vorbereitungsserie. |
| `scripts/rescue-live/validate-controlled-live-build-tree.sh` | `M` | Rescue ISO / Build Tree | `commit_later` | Validator-Skript fuer den Live-Build-Tree; mit Build-Tree-Aenderungen gemeinsam behandeln. |
| `.cursor/rules/# Setuphelfer – Core Rules.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei; nicht mit Projekt- oder Rescue-Commits vermischen. |
| `.cursor/rules/100_DASHBOARD_LAYOUT_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/110_FEATURE_GATEKEEPING.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/120_DOCUMENTATION_TRUTH_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/130_BACKEND_ENFORCEMENT_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/140_RESTORE_SANDBOX_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/150_DRY_RUN_MANDATORY.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/160_SYSTEM_STATE_ENGINE.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/170_API_CONTRACT_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/180_LOGGING_AUDIT_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/190_FRONTEND_SIMPLICITY_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/60_BACKUP_SECURITY_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/70_REAL_TEST_DEFINITION.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/80_ENVIRONMENT_GUARD.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/90_UI_STATE_LOGIC_RULES.md` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/setuphelfer-core.mdc` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/setuphelfer-testing.mdc` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `.cursor/rules/setuphelfer-workflow.mdc` | `??` | Cursor Rules | `ignore_do_not_stage` | Lokale Cursor-Regeldatei. |
| `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_DASHBOARD_IST_ANALYSIS.md` | `??` | Rescue Evidence / Handoff | `commit_later` | Analyse-Dokument fuer Rescue-ISO-Dashboard; nur in einem dedizierten Evidence-Buendel sinnvoll. |
| `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_RUNTIME_GATE_FIX.md` | `??` | Rescue Evidence / Handoff | `commit_later` | Fix-/Analyse-Dokument fuer Rescue-Runtime-Gate; nicht mit Cleanup-Doku vermischen. |
| `docs/evidence/runtime-results/BR-001-full-root-or-profile-2026-05-17.json` | `??` | Runtime Results | `needs_review` | Untracked Runtime-Resultat; ohne Nachweis, ob echte neue Evidence oder Altdatei, nicht committen. |
| `docs/evidence/runtime-results/rescue/` | `??` | Runtime Results | `ignore_do_not_stage` | Enthält lokale Summary-JSONs (`controlled_iso_build_latest_summary.json`, `controlled_usb_write_latest_summary.json`), also laufzeitgenerierte Dateien. |
| `frontend/public/dev-dashboard.snapshot.json` | `??` | Frontend / Dashboard | `ignore_do_not_stage` | Snapshot-/Generatdatei; kein Quellartefakt fuer diesen Cleanup-Lauf. |
| `packaging/systemd/setuphelfer-backup@.service.d/backup-target.conf.example` | `??` | Packaging | `needs_review` | Packaging-Aenderung ausserhalb des aktuellen Rescue-/Deploy-Cleanup-Scope. |

## Entscheidung fuer diesen Lauf

Sinnvoller Commit in diesem Lauf:

- **nur** dieses Cleanup-Dokument

Bewusst **nicht** in diesem Lauf:

- kein Rescue-ISO-Build-Tree-Commit
- kein Evidence-Sammelcommit fuer Rescue-/Lab-/Runtime-JSONs
- kein Packaging-Commit
- kein Frontend-Nebencommit
- kein `.cursor`-/`ckb-next`-Commit

## Nächster Schritt

Empfohlene thematische Folgeschritte vor dem naechsten ISO-Build:

1. **Rescue-Build-Tree separat reviewen**
   - `auto/config`
   - `auto/clean`
   - `setuphelfer.list.chroot`
   - `prepare-controlled-live-build-tree.sh`
   - `validate-controlled-live-build-tree.sh`

2. Danach, wenn gewollt, ein eigener kleiner Commit:
   - z. B. **"rescue: stabilize live-build tree cleanup and config validation"**

3. Runtime-Result-/Handoff-JSONs weiterhin getrennt behandeln:
   - nur committen, wenn sie als echte Evidence benoetigt und fachlich bestaetigt sind

4. `.cursor` und `ckb-next` weiterhin ausserhalb der Rescue-/Deploy-Historie halten
