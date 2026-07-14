# Rescue E2E Component Audit — SETUPHELFER-E2E-LIVE-001D

## Telemetrie

| Komponente | Pfad | 001D-Nutzung |
|------------|------|--------------|
| v2 Contract | `backend/core/rescue_telemetry_client_contract_v2.py` | Payload-Validierung |
| v2 Payload Builder | `backend/core/rescue_telemetry_payload_v2.py` | Vorlage für Assessment-Block |
| Endpoints | `config/rescue_telemetry_endpoints.json` | Cloud-Profil |
| Cloud Lab Send | `backend/core/rescue_stick_cloud_lab_send.py` | HTTP-Transport-Muster |
| Lab Client | `backend/core/rescue_lab_telemetry_client.py` | HMAC-Lab (nicht 001D primär) |
| Signing | `backend/core/rescue_telemetry_signing_v1.py` | HMAC optional |
| Offline Queue Preview | `backend/core/rescue_lab_telemetry_offline_queue_preview.py` | Erweitern → echter Queue |
| Boot Push (legacy) | `scripts/rescue-live/image/setuphelfer-rescue-telemetry-push` | Nicht duplizieren |

**Strategie:** Neues Modul `rescue_physical_e2e_*` verdrahtet Backup/Verify/Restore-Ergebnisse an `telemetry.rescue.beta.v2` + Bearer-Lab-Credential (wie 001C2-Smoke).

## Backup / Verify / Restore

| Komponente | Pfad | 001D-Nutzung |
|------------|------|--------------|
| File Backup | `modules/backup_engine.create_file_backup` | Echte Archivierung |
| Verify | `modules/backup_verify.verify_deep` | Echte Prüfung |
| Restore Files | `modules/restore_engine.restore_files` | Restore in leeres Ziel |
| Isolated Test | `tools/setuphelfer_restore_isolated_test.py` | Referenz für Allowlist |
| dd Backup | `rescue_backup_execute.py` | **Nicht** für 001D (Testdaten = Dateien) |

## Storage / Sicherheit

| Komponente | Pfad | 001D-Nutzung |
|------------|------|--------------|
| Discovery | `rescue_storage_discovery.py` | Geräteerkennung |
| Role Classifier | `rescue_disk_role_classifier.py` | Rollen + Pair-Validierung |
| Target Policy | `rescue_backup_target_policy.py` | SETUP_LOGS/SETUPHELFER-Block |
| Write Target | `safety_facade.validate_write_target` | Restore-Schutz |

**Erweiterung:** `rescue_physical_e2e_storage_safety.py` — leeres Ziel, Größenprüfung, Restore-Pfad-Blockliste.

## UI / Evidence

| Komponente | Pfad | 001D-Nutzung |
|------------|------|--------------|
| TUI | `setuphelfer-rescue-tui.sh` | Menüpunkt „E2E Backup-/Restore-Test“ |
| Evidence Mirror | `setuphelfer-rescue-common.sh` | SETUP_LOGS-Spiegelung |
| Session Evidence | `rescue_session_evidence.py` | Boot-Session-Korrelation |
| MSI Evidence Import | `scripts/rescue/import-msi-rs011b-evidence.sh` | Post-Run Import |

## USB / Payload

| Komponente | Pfad | 001D-Nutzung |
|------------|------|--------------|
| Version SoT | `config/rescue_payload_version.json` | `1.10.0.20` → Bump bei Build |
| Atomic Update | `rescue_usb_payload_atomic_update.py` | Stick-Update Phase 20 |
| Repack | `repack-rescue-squashfs-react-shell.sh` | Payload-Build |

## Live-Event-Vertrag (001C2)

```
rescue_session_started → backup_started → backup_completed →
verify_started → verify_completed → restore_started → restore_completed →
rescue_session_completed
```

Korrelation: `e2e_run_id`, `event_id`, `device_id_hash`, `rescue_session_id`, `backup_job_id`, `restore_job_id`

## Keine parallele Architektur

Alle neuen Teile erweitern bestehende Engines und den v2-Contract — kein zweites Backup- oder Telemetriesystem.
