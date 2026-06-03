# Devserver Agent Fix — QEMU Smoke Result

**Status:** **blocked** (ISO-Rebuild + Deploy ausstehend)

| Feld | Wert |
|------|------|
| `qemu_smoke_exit` | **n/a** (dieser Lauf) |
| run_id | — |
| qemu gestartet | **no** (dieser Lauf) |
| serial size | — |
| bootloader/kernel/systemd/autopilot gesehen | — |
| ModuleNotFoundError noch vorhanden | **yes** (letzter Run `20260603_111427`, pre-fix ISO) |
| Invalid Host header noch vorhanden | **yes** (gleicher Run) |
| Guest report received | **no** |
| Fleet final status | `guest_report_missing` (Run `20260603_111427`) |
| Release restored after | **yes** (Operator Terminal 6, Trap nach Run `111427`) |

QEMU-Smoke in diesem STRICT-Lauf **nicht** gestartet — ohne Deploy + ISO-Rebuild wäre Ergebnis nicht aussagekräftig.

Referenz-Fehlerklasse (vor Fix): `autopilot_network_or_api_report_failed` — `ModuleNotFoundError: devserver_agent`, Proxy `Invalid Host header`, `agent_send_failed`.
