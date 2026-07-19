# MSI Auto-Discovery Failure Analysis — Payload 1.10.0.27

## Session

```text
Session:     20260716_101029_boot
Boot-ID:     bd1ca170-77a7-4517-ac55-502c91c0838e
Payload:     1.10.0.27
MSI Evidence:2026-07-16T10:12:54Z
Operator:    TUI verschwand; setuphelfer-rescue-tui-guard.service/start lief minutenlang
```

## Gesamturteil

```text
failed_bare_tty_regression
```

Discovery war auch diesmal **nicht ausreichend beobachtbar**:

```text
failed_auto_discovery_observability
```

Die haertere Statusentscheidung ist hier jedoch die TTY/TUI-Regression, weil
die Guard-Reparatur selbst den Bildschirmverlust nicht verhindert hat.

## Belegt

```text
confirmed:
- Payload 1.10.0.27 bootete mit
  setuphelfer_msi_lab_auto=1
  setuphelfer_auto_discovery=1
  setuphelfer_msi_e2e_auto=0
  setuphelfer_auto_shutdown=1
- msi-evidence-complete.json wurde geschrieben
- lab-auto-result.json: passed
- collector/api-version: 1.10.0.27
- console owner war waehrend MSI-Evidence auf tty1 = tui
- boot_state_redacted.json endete in auto_shutdown_failsafe_observability_timeout
- discovery-run-control.json blieb enabled=true, consumed=false
- kein discovery-boot/<BOOT_ID> Verzeichnis auf SETUP_LOGS
- keine evidence/sessions/ fuer diesen Lauf
```

## Nicht belegt

```text
unknown:
- ob das Discovery-Start-Gate aufgerufen wurde
- ob der Discovery-Service jemals startete
- ob der Orchestrator sofort abstuerzte
- welcher Exitcode/Fehlercode vorlag
- ob spaetes Journal / service-status-late geschrieben werden sollte, aber nicht wurde
- exakte guard_restart_count auf dem Zielsystem
```

## Relevante Artefakte

```text
SETUP_LOGS2:
- setuphelfer/evidence/msi-rs011b/msi-evidence-complete.json
- setuphelfer/evidence/msi-rs011b/lab-auto-result.json
- setuphelfer/evidence/msi-rs011b/late-evidence-auto-20260716_101249.txt
- setuphelfer/diagnostics/20260716_101025_boot/*
- setuphelfer/e2e-live-001d/discovery-run-control.json
- setuphelfer/evidence/boot/boot_state_redacted.json
```

Es fehlen weiterhin alle 001D7C-Pflichtartefakte:

```text
missing:
- 00-start-gate.json
- 01-service-start.json
- 02-orchestrator-exit.json
- 03-service-result.json
- late-journal.redacted.log
- service-status-late.json
- boot-finalizer.json
```

## Root Cause dieser 1.10.0.27-Regressionsstufe

Der TUI-Guard war als `oneshot` ohne TTY konfiguriert, konnte aber in einen
blockierenden Hold-Pfad laufen. Damit blieb der systemd-Job sichtbar auf
`setuphelfer-rescue-tui-guard.service/start running`, ohne dass tty1 wieder von
einer TUI uebernommen wurde.

Das erklaert die Operator-Beobachtung:

```text
TUI weg
guard.service/start laeuft minutenlang
watchdog startet mehrfach
TUI kommt nicht zurueck
```

## Statusentscheidung

```text
primary_failure:
  tui_guard_inline_hold_blocked

secondary_failure:
  discovery_observability_absent

terminal_shutdown:
  failsafe_observability_timeout

discovery_started:
  not_proven

run_control_consumed:
  false

internal_disks_written:
  false

sabrent_written:
  false

Gesamtstatus:
  failed_bare_tty_regression

Nebenstatus:
  failed_auto_discovery_observability

production_ready:
  false
```

## Klassifikation

```text
belegt:
- MSI-Evidence passed
- Run-Control enabled=true, consumed=false
- boot_state: auto_shutdown_failsafe_observability_timeout
- fehlende discovery-boot Evidence

Operator-Beobachtung:
- TUI verschwand
- guard.service/start lief minutenlang
- tty1 leer/schwarz

stark wahrscheinlich:
- Guard blockierte durch inline Hold ohne TTY

nicht belegt:
- Start-Gate-Audit
- Discovery-Service-Start
- Orchestrator-Exit
- Spät-Journal / Boot-Finalizer
```

## Naechster Fix

```text
1. Guard niemals blockierend laufen lassen
2. Hold-Screen als eigene tty1-Unit starten
3. Payload 1.10.0.28 bauen und auf Stick aktualisieren
4. physisch erneut booten
5. danach gezielt pruefen, ob discovery-boot/<BOOT_ID>/ erstmals entsteht
```
