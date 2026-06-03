# Next Prompt — QEMU 212528 Agent Send Failure

## Titel

`Debug Developer-QEMU Guest Report POST After 886a098 Fix`

## Kontext

- Deploy + ISO-Rebuild erledigt (ISO SHA `bae2be32…`, `/opt` mit `10.0.2.2`).
- Run `212528`: Autopilot ok, **kein** ModuleNotFound/Invalid Host, aber `agent_send_failed`, `report_new=false`.
- ISO-Validator Exit 21 = Regex-Gap (subprocess-Aufruf), **kein** fehlender Fix in Squashfs.

## Auftrag

1. Autopilot-Script: `agent_send_raw` vollständig auf Serial schreiben (oder in `/run/setuphelfer/` persistieren).
2. Unter `local_lab`: manuell gleichen POST wie Gast reproduzieren (`curl` via Proxy `127.0.0.1:8001`, `Host: 127.0.0.1:8000`).
3. Backend: Response-Code/Body für `/api/dev-server/reports` und Health prüfen.
4. Validator: `validate-rescue-iso-squashfs.sh` Regex für Python-subprocess `-m devserver_agent.cli` erweitern.
5. **Kein** USB bis `guest_report_received=true`.

## Erfolg

- Serial/Logs zeigen HTTP 2xx auf Report-POST
- Host `dev_server_report_new=true`
- Fleet `guest.report_seen=true`
- Kein `agent_send_failed`
