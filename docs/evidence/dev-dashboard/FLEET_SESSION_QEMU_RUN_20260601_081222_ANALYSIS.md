# Fleet Session — QEMU-Lauf `081222`

**SESSION_ID:** `fleet-qemu_rescue_developer_autopilot_20260601_081222`  
**RUN_ID:** `qemu_rescue_developer_autopilot_20260601_081222`  
**Analyse:** 2026-06-01 (read-only)

## API-Snapshot (`GET /api/fleet/sessions/{id}`)

| Feld | Wert |
|------|------|
| status | `timeout` |
| severity | `error` |
| created_at | `2026-06-01T08:12:22+00:00` |
| updated_at / finished_at | `2026-06-01T08:33:25+00:00` |
| qemu.pid | null |
| qemu.exit_code | **null** |
| qemu.acceleration | `unknown` |
| qemu.timeout_seconds | 1200 |
| host.has_kvm | true |
| host.kvm_enabled | **false** (nie per Heartbeat gesetzt) |
| guest.report_seen | false |
| guest.dev_server_report_new | false |
| serial.exists | false |
| serial.size_bytes | 0 |
| serial.path | `""` |
| heartbeat.last_heartbeat_at | `2026-06-01T08:12:22+00:00` (nur Create) |
| heartbeat.stalled | true |
| heartbeat.stall_reason | `heartbeat_exceeded_timeout_window` |
| findings | `heartbeat_delayed`, `timeout_warning` |

## JSONL-Timeline (`fleet_sessions.jsonl`)

| updated_at | status | qemu.exit_code | serial.size_bytes | findings |
|--------------|--------|----------------|-------------------|----------|
| 08:12:22 | starting | null | 0 | [] |
| 08:15:24 | timeout_warning | null | 0 | heartbeat_delayed, timeout_warning |
| 08:33:25 | timeout | null | 0 | heartbeat_delayed, timeout_warning |

Nur **3** Einträge — keine Heartbeat-Zeilen mit `qemu_starting` / `booting` / `autopilot_waiting` in JSONL (entweder API-Heartbeats nicht persistiert als Zeilen, oder Heartbeat-POSTs fehlgeschlagen).

## Pflichtbewertung Fleet-Telemetrie

| Kriterium | Ergebnis |
|-----------|----------|
| Fleet-Telemetrie grundsätzlich funktioniert | **teilweise ja** — Create + stale timeout sichtbar |
| Heartbeats während Lauf sichtbar | **nein** — `last_heartbeat_at` unverändert |
| Finish geschrieben | **ja** — `finished_at`, terminal `timeout` |
| qemu_exit_code dokumentiert | **nein** — bleibt `null` trotz Wrapper `QEMU_EXIT=124` |
| serial_size dokumentiert | **ja** — 0 (aber `serial.exists=false`, Pfad leer) |
| guest_report_missing in findings | **nein** — Finish-Findings aus Wrapper nicht in Session |
| Session-Ende | `timeout` |

## Interpretation

1. **Wrapper JSON-Fix (`3af6f06`)** — Session **wurde** angelegt; kein Python-`NameError` mehr (im Gegensatz zu `080405`).
2. **Heartbeat-Lücke:** Während ~20 min QEMU keine erfolgreiche Heartbeat-Aktualisierung → Backend setzt nach `timeout_seconds + 60` Status `timeout` und `finished_at` (`_apply_stale_rules` in `fleet_session_state.py`). Das erklärt `finished_at` **ohne** sichtbares `qemu.exit_code=124` und **ohne** Finish-Findings `serial_empty` / `qemu_timeout_124` aus `fleet_session_finish_payload`.
3. **Finish-Payload vom Wrapper** enthält `qemu_exit_code: 124` und Findings — in `latest.json` **nicht** angekommen → Finish-POST vermutlich fehlgeschlagen oder von stale-GET überschrieben; weiterer Fix-Kandidat: `FIX_FLEET_SESSION_FINISH_AFTER_QEMU_EXIT` (sekundär, **nach** Serial-Sichtbarkeit).

## Abgrenzung `080405`

`080405`: Fleet-Wrapper kaputt, Session unzuverlässig — **nicht** als Boot-Referenz für `081222` verwenden.

## Guardrails

- Kein neuer QEMU-Lauf in dieser Analyse
- Kein Push
