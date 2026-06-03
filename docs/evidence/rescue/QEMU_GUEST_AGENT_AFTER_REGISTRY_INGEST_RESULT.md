# QEMU Guest Agent Smoke After Port Registry — Ingest Result

**Datum:** 2026-06-03  
**run_id:** `qemu_rescue_developer_autopilot_20260603_111427`  
**HEAD (Smoke):** `77253b5`

## Kurzfassung

Port-/Profil-/Devserver-Preflight war **grün**. QEMU lief mit developer-qemu-ISO, Serial **135 KiB**, Boot + systemd + **Autopilot-Start** OK. **Kein Devserver-Report** am Host (`guest_found=false`, `report_new=false`). Release-Trap danach **ok**.

**Keine neue QEMU-Ausführung** in diesem Ingest.

## Root Cause (primär)

**`autopilot_network_or_api_report_failed`** — Serial-JSON im Gast:

- `ModuleNotFoundError: No module named 'devserver_agent'`
- Proxy-Health: `"Invalid Host header"`
- `SETUPHELFER_DEVSERVER_AGENT_ERROR:agent_send_failed`

ISO-Profil ist **nicht** der Blocker (Validator exit 0, Autopilot-Unit startet).

## Evidence-Kette

| Dokument |
|----------|
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_INGEST_PHASE0.md` |
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_RAW_REVIEW.md` |
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_FLEET_REVIEW.md` |
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_ISO_REVIEW.md` |
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_FAILURE_CLASSIFICATION.md` |
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_NEXT_PROMPT.md` |
| `QEMU_GUEST_AGENT_AFTER_REGISTRY_INGEST_TEST_RESULT.md` |
| `qemu_guest_agent_after_registry_ingest_latest.json` |

## Nächster Schritt

Siehe **`QEMU_GUEST_AGENT_AFTER_REGISTRY_NEXT_PROMPT.md`**: Rescue-Squashfs `devserver_agent`-Import + Proxy Host-Header, dann ISO-Rebuild + erneuter Operator-Smoke.
