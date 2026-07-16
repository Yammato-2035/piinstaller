# MSI Auto-Discovery Failure Analysis — Payload 1.10.0.28

## Session

```text
Session:     20260716_123503_boot
Boot-ID:     e5caa488-9d3f-4a68-b9f9-8361f9e050dc
Payload:     1.10.0.28
MSI Evidence:2026-07-16T12:37:26Z
```

## Klassifikation

```text
guard_fix:
  passed

hold_screen:
  passed

bare_tty_regression:
  resolved

boot_observer_persistence:
  failed

discovery_observability:
  failed

run_control_consumption:
  failed

import_mount_selection:
  failed

import_mode_selection:
  failed
```

## Belegt

```text
- MSI-Evidence passed, payload 1.10.0.28
- Journal: boot-observer.service startete und beendete erfolgreich
- Journal: tui-guard.service startete und beendete erfolgreich (nicht blockierend)
- Late-Evidence: whiptail Discovery-Fehler auf tty1 (Hold sichtbar)
- discovery-boot/<BOOT_ID>/ fehlt auf SETUP_LOGS
- discovery-run-control.json blieb enabled=true, consumed=false
- Dev-Automation wählte leeren Schattenordner /media/volker/SETUP_LOGS
- Echter Stick-Mount später: /media/volker/SETUP_LOGS_STICK (/dev/sdc2)
- Import suchte evidence/e2e/ statt discovery-boot/ und sessions/
```

## Wahrscheinlich

```text
- Boot-Observer schrieb nur unter /run Fallback, weil find_setup_logs_mount()
  keinen gültigen SETUP_LOGS-Mount fand oder einen Schattenpfad akzeptierte
- Gate/Runner/Finalizer teilten denselben fehlerhaften Mountpfad
- esp-rw (/run/setuphelfer/esp-rw) und SETUP_LOGS divergierten
```

## Noch zu testen

```text
- ob Resolver mit kanonischem /run/setuphelfer-rescue/media/SETUP_LOGS
  Bootstrap-Evidence persistent migriert
- ob Run-Control nach terminalem Fehler zuverlässig konsumiert wird
```

## Gesamtstatus

```text
failed_auto_discovery_observability
production_ready=false
```
