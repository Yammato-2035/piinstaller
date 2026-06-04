# Runbook — Rescue QEMU Guest Agent Smoke (Operator)

**Ziel:** Developer-QEMU-ISO unter QEMU mit `local_lab` am Host; Gast sendet Devserver-Report über `http://10.0.2.2:8001`; danach **release** wiederherstellen.

## Voraussetzungen

| Check | Erwartung |
|-------|-----------|
| Port-Registry live | `/api/version` → `runtime_ports`, `canonical_urls` |
| ISO | `developer-qemu`, SHA dokumentiert, Validator exit 0 |
| Preflight | `DEVSERVER_PREFLIGHT_OK` (local_lab, fleet/dashboard 200) |
| Proxy | Host `:8001` → Backend `:8000` während Smoke |

Siehe `docs/dev-dashboard/PORTS_AND_PROFILES.md`, `RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_RESULT.md`.

## Operator-Ablauf

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh
```

Evidence: `docs/evidence/runtime-results/rescue/qemu/<run_id>/`

Skript setzt `local_lab`, startet Proxy, QEMU (KVM, kein Host-Disk, kein USB), wartet auf Autopilot; **Trap** stellt `release` wieder her.

## Erfolg

- `qemu_autopilot_result.json`: `status=ok` oder Gast-JSON mit `agent_send_ok=true`
- Devserver: neuer Report (`dev_server_report_new=true`)
- Fleet-Session: `guest.report_seen=true`
- Serial: `SETUPHELFER_QEMU_SMOKE_RESULT_JSON` ohne `agent_send_failed`

## Bekannte Fehlerbilder (2026-06-03)

| Symptom | Ursache | Evidence |
|---------|---------|----------|
| Serial 0 B | Standard-ISO / kein ttyS0 | ältere Runs |
| Autopilot startet, kein Report | `agent_send_failed` — Fix `ddd502e` deploy+ISO-Rebuild; Serial `SEND_HTTP_STATUS` | `PAYLOAD_FIX_REBUILD_QEMU_RESULT.md` |
| DCC „nicht verfügbar“ unter release | Profil-Gate, kein Portfehler | `DCC_PROFILE_STATUS_TRIAGE.md` |
| `guest_found=false`, exit 124 | Autopilot endete, VM lief bis Timeout | run `…111427` |

## Nach Smoke

- Release-Trap prüfen: `/api/version` → `install_profile=release`, Dev-Routen 404
- Kein USB, kein Backup, kein Restore in diesem Pfad

## Siehe auch

- `docs/knowledge-base/recovery/RESCUE_ISO_BUILD_AND_VM_VALIDATION.md`
- `docs/evidence/rescue/QEMU_GUEST_AGENT_AFTER_REGISTRY_NEXT_PROMPT.md`
