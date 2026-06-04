# QEMU 143148 — Failure Classification

## Primär

**`review_required`**

## Begründung

Serial zeigt vollständige Send-Instrumentierung (`SEND_TARGET`, `SEND_HTTP_STATUS`, `SEND_RESPONSE_BODY`), aber **kein HTTP-Ingest**: `http_status=0`, CLI-Exit wegen **GLIBC_2.38** auf dem Rescue-venv (`/opt/setuphelfer-rescue/backend/venv/bin/python3`) vs. Debian-Live-Basis (Bookworm).

Keine der engeren HTTP-/Token-/Schema-Klassen trifft zu (kein 401/403/422, kein `dev_server_disabled` — Preflight war `local_lab` + Health JSON ok).

## Sekundär

* `guest_rescue_venv_glibc_mismatch`
* `agent_send_failed`
* `qemu_timeout_124`
* `serial_report_parser_partial` (`guest_smoke_from_serial=null`, Marker dennoch lesbar mit `grep -a`)

## Nicht Primär

Ports, DCC, Profil-Preflight — Operator-Log: `DEVSERVER_PREFLIGHT_OK`, Fleet/Dashboard HTTP 200 unter `local_lab`.

**USB gesperrt.**
