# QEMU Guest Report Payload — Triage Test Result

**Status:** `partial`

| Check | Ergebnis |
|-------|----------|
| Bash `-n` rescue-live/*.sh | **ok** |
| pytest (venv) | **blocked** — kein pytest in `/opt` venv / system |
| unittest (15 Tests) | **ok** (exit 0) |
| Neue Tests | `test_devserver_agent_guest_report_payload_fix_v1.py` |

Log: `qemu_guest_report_payload_pytest_latest.log`
