# SETUPHELFER-E2E-LIVE-001D4 — Full Automation IST Audit

**Audit date:** 2026-07-14  
**Payload:** 1.10.0.22  
**Branch HEAD:** bafce68e (pre-001D4 implementation commit pending)

## Vorhandene Automation (bestanden)

| Komponente | Pfad | Status |
|------------|------|--------|
| Unattended E2E Service | `scripts/rescue-live/image/setuphelfer-rescue-auto-physical-e2e` | im Payload 1.10.0.22 |
| systemd Unit | `setuphelfer-rescue-auto-physical-e2e.service` | After MSI-Evidence |
| MSI Auto-Evidence | `setuphelfer-rescue-auto-msi-evidence.service` | Timeout 900s, late gate |
| Shutdown Failsafe | `setuphelfer-rescue-lab-auto-shutdown-failsafe.timer` | 420s, nur wenn Evidence fehlt |
| Physical Orchestrator | `backend/core/rescue_physical_e2e_orchestrator.py` | Backup/Verify/Restore real |
| Event Emitter | `backend/core/rescue_physical_e2e_event_emitter.py` | 8 kanonische Events |
| Receipt Journal | `backend/core/rescue_physical_e2e_journal.py` | Redaction aktiv |
| Storage Safety | `backend/core/rescue_physical_e2e_storage_safety.py` | Pfad-Blockliste |
| Evidence Import | `backend/core/rescue_physical_e2e_evidence_import.py` | Token-Ausschluss |
| GRUB Auto-Parameter | Stick `grub.cfg` | msi_lab/e2e/shutdown/late_sec=120 |

## 001D4 Ergänzungen (dieser Auftrag)

| Komponente | Pfad | Status |
|------------|------|--------|
| Run-Control | `backend/core/rescue_physical_e2e_run_control.py` | implementiert |
| Testmedium-Marker | `backend/core/rescue_physical_e2e_test_target.py` | implementiert |
| State Machine | `backend/core/rescue_physical_e2e_state_machine.py` | implementiert |
| MSI Identity Gate | `backend/core/rescue_physical_e2e_machine_gate.py` | implementiert |
| Unattended Orchestrator | `backend/core/rescue_physical_e2e_unattended.py` | implementiert |
| Physical MSI Import | `backend/core/rescue_physical_e2e_physical_import.py` | implementiert |
| IONOS Preflight | `backend/core/rescue_physical_e2e_ionos_preflight.py` | implementiert |
| Server Verify | `backend/core/rescue_physical_e2e_server_verify.py` | implementiert |
| prepare test medium | `scripts/rescue/prepare-e2e-live-001d-test-medium.sh` | implementiert |
| prepare run-control | `scripts/rescue/prepare-e2e-live-001d-run-control.sh` | implementiert |
| stage lab token | `scripts/rescue/stage-e2e-live-001d-lab-token.sh` | implementiert |
| verify server | `scripts/verify-e2e-live-001d-server-results.sh` | implementiert |

## Unit-Reihenfolge (systemd)

```text
setuphelfer-rescue-auto-msi-evidence.service
  → setuphelfer-rescue-auto-physical-e2e.service
  → Evidence-Spool-Sync (bestehend)
  → Shutdown via setuphelfer_auto_shutdown=1 (nach E2E in auto-physical-e2e Script)
```

Failsafe-Timer greift nur, wenn `auto-msi-evidence.done` fehlt — kein paralleler vorzeitiger Shutdown nach E2E.

## Ordering-Prüfung

- Auto-E2E `After=` MSI-Evidence: **ja**
- Auto-Shutdown in `setuphelfer-rescue-auto-physical-e2e` erst nach Workflow: **ja**
- SETUP_LOGS vor E2E via `find_setup_logs_mount`: **ja**
- Netzwerk vor Telemetrie via Token + Consent: **ja**
- Timeouts: Evidence 900s, E2E 1200s: **ja**
- Atomare State-Persistenz `.tmp → rename`: **ja**

## Smoke vs. Full Physical

| Modus | Bedingung | Status |
|-------|-----------|--------|
| `automation_smoke_only` | Kein registriertes externes Testmedium | `/run`-Fallback |
| `physical_full` | Gültiger `setuphelfer-e2e-target.json` + Run-Control | Zielpfad |

Smoke erzeugt **nicht** `physical_rescue_telemetry_diagnostics_e2e_passed`.

## Offene physische Schritte

- MSI GE63 Boot (Operator)
- Registriertes externes USB-Testmedium am MSI
- Import + Serververification nach Stick-Rückkehr

**Gesamtstatus:** `implemented_pending_physical_msi_run`
