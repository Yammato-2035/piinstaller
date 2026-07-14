# PIINSTALLER IST-Audit — SETUPHELFER-E2E-LIVE-001D

## Workspace

| Feld | Wert |
|------|------|
| Pfad | `/home/volker/piinstaller` |
| Repository | `piinstaller` |
| Branch (Audit) | `main` |
| HEAD | `b8651d3` |
| origin/main | `b8651d3` |
| Working Tree | bekannte Drift (72 Einträge, MSI-GUI/auto-evidence) |

## Payload-Version

| Quelle | Version |
|--------|---------|
| `config/rescue_payload_version.json` | `1.10.0.20` |
| `backend/core/rescue_payload_version.py` | Default `1.10.0.20` |

## Live-Stack (read-only, Monorepo `e101058`)

| Komponente | Status |
|------------|--------|
| Öffentlicher HTTPS-Intake | `https://telemetrie.setuphelfer.de/v1/telemetry/ingest` |
| Schema | `telemetry.rescue.beta.v2` |
| Legacy-Mock | deaktiviert |
| Telemetrie-Persistenz | MariaDB |
| Diagnostik-Engine | `real_input_driven` |
| Pipeline-Status | `live_pipeline_ready_for_physical_rescue_test` |

## Vorhandene Rescue-Komponenten

| Bereich | Reife | Kernpfade |
|---------|-------|-----------|
| Telemetrie v2 Contract | 🟡 Preview/Lab | `rescue_telemetry_payload_v2.py`, `rescue_telemetry_client_contract_v2.py` |
| Cloud Lab Send (Workspace) | 🟢 Lab | `rescue_stick_cloud_lab_send.py` |
| Lab HMAC Client | 🟡 Lab | `rescue_lab_telemetry_client.py` |
| Boot Legacy Push | 🟡 Alt | `setuphelfer-rescue-telemetry-push` |
| Backup Engine (Dateien) | 🟢 | `modules/backup_engine.py` → `create_file_backup` |
| Verify Engine | 🟢 | `modules/backup_verify.py` |
| Restore Engine | 🟢 | `modules/restore_engine.py` → `restore_files` |
| Rescue Backup Execute (dd) | 🟡 HW | `rescue_backup_execute.py` |
| Storage Discovery | 🟢 | `rescue_storage_discovery.py` |
| Disk Role Classifier | 🟢 | `rescue_disk_role_classifier.py` |
| USB Atomic Updater | 🟢 | `rescue_usb_payload_atomic_update.py` |
| TUI | 🟢 MSI-stabil | `setuphelfer-rescue-tui.sh` |
| SETUP_LOGS Evidence | 🟢 | `setuphelfer-rescue-common.sh` |

## Lücken für 001D

1. Kein vereinheitlichter Event-Emitter für Backup/Verify/Restore → Cloud v2
2. Kein physisches E2E-Orchestrator-Modul mit Operator-Gate
3. Kein lokales Eventjournal unter `setuphelfer/evidence/e2e/<run_id>/`
4. Kein TUI-Menüpunkt „E2E Backup-/Restore-Test“
5. Kein Testdatenskript `create-e2e-backup-test-data.sh`
6. Kein unabhängiger Manifestvergleich für Restore-Integrität
7. Stick-Boot sendet noch nicht über Live-Ingest mit Receipt-Persistenz

## MSI-Kompatibilität

- GUI default-off unter MSI-Compat (`setuphelfer_rescue_should_disable_gui_for_msi_compat`)
- TUI-Fallback stabil — neue Funktion nur als zusätzlicher Menüpunkt

## Arbeitsfreigabe

**ja** — Feature-Branch `pi-rs-e2e-live-001d-physical-backup-restore` auf Basis `b8651d3`.

`production_ready=false`
