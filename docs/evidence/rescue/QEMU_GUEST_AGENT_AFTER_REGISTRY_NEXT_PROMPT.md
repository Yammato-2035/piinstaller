# Nächster Prompt — Developer-QEMU Guest Devserver Agent Report Fix

**Titel:** `Developer-QEMU Guest Devserver Agent Report Triage`

## Scope

- **Kein neuer QEMU-Lauf** in Phase 0–Evidence.
- **Kein ISO-Rebuild** bis statische Analyse + Validator-Erweiterung abgeschlossen.
- Kein USB/dd, kein Host-Disk, kein Backup/Restore.

## Ziel

Serial belegt: Autopilot startet, scheitert an **`ModuleNotFoundError: devserver_agent`** und **`Invalid Host header`** auf Proxy-Health. Fix-Pfad definieren und Squashfs-Validator um **Import-Smoke** erweitern.

## Aufgaben

1. **Rescue-Squashfs:** Prüfen ob `devserver_agent` unter `/opt/setuphelfer-rescue/backend/` als Paket installiert ist (PYTHONPATH, `pip install -e`, Hook, venv).
2. **Autopilot-Skript:** Aufruf `python3 -m devserver_agent…` gegen tatsächlichen Layout-Pfad anpassen oder `PYTHONPATH=/opt/setuphelfer-rescue/backend` setzen.
3. **QEMU Lab Proxy:** Health-Endpoint für Gast-Requests von `10.0.2.2` / ohne `Host: 127.0.0.1` — „Invalid Host header“ beheben oder Health-Check im Autopilot umgehen/dokumentieren.
4. **run_id-Konsistenz:** Gast-JSON `qemu_smoke_*` an Host-`run_id` koppeln für Fleet-Matching.
5. **Validator:** `validate-rescue-iso-squashfs.sh` — `python3 -c "import devserver_agent"` im gemounteten Squashfs (developer-qemu).
6. Nach Fix: **ISO-Rebuild** (Operator) → **ein** QEMU-Smoke mit `local_lab` + Release-Trap.

## Evidence-Ziel

`QEMU_GUEST_AGENT_DEVSERVER_AGENT_FIX_RESULT.md` + grüner Smoke mit `report_new=true`.
