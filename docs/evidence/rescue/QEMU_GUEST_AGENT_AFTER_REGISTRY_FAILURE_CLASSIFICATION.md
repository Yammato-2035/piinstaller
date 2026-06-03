# QEMU Guest Agent After Registry — Failure Classification

**Datum:** 2026-06-03  
**run_id:** `qemu_rescue_developer_autopilot_20260603_111427`

## Kontext (nicht Blocker)

- Port-Registry live, Devserver-Preflight grün (`local_lab`, fleet/dashboard 200)
- ISO `developer-qemu`, Serial 135 KiB, Boot + systemd + Autopilot-Unit-Start OK
- Release-Trap nach Smoke erfolgreich

## Primäre Klassifikation

**`autopilot_network_or_api_report_failed`** (Matrix **D**)

Autopilot startete und schrieb Serial-JSON, aber **kein Devserver-Report** am Host (`report_new=false`, `guest_found=false`).

### Konkrete Ursache (Serial-JSON im Gast)

1. **`ModuleNotFoundError: No module named 'devserver_agent'`** beim Aufruf von  
   `python -m devserver_agent` aus `/opt/setuphelfer-rescue/backend/` — Python-Paket/Import-Pfad im Rescue-Squashfs unvollständig.
2. **`host_health_raw: "Invalid Host header"`** — Proxy-Health-Probe vom Gast liefert kein JSON (Host-Header/Proxy-Konfiguration).
3. **`agent_send_ok: false`**, Marker `SETUPHELFER_DEVSERVER_AGENT_ERROR:agent_send_failed`.

## Sekundäre Klassifikationen

| ID | Beschreibung |
|----|--------------|
| `devserver_agent_module_missing_in_rescue_squashfs` | Import scheitert trotz vorhandenem Verzeichnis `backend/devserver_agent/` |
| `proxy_invalid_host_header_on_health_check` | Gast-Health gegen `10.0.2.2:8001` → Text „Invalid Host header“, nicht JSON |
| `guest_run_id_mismatch` | Host `…111427` vs. Gast-JSON `qemu_smoke_20260603_111445` (Matching-Risiko) |
| `qemu_timeout_124_after_autopilot_finished` | Autopilot endete früh; VM lief bis 1200s-Timeout weiter |

## Ausgeschlossen

- Port-/Profil-Gating (Preflight grün)
- Serial leer / Bootloader hängt / kein Kernel / kein systemd
- Autopilot-Unit fehlt in ISO (Validator + Serial: Unit startet)
- Falsches ISO-Profil (`standard` ohne ttyS0)

## Nächste technische Richtung

Rescue-ISO: **`devserver_agent` als importierbares Python-Paket** (venv/PYTHONPATH/Install-Hook) + Proxy **Host-Header** für Lab-Health tolerieren oder dedizierten Health-Pfad ohne Host-Check.
