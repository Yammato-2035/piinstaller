# MSI Auto E2E Failure Analysis — Payload 1.10.0.24

## Session

```text
Session:     20260715_113551_boot / 20260715_113609_boot
Payload:     1.10.0.24
Boot UTC:    2026-07-15T11:35:52Z
Collect UTC: 2026-07-15T12:08:09Z–12:08:13Z
Uptime bei Collect: ~1950 s (~32,5 min)
Operator:    manueller Abbruch nach ~30 min (berechtigt)
```

## Gesamturteil

```text
Gesamtstatus:  failed_msi_evidence_completion
Physical E2E:  nicht gestartet
Shutdown:      kein automatischer Failsafe (manueller Abbruch)
```

---

## Belegt

### TUI zeigte irreführend „Evidence wird gesammelt“

- Ab System-Uptime ~150 s setzt `refresh_auto_e2e_phase_from_runtime()` die Phase auf `msi_evidence_running`.
- Der eigentliche Collector (`collect-msi-rs011b-evidence.sh`) lief erst bei Uptime **~1950 s** (4 s Dauer).
- **~30 min** lang zeigte die TUI eine aktive Collect-Phase ohne laufenden Collector.

### MSI-Evidence-Marker fehlt

```text
setuphelfer/evidence/msi-rs011b/msi-evidence-complete.json  → fehlt
```

→ Physical-E2E-Orchestrator startete nicht (Gate nicht erfüllt).

### Run-Control nicht verbraucht

```text
enabled=true
consumed=false
expected_payload_version=1.10.0.24
```

### Physical E2E nicht gestartet

- Kein `e2e-rescue-msi-*` Run auf SETUP_LOGS.
- Import: `new_physical_msi_run_missing`.
- SABRENT: nicht geprüft (kein Destructive-Gate erreicht).

### Collector-Payload-Defekt (RS-011D Supplement)

`rs011d-supplement.log`:

```text
ImportError: cannot import name 'ensure_setup_logs_rw'
  from core.rescue_setup_logs_persistence
```

→ Supplement im SquashFS 1.10.0.24 schlägt fehl (Backend/Bundle-Drift).

### API-Endpunkte im Collector

```text
rescue-health:     HTTP 404
disk-inventory:    HTTP 404
storage-discovery: HTTP 200
```

### Lab-Evaluation vs. Gate-Marker

`lab-auto-result.json`:

```text
result_status: passed
capture_uptime_s: 1953.84
evidence_complete: true
tui_owned: true
```

Evaluation **passed**, aber `msi-evidence-complete.json` fehlt → Gate für Physical E2E nicht geschlossen.

### Failsafe 001D6

- 420-s-Timer **nicht** aktiv (Watchdog/3600-s-Timer im Journal).
- Kein vorzeitiger Failsafe-Shutdown belegt.
- Abbruch durch Operator, nicht durch Heartbeat-Failsafe.

### TUI / Konsole

- `lab-auto-result.json`: `console_owner=tui`, Shield aktiv.
- Operator beobachtete dennoch **Kommandozeilen unter der TUI** → Console-Leak (Boot-Progress/Collector-stderr) **wahrscheinlich**, nicht vollständig im Stick-Journal belegt.

### Interne Platten

- Kein Nachweis destruktiver Schreibzugriffe auf SABRENT oder interne MSI-Platten.

---

## Stark wahrscheinlich

### Service-Start ~32 min verzögert

- Frühere Boots (z. B. `20260715_093920_boot`): `auto-msi-evidence.service` startet **~6 s** nach Boot (Journal).
- Dieser Boot (`20260715_113551_boot`): **kein** `Starting auto-msi-evidence` im Boot-Journal; Collect-Evidence erst bei Uptime ~1950 s.
- Vermutliche Ursache: systemd-Abhängigkeit `After=/Wants=setuphelfer-rescue-start-assistant.service` im Lab-Auto-Modus (Start-Assistant inaktiv) oder blockierende Boot-Kette (`media-check`, `network-online`).

### Operator-Abbruch vor Marker-Schreiben

- `lab-auto-result.json` wurde um 12:08 geschrieben.
- `msi-evidence-complete.json` fehlt → Schreibpfad nach Evaluation nicht abgeschlossen (Abbruch, `_collect_ok=0`, oder Schreibfehler).

---

## Nicht belegt

- SABRENT während des Laufs angeschlossen/erkannt.
- Automatischer Shutdown nach Evidence.
- Heartbeat-Failsafe als Abbruchursache.

---

## Zeitachse (rekonstruiert)

| Zeit (UTC) | Ereignis |
|------------|----------|
| 11:35:52 | Boot, Payload 1.10.0.24 |
| ~11:38 | TUI zeigt „MSI-Evidence wird gesammelt“ (Uptime-Gate 150 s) |
| 11:35–12:06 | Collector **nicht** aktiv; TUI-Zeit läuft weiter |
| 12:08:09 | Late-Evidence + Collector-Start (Uptime 1949 s) |
| 12:08:13 | Collector fertig (4 s); Supplement fehlgeschlagen |
| ~12:08+ | Operator-Abbruch; Stick zurück |

---

## Nächste Fixes (001D7)

1. **TUI-Phase** nur bei laufendem `auto-msi-evidence` / Heartbeat-Phase `evidence_collection`, nicht allein nach Uptime.
2. **Service-Unit**: `start-assistant`-Abhängigkeit im Lab-Auto-Modus entfernen oder entkoppeln.
3. **SquashFS**: `ensure_setup_logs_rw` in Payload aufnehmen / Bundle-Import reparieren.
4. **`msi-evidence-complete.json`** auch bei `lab-auto-result passed` schreiben (nicht nur bei `_collect_ok`).
5. **Collector-Dauer-Obergrenze** mit sichtbarem Substatus (Late-Gate vs. Collect vs. Warten auf Service).
6. **Console-Leaks** weiter abschirmen (Boot-Progress, Collector-stderr).

---

## Nicht als Erfolg werten

Dieser Lauf erfüllt **nicht** `physical_rescue_telemetry_diagnostics_e2e_passed`.
