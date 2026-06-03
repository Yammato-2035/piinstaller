# QEMU Guest Agent After Registry — Fleet Review

**Datum:** 2026-06-03  
**session_id:** `fleet-qemu_rescue_developer_autopilot_20260603_111427`

## Live-API unter release (nach Trap)

Fleet-Routen **404** `PROFILE_ROUTE_BLOCKED` — erwartet, korrekt dokumentiert.

Artefakt: `qemu_guest_agent_after_registry_fleet_release_block_latest.txt`

## Persistenz (`/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/`)

| Feld | Wert |
|------|------|
| Fleet-Session angelegt | **yes** |
| `status` (final) | **timeout** |
| `agent_state` | **booting** (nie fortgeschritten) |
| `findings` | `qemu_timeout_124`, `guest_report_missing` |
| `guest.report_seen` | **false** |
| `guest.dev_server_report_new` | **false** |
| `guest.guest_node_id` | **null** |
| `qemu.exit_code` | **124** |
| `serial.size_bytes` | **135299** |

Persistenz-Pfade: `fleet_sessions_latest.json`, `fleet_sessions.jsonl`  
Such-Log: `qemu_guest_agent_after_registry_fleet_files_latest.log`, `qemu_guest_agent_after_registry_session_refs_latest.log`

## Bewertung

| Frage | Antwort |
|-------|---------|
| release-block korrekt | **yes** |
| Session-Evidence vorhanden | **yes** |
| Guest-Report ingested | **no** |

## Status

**guest_report_missing**

Fleet dokumentiert den Lauf korrekt; Gast lieferte keinen ingestierbaren Devserver-Report.
