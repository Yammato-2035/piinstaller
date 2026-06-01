# Fleet Session — QEMU Bootloader Serial Smoke

**Stand:** 2026-06-01
**RUN_ID:** `qemu_rescue_developer_bootserial_20260601_202000`
**SESSION_ID:** `fleet-qemu_rescue_developer_bootserial_20260601_202000`

## Session

| Feld | Wert |
|------|------|
| Fleet API (live) | **404** — Runtime `release` |
| JSONL-Fallback | `docs/evidence/runtime-results/dev-dashboard/fleet_sessions.jsonl` (falls geschrieben) |
| ISO | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `5c79e35c35a227bdcb9978c1728d8d6aaeef515938ce13358ca6b994d293829a` |

## Ergebnis

| Feld | Wert |
|------|------|
| qemu_exit_code | **124** |
| serial_size_bytes | **132412** |
| serial_non_empty | **yes** |
| acceleration | **kvm** |
| guest_seen / report_new | **false** |
| findings (erwartet bei Erfolg) | serial capture OK; ingest blockiert durch release-Profil |

## Telemetry

- Proxy: `0.0.0.0:8001` (QEMU slirp `10.0.2.2`)
- Host Dev-URL: `http://10.0.2.2:8001` — Gast erreicht Host, aber `/api/dev-server/*` auf Host **404** in release

## Keine Fake-VM

Kein neuer Gast-Knoten ohne belastbaren Report (`report_new=false`).

## Nächster Schritt

Fleet/Diagnostics unter `local_lab` erneut prüfen; Autopilot-Unit-Logs im Gast analysieren.
