# Devserver Agent ISO Report Fix — Result

**Datum:** 2026-06-03  
**Basis-QEMU:** `qemu_rescue_developer_autopilot_20260603_111427`

## Kurzfassung

Ports/Profile/Devserver-Preflight waren **nicht** der Blocker. Gast bootet bis Autopilot; Fehler lag am **Import-/Report-Pfad**:

1. `ModuleNotFoundError: devserver_agent` — falsches `PYTHONPATH` + `-m backend.devserver_agent.cli`
2. `"Invalid Host header"` — Lab-Proxy + TrustedHost ohne `10.0.2.2` / fehlender curl-Host-Override

## Fix (Workspace, kein ISO-Build)

- Autopilot: `PYTHONPATH=/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue`, `-m devserver_agent.cli`, Health-curl mit `Host: 127.0.0.1:8000`
- Dev-Agent-Unit + prepare: gleiches PYTHONPATH
- Backend: `10.0.2.2` in `_get_allowed_hosts()` unter `local_lab`
- Validator: Import-/Autopilot-/Host-Checks (Exit 18–21)

Alter ISO-Validator: **exit 21** (erwartet).

## Evidence-Kette

| Dokument |
|----------|
| `DEVSERVER_AGENT_ISO_REPORT_FIX_PHASE0.md` |
| `DEVSERVER_AGENT_ISO_REPORT_FIX_SERIAL_REVIEW.md` |
| `DEVSERVER_AGENT_ISO_REPORT_FIX_REPO_MODULE_REVIEW.md` |
| `DEVSERVER_AGENT_ISO_REPORT_FIX_SQUASHFS_REVIEW.md` |
| `DEVSERVER_AGENT_ISO_REPORT_FIX_DECISION.md` |
| `DEVSERVER_AGENT_ISO_REPORT_FIX_TEST_RESULT.md` |
| `devserver_agent_iso_report_fix_latest.json` |

## Operator-Nächste Schritte

1. Build-Tree clean (Operator)
2. `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu ./scripts/rescue-live/prepare-controlled-live-build-tree.sh`
3. Controlled ISO build `--profile developer-qemu`
4. `./scripts/rescue-live/validate-rescue-iso-squashfs.sh` → Exit **0**
5. QEMU Guest Agent Smoke (`local_lab` + Release-Trap)

Kein ISO/QEMU/USB in diesem Ingest-Lauf.
