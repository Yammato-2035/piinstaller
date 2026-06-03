# Backend Down After Release Restart — Result

**Datum:** 2026-06-03  
**HEAD (vor Commit):** `cce563b`  
**Branch:** `main`

## Zusammenfassung

Port **8000** war nach DCC-Deploy und geplantem **Release-Restart** kurz **down** (`curl: (7)`). Ursache belegt: systemd-Unit-Änderungen ohne vorheriges **`daemon-reload`** plus transientes Fenster während **Backend-Restart** (Operator-Terminal: Reload+Restart, sofortiger curl noch fehlgeschlagen). **Recovery erfolgreich** — kein Import-/Deploy-Schaden.

| Aussage | Wert |
|---------|------|
| Port 8000 war down | **yes** (nach Deploy / nach erstem Restart-Probe) |
| Ursache belegt | **yes** (`systemd_reload_required` + Restart-Race) |
| Recovery | **recovered** |
| QEMU ausgeführt | **no** |
| ISO / lb / USB / Backup / Restore | **no** |
| DCC-Fix deployed | **yes** (unter `/opt`; release blockiert API erwartungsgemäß) |
| QEMU-Smoke freigegeben | **yes** (release green, :8000 200) |

## Gates (nach Recovery)

- `install_profile=release`, `profile_gate_status=green`, `dev_control_enabled=false`
- `/api/dev-dashboard/recent-evidence` → `PROFILE_ROUTE_BLOCKED`
- `check-runtime-profile-deploy-gate.sh` → Exit **0**
- Legacy gate Exit **20** (informational unter release)

## Nächster Schritt

**QEMU Guest Agent Smoke Operator Run** — `./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh` (Operator-Terminal, sudo/local_lab Preflight laut Skript).

## Evidence-Dateien

- `BACKEND_DOWN_AFTER_RELEASE_RESTART_PHASE0.md`
- `BACKEND_DOWN_AFTER_RELEASE_RESTART_JOURNAL_REVIEW.md`
- `backend_down_after_release_restart_backend_journal_latest.log` (leer ohne sudo)
- `BACKEND_DOWN_AFTER_RELEASE_RESTART_OPT_IMPORT_REVIEW.md`
- `BACKEND_DOWN_AFTER_RELEASE_RESTART_RESTART_RESULT.md`
- `BACKEND_DOWN_AFTER_RELEASE_RESTART_POST_RESTART_REVIEW.md`
- `BACKEND_DOWN_AFTER_RELEASE_RESTART_GATE_RESULT.md`
- `backend_down_after_release_restart_profile_gate_latest.log`
- `backend_down_after_release_restart_legacy_gate_latest.log`
- `backend_down_after_release_restart_version_recovered.json`
- `backend_down_after_release_restart_recent_evidence_release_block.txt`
- `backend_down_after_release_restart_api_after_restart.txt`
- `DCC_RECENT_EVIDENCE_AFTER_BACKEND_RECOVERY_READINESS.md`
- `BACKEND_DOWN_AFTER_RELEASE_RESTART_TEST_RESULT.md`

## Offene Risiken

- Agent kann **journalctl** und **sudo restart** nicht ohne Operator reproduzieren.
- Broad `pytest -k dev_dashboard` trifft auf unrelated Collection-Errors — gezielter recent_evidence-Test grün.
