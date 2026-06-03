# Devserver Agent ISO Report Fix — Serial Review

**run_id:** `qemu_rescue_developer_autopilot_20260603_111427`

| Prüfung | Ergebnis |
|---------|----------|
| Autopilot-Service gestartet | **yes** |
| Python Traceback | **yes** |
| Fehlendes Modul | `devserver_agent` (Import aus `/opt/setuphelfer-rescue/backend/devserver_agent/__init__.py` mit PYTHONPATH ohne `backend/`) |
| Proxy-/Health-Fehler | `"Invalid Host header"` (Gast-Host `10.0.2.2:8001` vs. TrustedHost) |
| Report an Host gesendet | **no** |

## Klassifikation

- `devserver_agent_import_failure` (primär)
- `proxy_invalid_host_header`
- `agent_report_send_failed`

Artefakt: `devserver_agent_iso_report_fix_serial_errors_latest.log`
