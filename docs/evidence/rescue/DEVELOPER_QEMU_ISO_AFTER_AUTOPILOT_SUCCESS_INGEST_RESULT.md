# Developer-QEMU ISO After Autopilot Success — Ingest Result

**Datum:** 2026-06-03  
**HEAD (vor Commit):** `0190a1a`  
**Branch:** `main`

## Kernergebnis

Developer-QEMU ISO nach Autopilot-Wants-Fix ist **verifiziert**. Autopilot-Wants ist im Squashfs belegt. Squashfs-Validator Exit **0**. ISO-SHA neu (`614cc86e…`, ≠ pre-fix `3ee02b36…`).

## Wichtige Leitplanken

- Vorherige Guest-Report-Probleme dürfen **nicht** als Guest-Agent-Fehler bewertet werden, wenn Host-Devserver/`local_lab` deaktiviert war (`release`, `dev_control_enabled=false`, Routen `PROFILE_ROUTE_BLOCKED`).
- QEMU-Smoke nur mit `local_lab`, `dev_control_enabled=true`, Fleet- und Dev-Dashboard-API HTTP 200.
- Preflight-Guard in `qemu-guest-agent-smoke-operator.sh` gehärtet (Exit 21 bei Block).
- Rescue bleibt ohne erfolgreichen QEMU-/Boot-/Guest-Report-Ingest **nicht grün**.

## Readiness

**Status:** `ready_for_qemu_guest_agent_smoke_operator_run`

## Evidence-Dateien

| Datei |
|-------|
| `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_SUCCESS_INGEST_PHASE0.md` |
| `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_BUILD_SUMMARY_REVIEW.md` |
| `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_ARTIFACT_VERIFY.md` |
| `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_SQUASHFS_REVIEW.md` |
| `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_SERIAL_FINGERPRINT.md` |
| `QEMU_GUEST_AGENT_DEVSERVER_PREFLIGHT_ANALYSIS.md` |
| `QEMU_GUEST_AGENT_DEVSERVER_PREFLIGHT_GUARD_RESULT.md` |
| `developer_qemu_iso_after_autopilot_success_ingest_latest.json` |
| `developer_qemu_iso_after_autopilot_squashfs_validator_latest.log` |
| `developer_qemu_iso_after_autopilot_serial_fingerprint_latest.log` |
| `developer_qemu_iso_after_autopilot_wants_check_latest.txt` |

## Offene Risiken

- Runtime aktuell noch `release` — Smoke schlägt ohne Operator-Profilwechsel erwartbar am Preflight fehl (gewollt).
- Port 8001 kann bei stale Proxy-Lauf warnen; Operator vor Smoke prüfen.
- Guest-Report-Erfolg hängt weiterhin von Proxy + Fleet-Ingest ab (nicht in diesem Lauf getestet).

## Nächster sinnvoller Schritt (Operator)

1. `./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh` (aktiviert `local_lab`, Preflight, QEMU, Release-Trap)
2. Vorher optional manuell prüfen: `/api/version` → `local_lab`, `dev_control_enabled=true`; `/api/fleet/sessions` und `/api/dev-dashboard/status` → HTTP 200
3. Release-Trap nach Smoke verifizieren
4. Smoke-Ergebnis ingestieren
