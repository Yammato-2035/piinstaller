# Rescue ISO Executor Dashboard — Integration Result

**Datum:** 2026-05-25
**Git HEAD:** `653d41a` (aktueller Workspace fuer den ersten Runtime-Lauf)
**Status:** `yellow`

## Neue Dashboard-Routen

- `GET /api/dev-dashboard/rescue-iso/status`
- `POST /api/dev-dashboard/rescue-iso/step`
- `GET /api/dev-dashboard/rescue-iso/step/{action_id}`
- `POST /api/dev-dashboard/rescue-iso/operator-commands/sudo-clean`
- `POST /api/dev-dashboard/rescue-iso/operator-commands/build`

## Neuer Executor

- `backend/core/rescue_iso_build_state.py`
  - read-only Aggregation
  - Stale-State-Erkennung
  - Log-Redaction
  - Artefakt-Zusammenfassung
  - naechste Operator-Aktion
- `backend/core/rescue_iso_build_executor.py`
  - erlaubte Steps mit `action_id`
  - Step-Logs unter `build/rescue/logs/controlled-iso-build/actions/`
  - Summary-Update nach jedem Step
- `backend/core/rescue_iso_operator_commands.py`
  - sichere, rein ausgebende Operator-Kommandos

## FastAPI-/Testinterpreter-Befund

- `/usr/bin/python3` (`Python 3.12.3`) hat **kein** `fastapi`
- `backend/venv/bin/python3` (`Python 3.12.3`) hat `fastapi ok`
- Verwendeter Testinterpreter fuer alle Backend-Checks:
  - `backend/venv/bin/python3`

## Artefakt-Cleanup-Befund

Vorherige verbotene Artefakte im Build-Tree:

- `build/rescue/live-build/setuphelfer-rescue-live/chroot/boot/initrd.img-6.1.0-48-amd64`
- `build/rescue/live-build/setuphelfer-rescue-live/chroot/boot/vmlinuz-6.1.0-48-amd64`
- `build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.squashfs`

Befund:

- diese Dateien waren **nicht versioniert**
- der Arbeitsbaum ist jetzt fuer die verbotenen Artefakte **sauber**

Cleanup-Ergebnis:

- aktuelle Suche nach `filesystem.squashfs`, `initrd*`, `vmlinuz*`, `*.iso`, `*.img`, `*.qcow2` unter `build/rescue/live-build/setuphelfer-rescue-live` ergibt **keine Treffer**
- zusaetzlicher Workspace-Fix:
  - `auto/clean` verwendet jetzt **kein** rekursives `lb clean` mehr
  - Operator-Sudo-Clean-Kommandos verwenden jetzt nur noch den direkten Stage-Directory-Clean
- korrektes Operator-Kommando bleibt:
  - `cd /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`
  - `sudo rm -rf .build chroot cache binary local`
- der Regressionstest fuer den **clean**-Pfad ist zusaetzlich auf einen sauberen Testzustand isoliert, damit kuenftige Host-Reste nicht erneut falsche Rot-Faelle erzeugen

## Logging- und Summary-Pfade

- `build/rescue/logs/controlled-iso-build/latest.log`
- `build/rescue/logs/controlled-iso-build/actions/<action_id>.log`
- `build/rescue/logs/controlled-iso-build/actions/<action_id>.json`
- `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`

## Neue Testläufe

### Compile

- `backend/venv/bin/python3 -m py_compile ...` → **grün**

### Neue Rescue-ISO-Tests

- `PYTHONPATH=backend backend/venv/bin/python3 -m unittest backend.tests.test_rescue_iso_build_dashboard_state_v1 backend.tests.test_rescue_iso_build_executor_v1 -v` → **grün**

### Regressionen

- `PYTHONPATH=backend backend/venv/bin/python3 -m unittest backend.tests.test_deploy_runner_rescue_stick_readonly_build_emulation_v1 backend.tests.test_partitions_storage_facade_v1 backend.tests.test_partitions_hardstop_preview_v2 backend.tests.test_partitions_manifest_layout_preview_v2 backend.tests.test_partitions_restore_handoff_preview_v2 -v` → **grün**

## Frontend-Build

- `npm --prefix frontend run build` → **grün**
- Google-Fonts-CDN-Scan in `frontend/dist`, `frontend/index.html`, `frontend/src` → **keine Treffer**

## Frontend-Panel

- Titel: **Rettungsstick ISO-Build**
- Sichtbar in bestehendem `RescueBuildPanel`
- Zeigt:
  - Gesamtstatus
  - Toolcheck
  - Stale Build-State
  - Temp-Runtime-Bundle
  - Live-Build-Baum
  - `auto/config noauto`
  - ISO-Build / ISO-Artefakt
  - letzte Logzeilen
  - naechste Operator-Aktion
  - kopierbare Operator-Kommandos

## Produktive Runtime-Smokes

Nach kontrolliertem Helper-Deploy auf `/opt/setuphelfer` erfolgreich verifiziert:

- `GET /api/dev-dashboard/rescue-iso/status`:
  - `status = green`
  - `stale_state.needs_sudo_clean = false`
  - `iso_build.status = review_required`
  - `next_operator_action.type = operator_sudo_required`
- `POST /api/dev-dashboard/rescue-iso/step` mit `detect_stale_state`:
  - `code = DEV_DASHBOARD_RESCUE_ISO_STEP_OK`
  - `status = ok`
- `POST /api/dev-dashboard/rescue-iso/operator-commands/sudo-clean`:
  - liefert nur den sicheren Workspace-Clean-Pfad:
    - `cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"`
    - `sudo rm -rf .build chroot cache binary local`
- `POST /api/dev-dashboard/rescue-iso/step` mit `usb_write`:
  - `code = DEV_DASHBOARD_RESCUE_ISO_FORBIDDEN_STEP`
  - `status = forbidden`
- Cockpit-UI `http://127.0.0.1:3001/?window=cockpit`:
  - `rescue-build-panel` sichtbar
  - `rescue-build-usb-blocked` sichtbar
  - keine Buttons fuer `dd`, `mkfs`, `parted` oder USB-Write

## Erster Runtime-Lauf ueber den Executor

Am 2026-05-25 wurde der erste kontrollierte Rescue-ISO-Lauf erneut ueber den produktiven Dashboard-/Executor-Pfad gestartet.

### Vor dem Build

- `./scripts/check-runtime-deploy-gate.sh` im Workspace: **Exit 0**
- `GET /api/dev-dashboard/rescue-iso/status`:
  - `status = green`
  - `build_tree.validator_status = ok`
  - `temp_runtime_bundle.status = ok`
  - `iso_build.status = review_required`
  - `stale_state.needs_sudo_clean = false`
  - `next_operator_action.type = operator_sudo_required`
  - `usb_write.allowed = false`

### Executor-Schritte

- `detect_stale_state`:
  - `code = DEV_DASHBOARD_RESCUE_ISO_STEP_OK`
  - `status = ok`
  - `needs_sudo_clean = false`
- `prebuild_check`:
  - `code = DEV_DASHBOARD_RESCUE_ISO_STEP_OK`
  - `status = ok`
  - `details.status = green`
  - vorgeschlagene Operator-Kommandos waren in diesem fruehen Lauf noch falsch auf den Runtime-Pfad ausgerichtet:
    - `cd "/opt/setuphelfer/build/rescue/live-build/setuphelfer-rescue-live"`
    - `./auto/config`
    - `sudo lb build noauto`
- `prepare_bundle`:
  - `code = DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED`
  - `status = blocked`
  - Ursache: `create-temp-runtime-bundle.sh` scheitert im produktiven `/opt`-Pfad mit `rsync`-Permission-Fehlern
- `validate_bundle`:
  - `status = blocked`
  - Ursache: `MISSING: MANIFEST.json`
- `prepare_tree`:
  - `status = blocked`
  - Ursache: `bundle MANIFEST.json missing`
- `validate_tree`:
  - `status = ok`
  - letzter Build-Tree ist weiter formal gueltig, referenziert aber `build-tree-manifest source_head = 27d790a`

### Ergebnis

- **Kein** `sudo lb build noauto` ausgefuehrt, weil PHASE 4 bereits blockiert hat
- Dashboard-Status danach:
  - `status = yellow`
  - `temp_runtime_bundle.status = review_required`
  - `iso_build.status = not_started`
  - `next_operator_action.type = fix_required`
  - `usb_write.allowed = false`
- Services bleiben aktiv:
  - `setuphelfer-backend.service = active`
  - `setuphelfer.service = active`
- Summary/Logs bleiben dashboard-lesbar:
  - `build/rescue/logs/controlled-iso-build/latest.log`
  - `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`

### Bewertung

Die Dashboard-/Executor-Integration ist produktiv vorhanden und fuehrt den Operator korrekt bis zum Build-Befehl. Der erste echte Runtime-Lauf ist jedoch **nicht build-ready**, weil das produktive `/opt`-Temp-Bundle vor dem Build nicht reproduzierbar neu erstellt werden konnte. Ein ISO-Erfolg darf deshalb nicht gruen gemeldet werden.

## Explizit nicht hinzugefuegt

- keine USB-Schreibfunktion
- kein `dd`
- kein `mkfs`
- kein `parted write`
- kein Restore
- kein Backup
- kein Verify Deep
- keine Safety-Gates abgeschwaecht

## Aktuell erkannte Fehlerlage

- `chroot_package-lists.install` kann stale sein
- `skipping chroot_package-lists.install, already done` ist ein harter Review-Hinweis
- `tar failed` bei `adduser` bleibt als letzter Fehler / Stale-Indikator sichtbar
- `./scripts/check-runtime-deploy-gate.sh` ist fuer die produktive Runtime inzwischen **gruen (Exit 0)**; der ISO-Build selbst bleibt trotzdem `review_required`
- im ersten Runtime-Lauf blockierten `prepare_bundle` und `prepare_tree` im produktiven `/opt`-Pfad
- `validate_tree` referenziert dort weiter `source_head = 27d790a`, also nicht den aktuellen Workspace-Stand `653d41a`

## Deploy-Befund

- kontrollierter Deploy ueber `setuphelfer-deploy-helper.service` erfolgreich
- Helper-State:
  - `status = success`
  - `deploy_exit_code = 0`
  - `runtime_gate_exit_after = 0`
- produktiver Runtime-Gate-Lauf danach:
  - `./scripts/check-runtime-deploy-gate.sh` → Exit `0`

## Naechster Operator-Schritt

1. produktive `/opt`-Runtime zuerst auf den aktuellen Rescue-Executor-/Bundle-Stand bringen
2. danach den Dashboard-Lauf erneut bei `detect_stale_state` / `prebuild_check` starten
3. erst wenn `prepare_bundle`, `validate_bundle`, `prepare_tree` und `validate_tree` alle gruen sind, den Operator-Build erneut freigeben
4. USB-Schreiben bleibt weiterhin blockiert

## Workspace-Path-Fix Final (2026-05-25)

Nach dem finalen Workspace-Path-Fix und dem erneuten Runtime-Smoke auf `f2b13f5` ist der produktive Executor jetzt im Zielzustand:

- `GET /api/dev-dashboard/rescue-iso/status`:
  - `status = green`
  - `workspace_path = /home/volker/piinstaller`
  - `runtime_path = /opt/setuphelfer`
  - `build_tree_path = /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`
  - `temp_runtime_bundle_path = /home/volker/piinstaller/build/rescue/temp-runtime/setuphelfer-rescue-runtime`
  - `build_tree.source_head = f2b13f5`
  - `temp_runtime_bundle.source_head = f2b13f5`
  - `stale_state.needs_sudo_clean = false`
  - `usb_write.allowed = false`
- `POST /api/dev-dashboard/rescue-iso/step`:
  - `prepare_bundle` → `ok`
  - `validate_bundle` → `ok`
  - `prepare_tree` → `ok`
  - `validate_tree` → `ok`
- `POST /api/dev-dashboard/rescue-iso/step` mit `build_iso_operator_required`:
  - `status = operator_required`
  - Kommandos:
    - `cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"`
    - `./auto/config`
    - `sudo lb build noauto`

Damit ist die Dashboard-/Executor-Integration fuer den Workspace-Path-Fix produktiv verifiziert. Der echte ISO-Build bleibt weiterhin ein separater Operator-Schritt ausserhalb dieses Strict-Mode-Laufs.

## Echter ISO-Build ueber den Dashboard-Pfad (2026-05-25)

Nach `887ace6` wurde der erste echte Operator-Build entlang des Dashboard-Pfads gestartet.

### Vor dem Build

- `./scripts/check-runtime-deploy-gate.sh` → **Exit 0**
- `GET /api/dev-dashboard/rescue-iso/status`:
  - `status = green`
  - `workspace_path = /home/volker/piinstaller`
  - `runtime_path = /opt/setuphelfer`
  - `build_tree_path = /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`
  - `usb_write.allowed = false`
- `detect_stale_state` → **ok**
- `prebuild_check` → **ok** / `green`
- `prepare_bundle`, `validate_bundle`, `prepare_tree`, `validate_tree` → **ok**

### Operator-Befehl

```bash
cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./auto/config
sudo lb build noauto
```

### Ergebnis

- `LB_EXIT = 100`
- **keine ISO** erzeugt
- Dashboard danach:
  - `status = red`
  - `next_operator_action.type = sudo_clean_required`
  - `usb_write.allowed = false`
- verbliebene Build-Artefakte:
  - `binary/live/filesystem.squashfs`
  - `binary/live/initrd.img`

### Letzter Fehler aus `latest.log`

```text
dpkg: warning: 'start-stop-daemon' not found in PATH or not executable
dpkg: error: 1 expected program not found in PATH or not executable
E: Sub-process /usr/bin/dpkg returned an error code (2)
LB_EXIT=100
```

### Bewertung

Die Dashboard-/Executor-Integration bleibt fuer den Pfad und die kontrollierten Prepare-/Validate-Schritte **gruen verifiziert**. Der erste echte ISO-Build selbst ist jedoch **fehlgeschlagen** und bleibt deshalb `failed/review_required`. USB-Schreiben bleibt weiterhin blockiert.

## Finaler Green-Up Runtime-Stand (2026-05-25)

Nach dem letzten Helper-Deploy `deploy-20260525T193756Z-954998` wurde die produktive Runtime erneut gegen `/opt/setuphelfer` geprueft.

### Runtime- und Dateistand

- `./scripts/check-runtime-deploy-gate.sh` → **Exit 0**
- SHA256 Workspace == `/opt` fuer:
  - `backend/core/rescue_iso_build_executor.py`
  - `backend/core/rescue_iso_build_state.py`
  - `backend/app.py`
- `GET /api/version`:
  - HTTP `200`
  - `backend_runtime_path = /opt/setuphelfer/backend`

### Rescue-ISO-Smokes

- `GET /api/dev-dashboard/rescue-iso/status`:
  - `status = green`
  - `workspace_path = /home/volker/piinstaller`
  - `runtime_path = /opt/setuphelfer`
  - `build_tree.path = /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`
  - `temp_runtime_bundle.status = ok`
  - `dpkg_preflight.status = pre_chroot_ok`
  - `stale_state.needs_sudo_clean = false`
  - `iso_build.status = not_started`
  - `usb_write.allowed = false`
  - `next_operator_action.type = operator_sudo_required`
- `POST /api/dev-dashboard/rescue-iso/step`:
  - `dpkg_preflight` → `ok`
  - `prepare_bundle` → `ok`
  - `validate_bundle` → `ok`
  - `prepare_tree` → `ok`
  - `validate_tree` → `ok`
- `POST /api/dev-dashboard/rescue-iso/step` mit `build_iso_operator_required`:
  - `status = operator_required`
  - Kommandos:
    - `cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"`
    - `./auto/config`
    - `sudo lb build noauto`

### Bewertung

Der Rescue-ISO-Executor ist fuer den read-only/prebuild-Pfad produktiv **gruen**. Der echte ISO-Build bleibt weiterhin ein separater Operator-Sudo-Schritt ausserhalb dieses Strict-Mode-Laufs; deshalb wird kein ISO-Erfolg vorgetaeuscht.

## Zweiter echter ISO-Build-Versuch (fe36af0)

Nach `fe36af0` wurde der echte Build erneut kontrolliert gestartet, diesmal im Lauf "Controlled Rescue ISO Build + USB Write Gate + First Boot Prep".

### Vor dem Build

- Runtime-Gate: **Exit 0**
- `detect_stale_state` vor dem Build: **ok**, `needs_sudo_clean = false`
- `prepare_bundle`, `validate_bundle`, `prepare_tree`, `validate_tree`: **ok**
- `dpkg_preflight`: **ok** / `pre_chroot_ok`
- Dashboard-Befehl blieb korrekt:
  - `cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"`
  - `./auto/config`
  - `sudo lb build noauto`

### Ergebnis

- `LB_EXIT = 127`
- keine `.iso`
- primaerer Fehler:

```text
/usr/bin/env: 'rsvg': No such file or directory
LB_EXIT=127
```

- `scan_iso` → **review_required**
  - `iso_found = false`
  - heuristische `secret_hits` und `cdn_hits`
- `summarize` → **ok**
- Dashboard danach:
  - `status = red`
  - `next_operator_action.type = sudo_clean_required`
  - `stale_state.needs_sudo_clean = true`
  - `usb_write.allowed = false`

### Bewertung

Der Executor-/Dashboard-Pfad bleibt fuer Prepare-/Validate-Schritte verifiziert. Der zweite echte Build war jedoch erneut **fehlgeschlagen**; deshalb blieb die USB-Phase strikt blockiert und wurde nicht gestartet.

## Nachtrag: Deploy-Drift-False-Positive (`2c7e9ee`, 2026-05-27)

- Bekannter Blocker **nicht** `runtime_file_outdated` am Packaging-Helper, sondern `workspace_dirty_uncommitted` mit Dashboard-False-Positive.
- Nach Code-Fix und Helper-Deploy zu `/opt` soll `operator_policy_gate` nicht mehr allein wegen dieses Drifts blockieren; `usb_write.allowed` bleibt **false**.
- Evidence: `docs/evidence/dev-dashboard/DEPLOY_DRIFT_SINGLE_FILE_FIX.md`
- Naechster enger Prompt nach gruenem internen Gate: `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`
