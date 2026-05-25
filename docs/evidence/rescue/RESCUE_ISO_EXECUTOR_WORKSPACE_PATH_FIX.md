# Rescue ISO Executor Workspace Path Fix

**Datum:** 2026-05-25
**Workspace HEAD vor Finalisierung:** `f2b13f5`
**Ziel:** produktive Runtime unter `/opt/setuphelfer`, kontrollierter Rescue-ISO-Build-Workspace unter `/home/volker/piinstaller`, kein ISO-Build in diesem Lauf.

## Ausgangsfehler

Im ersten produktiven Dashboard-/Executor-Lauf wurde der Rescue-ISO-Build noch gegen einen falschen Runtime-nahen Build-Kontext ausgewertet:

- Runtime: `/opt/setuphelfer`
- erwarteter Workspace: `/home/volker/piinstaller`
- früherer Operator-Befehl: `cd "/opt/setuphelfer/build/rescue/live-build/setuphelfer-rescue-live"`
- Folgefehler:
  - `prepare_bundle` blockiert
  - `validate_bundle` blockiert
  - `prepare_tree` blockiert
  - `source_head` im Build-Tree veraltet

## Zielpfade

Der jetzt verifizierte Zielzustand ist:

- `runtime_path = /opt/setuphelfer`
- `workspace_path = /home/volker/piinstaller`
- `build_tree_path = /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`
- `temp_runtime_bundle_path = /home/volker/piinstaller/build/rescue/temp-runtime/setuphelfer-rescue-runtime`

## Umgesetzte Logik

- `backend/core/rescue_iso_operator_commands.py`
  - trennt Runtime- und Workspace-Pfad explizit
  - gibt nur noch Workspace-basierte Operator-Kommandos aus
  - blockiert ungueltige oder nicht allowlistete Workspace-Pfade
  - nutzt `git -c safe.directory=...` fuer Workspace-HEAD/Branch
- `backend/core/rescue_iso_build_state.py`
  - liest Dashboard-Status konsistent aus dem Workspace-Build-Tree
  - meldet `workspace_path`, `runtime_path`, `build_tree_path`, `temp_runtime_bundle_path`
  - leitet `source_head` aus dem Workspace ab
- `backend/core/rescue_iso_build_executor.py`
  - fuehrt `prepare_bundle`, `validate_bundle`, `prepare_tree`, `validate_tree` mit `cwd=/home/volker/piinstaller` aus
  - behandelt fehlenden Workspace als `blocked` statt Crash

## Zusatzfixe fuer reproduzierbare Prepare-Schritte

- `scripts/rescue-live/create-temp-runtime-bundle.sh`
  - atomarer Staging-/Rename-Pfad statt hartem rekursivem Loeschen
  - kein `rsync -a`-Metadatenproblem mehr auf fremd besessenen Resten
- `scripts/rescue-live/prepare-controlled-live-build-tree.sh`
  - service-taugliche Dateierzeugung per Tempfile + `mv`
  - lokales `config/bootloaders/isolinux` aus echten Host-Dateien statt kaputter Ubuntu-Symlinks
  - alte `setuphelfer-rescue.old.*`-Verzeichnisse werden aus `config/includes.chroot/opt` in `build/rescue/.trash` verschoben und landen nicht mehr im Build-Tree

## Tests

### Compile

- `backend/venv/bin/python3 -m py_compile backend/core/rescue_iso_build_state.py backend/core/rescue_iso_build_executor.py backend/core/rescue_iso_operator_commands.py backend/app.py` → **ok**

### Pfad-/Executor-Tests

- `PYTHONPATH=backend backend/venv/bin/python3 -m unittest backend.tests.test_rescue_iso_build_dashboard_state_v1 backend.tests.test_rescue_iso_build_executor_v1 -v` → **34 Tests, ok**

Abgedeckte Pflichtfaelle:

- `workspace_path != runtime_path`
- `build_tree_path` unter `/home/volker/piinstaller/build`
- kein `/opt/setuphelfer/build` im Operator-Befehl
- `prepare_bundle` nutzt Workspace-`cwd`
- `validate_bundle` nutzt Workspace-MANIFEST
- `source_head` kommt aus dem Workspace
- `usb_write.allowed` bleibt `false`
- Path-Traversal wird blockiert

### Regressionen

- `PYTHONPATH=backend backend/venv/bin/python3 -m unittest backend.tests.test_deploy_runner_rescue_stick_readonly_build_emulation_v1 backend.tests.test_partitions_storage_facade_v1 backend.tests.test_partitions_hardstop_preview_v2 backend.tests.test_partitions_manifest_layout_preview_v2 backend.tests.test_partitions_restore_handoff_preview_v2 -v` → **41 Tests, ok**

## Lokale Validatoren

- `scripts/rescue-live/create-temp-runtime-bundle.sh` → **ok**
- `scripts/rescue-live/validate-temp-runtime-bundle.sh build/rescue/temp-runtime/setuphelfer-rescue-runtime` → **ok**
- `scripts/rescue-live/prepare-controlled-live-build-tree.sh` → **ok**
- `scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live` → **ok**

Befund:

- `MANIFEST.json.source_head = f2b13f5`
- `build-tree-manifest.json.source_head = f2b13f5`
- keine `.iso`-, `.img`-, `.qcow2`-, `filesystem.squashfs`-, `initrd*`- oder `vmlinuz*`-Artefakte im sauberen Prebuild-Zustand

## Produktive Runtime-Abnahme

### Gate / Runtime

- `./scripts/check-runtime-deploy-gate.sh` → **Exit 0**
- `GET /api/version`:
  - `backend_runtime_path = /opt/setuphelfer/backend`
- `GET /api/dev-dashboard/rescue-iso/status`:
  - `status = green`
  - `workspace_path = /home/volker/piinstaller`
  - `runtime_path = /opt/setuphelfer`
  - `build_tree_path = /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`
  - `temp_runtime_bundle_path = /home/volker/piinstaller/build/rescue/temp-runtime/setuphelfer-rescue-runtime`
  - `build_tree.source_head = f2b13f5`
  - `temp_runtime_bundle.source_head = f2b13f5`
  - `usb_write.allowed = false`
  - `next_operator_action.type = operator_sudo_required`

### Runtime-Executor-Smokes

- `prepare_bundle` → `DEV_DASHBOARD_RESCUE_ISO_STEP_OK` / `ok`
- `validate_bundle` → `DEV_DASHBOARD_RESCUE_ISO_STEP_OK` / `ok`
- `prepare_tree` → `DEV_DASHBOARD_RESCUE_ISO_STEP_OK` / `ok`
- `validate_tree` → `DEV_DASHBOARD_RESCUE_ISO_STEP_OK` / `ok`

### Operator-Build-Befehl

Der produktive Executor gibt jetzt ausschließlich den Workspace-Befehl aus:

```bash
cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./auto/config
sudo lb build noauto
```

Es erscheint **kein** `/opt/setuphelfer/build` mehr.

## Safety

Explizit **nicht** ausgefuehrt:

- kein ISO-Build
- kein `lb build`
- kein USB-Write
- kein `dd`
- kein `mkfs`
- kein `parted write`
- kein Backup
- kein Restore
- kein Verify Deep

## Ergebnis

**Abnahme dieses Fix-Laufs: erfolgreich**

Erfuellt:

- Runtime-Executor nutzt Workspace-Buildpfade
- keine `/opt/setuphelfer/build`-Pfade mehr fuer Prepare-/Build-Ausgabe
- `prepare_bundle`, `validate_bundle`, `prepare_tree`, `validate_tree` in Runtime gruen
- Operator-Build-Befehl zeigt auf `/home/volker/piinstaller`
- Runtime-Gate bleibt gruen
- kein ISO-Build ausgefuehrt
- kein USB geschrieben

## Naechster Schritt

Separater Operator-Lauf fuer den echten ISO-Build:

```bash
cd "/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./auto/config
sudo lb build noauto
```

Erst danach ISO-Scan, SHA256-Evidence und weitere Hardware-/Live-Boot-Abnahmen.
