# MSI Auto E2E Failure Analysis — Payload 1.10.0.23

## Session

```text
Session:  20260715_104722_boot
Payload:  1.10.0.23
```

## Failure (belegt)

```text
Failure:  auto_shutdown_failsafe_timeout (420 s)
Physical E2E:  not started
msi-evidence-complete.json:  fehlt
```

## Run-Control (belegt)

```text
enabled=true
consumed=false
one_shot nicht verbraucht — kein erneuter Lauf ohne neues Run-Control
```

## TUI (belegt)

```text
Statische Anzeige auf „MSI-Hardware prüfen“
Blockierendes whiptail --menu ohne periodischen Refresh
Keine sichtbaren Phasenwechsel während MSI-Evidence
```

## Failsafe (belegt)

```text
OnBootSec=420s Timer löste Shutdown aus
Failsafe berücksichtigte Heartbeat/Orchestrator nicht ausreichend
Shutdown vor MSI-Evidence-Abschluss
```

## SETUP_LOGS (belegt)

```text
FAT unclean unmount (Dirty bit)
Kernel: FAT-fs Volume was not properly unmounted
```

## SABRENT (nicht belegt / unbekannt)

```text
Früher Snapshot: SABRENT nicht sichtbar
Destruktive Aktionen: nicht gestartet
Späterer Zustand: unbekannt (Lauf vor Physical E2E beendet)
```

## Internal disks (nicht belegt)

```text
Kein Nachweis von Schreibzugriffen auf interne MSI-Datenträger
```

## Klassifikation

| Befund | Kategorie |
|--------|-----------|
| 420-s Failsafe-Shutdown | **belegt** |
| Statische TUI | **belegt** |
| Fehlender MSI-Evidence-Marker | **belegt** |
| SETUP_LOGS unclean | **belegt** |
| Physical E2E nicht gestartet | **belegt** |
| Run-Control nicht verbraucht | **belegt** |
| SABRENT später erkannt | **nicht belegt** |
| Interne Platten beschrieben | **nicht belegt** |
| MSI-Evidence wäre ohne Failsafe durchgelaufen | **stark wahrscheinlich** (Heartbeat aktiv, aber Timer unabhängig) |

## Nicht als Erfolg übernehmen

Dieser Lauf darf **nicht** als Teilnachweis für `physical_rescue_telemetry_diagnostics_e2e_passed` verwendet werden.
