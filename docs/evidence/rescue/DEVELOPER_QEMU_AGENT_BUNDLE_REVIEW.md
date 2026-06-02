# Developer QEMU Agent Bundle Review (Phase 3)

**Datum:** 2026-06-02  
**Logs:** `developer_qemu_agent_bundle_occurrences_latest.log`, `developer_qemu_bundle_prepare_review_latest.log`

## Checkliste

| Prüfpunkt | Ergebnis |
|-----------|----------|
| `devserver_agent` im Bundle | **yes** (`includes.chroot/opt/setuphelfer-rescue/backend/devserver_agent/`) |
| `rescue_agent` im Bundle | **no** |
| Autopilot erwartet | **devserver_agent** (`setuphelfer-qemu-smoke-autopilot.sh` → CLI) |
| System-Report-Flow | Autopilot-Unit mit `http://10.0.2.2:8001` (QEMU user-mode NAT) |
| Muss `backend/rescue_agent` ins ISO? | **no** — für QEMU-Autopilot-Smoke nicht erforderlich |

## Begründung

- Operator-Smoke-Failure: Agent nicht gestartet (Enable-Gap + Serial), nicht Bundle-Missing für devserver_agent.
- `rescue_agent/` ist Backend-Contract-Stub für Fleet-Ingest (E2EE `contract_stub_only`); separater Pfad.
- Kein unnötiges Modul hinzugefügt.

## Status

**ok**
