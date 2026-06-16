# FAQ — Development Control Center (DE)

## Wo ist die Roadmap?

Tab **Roadmap** im Development Control Center. Daten kommen aus `/api/dev-dashboard/roadmap`.

## Warum ist SSH rot/grau?

SSH **disabled** ist im Lab-MVP **gewollt** und wird als sicherer Zustand (grün) angezeigt, nicht als Fehler.

## Warum keine Public Uploads?

Public Rescue Auto-Upload bleibt blockiert. **Disabled** ist korrekt.

## Was ist der Telemetrieserver?

Der **Development Server** (`local_lab`) — ingest-only, read-only SSH vorbereitet aber deaktiviert.

## Kann ich von hier ein ISO bauen?

Nein. ISO-Build-Status bleibt **pending** bis echte Build-Evidence existiert. Der Rettungsstick-Build läuft über `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build` im Operator-Terminal — nicht aus dem DCC.

Stand Rettungsstick-Produktisierung (1.7.7.0): Start Assistant, WLAN-Fix, Boot-Menü in `live.cfg.in` — siehe `docs/knowledge-base/rescue/RESCUE_START_ASSISTANT_OVERVIEW.md`.

## Sind die Doku-Zahlen live?

Read-only Scan von `docs/` — keine manuellen Hardcodes.

## Warum sehe ich eine Lab-Session, aber keinen neuen Gast-Knoten?

Das ist in Phase 1 normal: **Host-Session** und **Guest-Node** sind getrennt.
Die Session wird beim Start des Wrappers sichtbar (`starting`, `booting`, `autopilot_waiting`), auch wenn später kein Ingest-Report kommt.

## Wie wird ein QEMU-Timeout angezeigt?

Bei `qemu_exit_code=124` wird die Session als `timeout` markiert.
Zusätzlich bleibt sichtbar, ob `guest_report_seen=false` war.

## Was bedeutet `serial_empty`?

`serial_empty` ist ein **Warning**-Zustand (kein automatischer Hard-Fail).
Er zeigt: Serial-Log existiert, blieb aber nach Bootwartezeit bei 0 Bytes.

## Ist Fleet Session Phase 1 jetzt live abgenommen?

Ja. Die Live-Abnahme wurde erfolgreich durchgeführt:

- `local_lab` aktiv
- `/api/fleet/sessions*` live erreichbar
- genau ein manueller Host-Session-Smoke ausgeführt
- `timeout`/`serial_empty`/`guest_report_missing` live sichtbar
- Runtime danach wieder auf `release` zurückgestellt (`profile_gate: OK`)

Siehe: `docs/evidence/dev-dashboard/FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md`.

## Warum kann Heartbeat `invalid_status` liefern?

Der Heartbeat-Endpoint akzeptiert nur Fleet-Statuswerte aus dem Session-Vertrag.
`status=running` ist dort derzeit nicht erlaubt und wird als `invalid_status` geblockt.

Praktische Regel:

- Im Heartbeat einen erlaubten Status verwenden (z. B. `starting`, `booting`, `serial_active`)
- oder `status` im Heartbeat weglassen, wenn nur Telemetrie (serial/guest) aktualisiert werden soll.

## Warum ist der Diagnose-Export manchmal 404?

Im Runtime-Profil `release` sind Dev-Diagnostics/Fleet-Routen nicht immer aktiv.
Für Live-Export ist ein geeigneter Lab-Modus (z. B. `local_lab`) plus entsprechender Runtime-Stand nötig.
