# QEMU Guest Agent Smoke — Run Identification

**Datum:** 2026-06-03

## Neuestes QEMU-Verzeichnis (mtime)

| Feld | Wert |
|------|------|
| Run-ID | `qemu_rescue_developer_autopilot_20260602_202725` |
| QEMU_RUN_DIR | `docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_autopilot_20260602_202725` |

## Dateien

| Datei | Vorhanden |
|-------|-----------|
| qemu_autopilot_result.json | **yes** |
| qemu-serial.log | **yes** (0 Bytes) |
| operator_smoke.log | **yes** |
| fleet/rescue-agent snapshots im Run-Dir | **no** (`fleet_sessions_after_qemu.json` fehlt) |
| dev_server_summary_before/after.json | **yes** |

## Abgleich mit Auftrag

| Erwartung | Ist |
|-----------|-----|
| Smoke nach Preflight-Guard (`b5075a5`) | **nicht belegt** |
| `DEVSERVER_PREFLIGHT_OK` in operator_smoke.log | **no** (`PROFILE_GUARD_OK` only) |
| ISO SHA `614cc86e…` zum Smoke-Zeitpunkt | **nein** (Smoke 2026-06-02 22:27, ISO-Rebuild 2026-06-03 00:05) |

**Status:** `blocked_missing_evidence`

Kein verwertbarer Post-Preflight-/Post-ISO-Rebuild-Smoke im Repo. Nächster Schritt: Operator erneut `./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh` — Evidence-Verzeichnis mit neuem `run_id` und `DEVSERVER_PREFLIGHT_OK` muss entstehen.
