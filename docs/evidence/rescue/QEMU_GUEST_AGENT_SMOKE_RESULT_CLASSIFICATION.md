# QEMU Guest Agent Smoke — Result Classification

**Datum:** 2026-06-03

## root_cause_classification

**`qemu_operator_smoke_incomplete`**

## Was ist belegt?

- Developer-QEMU ISO nach Autopilot-Fix ist verifiziert (SHA `614cc86e…`, Validator Exit 0, Autopilot-Wants).
- Preflight-Guard ist im Skript implementiert (Commit `b5075a5`).
- Release-Trap funktioniert: Runtime wieder `release`, Dev-Routen blockiert.
- **Einziger** Operator-QEMU-Evidence-Run: `20260602_202725` — **vor** ISO-Rebuild und **ohne** `DEVSERVER_PREFLIGHT_OK`.
- Dieser alte Run: Serial **0 B**, Exit **124**, `guest_report_missing`, Standard-ISO-Profil-Mismatch (bereits klassifiziert).

## Was ist ausgeschlossen?

- **Kein** post-Preflight-Smoke mit neuer ISO im Evidence-Baum.
- Kein `ok` / Guest-Report-Erfolg für den angefragten Ingest.
- Kein Fake-Green durch bloßen QEMU-Start.

## Warum blocked?

Operator-Auftrag verlangt Auswertung eines **bereits ausgeführten** Smokes nach Preflight-Guard. Es existiert **kein** passendes Run-Verzeichnis (`head=b5075a5`, `DEVSERVER_PREFLIGHT_OK`, Timestamp nach ISO-Rebuild `2026-06-03T00:05`).

Terminal-6-Log endet mit ISO-Validator — **kein** `qemu-guest-agent-smoke-operator.sh`-Output.

## Sekundäre Referenz (alter Run)

Falls der alte Run `20260602_202725` gemeint war: Klassifikation bleibt `qemu_serial_capture_failure` + `guest_agent_autostart_gap` + Profil-Mismatch — bereits durch Fixes adressiert, aber **nicht** erneut gegen neue ISO verifiziert.

**Gesamt-Status Ingest:** `blocked`
