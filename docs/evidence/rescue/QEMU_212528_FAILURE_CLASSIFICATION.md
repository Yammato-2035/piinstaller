# QEMU 212528 — Failure Classification

**Run:** `qemu_rescue_developer_autopilot_20260603_212528`

## Primär

**`guest_report_payload_or_ingest_failure`**

Fix `886a098` war live (`/opt` + neues ISO). Serial zeigt:

- Autopilot startet und erreicht Report-Versuch
- **Kein** `ModuleNotFoundError`
- **Kein** `Invalid Host header`
- **`agent_send_failed`** bleibt
- Host: `dev_server_report_new=false`, Reports unverändert (0→0)

Nächster Schritt: HTTP-Status/Response-Body aus Autopilot-`agent_send_raw` und Host-Backend-Logs unter `local_lab` extrahieren (POST `/api/dev-server/reports`).

## Sekundär

| Klassifikation | Begründung |
|----------------|------------|
| `autopilot_report_send_failed_new_reason` | Neuer Fehlerklassen-Wechsel vs. Run `111427` |
| `qemu_timeout_124` | Fleet final `timeout`; VM lief bis Wrapper-Timeout |
| `iso_validator_regex_false_negative` | Exit 21 trotz Fix in Squashfs (subprocess vs. Shell-Grep) |

## Ausgeschlossen (Primärursache)

| Ausgeschlossen | Grund |
|----------------|-------|
| Port-/Profilfehler | Preflight `DEVSERVER_PREFLIGHT_OK`; Proxy 8001 ok; DCC-Block nur post-Trap unter `release` |
| `qemu_ran_against_old_runtime_or_iso` | Deploy + Rebuild `bae2be32…` vor Smoke |
| `devserver_agent_import_still_broken` | Kein ModuleNotFound in Serial |
| `trusted_host_or_proxy_header_fix_incomplete` | Kein Invalid Host in Serial |

## USB

**Gesperrt** — Guest-Report nicht grün.
