# MSI Auto-Discovery Failure Analysis — Payload 1.10.0.25

## Session

```text
Session:     20260715_200455_boot
Boot-ID:     88fd4c2f-dc26-42fa-9fc0-900a167c4790
Payload:     1.10.0.25
Boot UTC:    2026-07-15T20:04:32Z
Evidence OK: 2026-07-15T20:07:01Z (Uptime ~156 s)
Operator:    Abbruch bei ~667 s Heartbeat-Alter auf „MSI-Evidence abgeschlossen“
```

## Structured verdict (001D7B)

```text
primary_failure:
  auto_discovery_service_condition_skipped

secondary_failure:
  tui_execstart_path_mismatch

mode_display_failure:
  physical_e2e_text_in_discovery_mode

discovery_started:
  false

destructive_actions_started:
  false

internal_disks_written:
  false
```

## Gesamturteil

```text
failed_rescue_auto_discovery
```

Ursache: Auto-Discovery startete nie. Die TUI hing nach erfolgreicher MSI-Evidence
auf der E2E-Zwischenphase „physischer E2E startet“, ohne Session-State und ohne Heartbeat.

---

## Belegt

### MSI-Evidence diesmal erfolgreich und schnell

```text
lab-auto-result:          passed (uptime 156.4 s)
msi-evidence-complete.json: vorhanden, status=passed
payload_version:          1.10.0.25
rs011d_supplement:        OK (ImportError behoben)
collect Dauer:            ~3–4 s nach Late-Gate
```

Gegenüber 1.10.0.24 (Collect erst nach ~1950 s): Late-Gate + Marker-Fix **bestanden**.

### Auto-Discovery übersprungen

Journal (`20260715_200437_boot/90-journal-boot.txt`):

```text
setuphelfer-rescue-auto-discovery.service ... was skipped
  because no trigger condition checks were met.
```

Unit-Zeile:

```ini
ConditionKernelCommandLine=|setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=1
```

Cmdline enthielt `setuphelfer_msi_lab_auto=1`, aber **nicht** das Literal
`setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=1` als ein Wort.

`setuphelfer_auto_discovery=1` fehlte in der Kernel-Cmdline.

### Keine Discovery-Evidence

```text
SETUP_LOGS/.../evidence/sessions/  → fehlt
```

### Discovery-Run-Control nicht verbraucht

```text
enabled=true
consumed=false
run_mode=auto_discovery_only
```

### Physischer E2E nicht ausgeführt

```text
run-control.json enabled=false
kein neuer e2e-rescue-* Run
kein msi-e2e-auto-result für diesen Boot
```

### TUI-State / Heartbeat

```text
Phase: „MSI-Evidence abgeschlossen — physischer E2E startet“
Heartbeat-Alter: ~667 s (kein Orchestrator-Heartbeat)
```

`refresh_auto_e2e_phase_from_runtime()` setzt diese Phase allein wegen
`msi-evidence-complete.json` — auch wenn Physical-E2E und Discovery fehlen.

### systemd-TUI-Unit übersprungen

```text
setuphelfer-rescue-tui.service skipped:
  ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-tui.sh
```

Installierter Pfad ist `/usr/local/sbin/setuphelfer-rescue-tui` (ohne `.sh`).
TUI war trotzdem sichtbar (vermutlich Entry­point/andere Startkette).

Unit verwies zudem auf:

```ini
ExecStart=/usr/local/sbin/setuphelfer-rescue-entrypoint.sh --boot-trigger
```

Installiert ist `/usr/local/sbin/setuphelfer-rescue-entrypoint` (ohne `.sh`).

### Console-Leaks

Operator: Kommandozeilen unter der TUI — bestätigt (stark wahrscheinlich Boot-Progress/Collector).

### Interne Platten / SABRENT destruktiv

Kein Nachweis destruktiver Aktionen (Discovery fehlte; E2E-Run-Control disabled).

```text
destructive_actions_started: false
internal_disks_written: false
```

---

## Stark wahrscheinlich

1. Physical-E2E hing oder lief ohne Heartbeat, während die TUI fälschlich „E2E startet“ zeigte.
2. Failsafe löste nicht aus, weil die TUI den Auto-E2E-State jede Sekunde aktualisiert (`state_fresh`).

---

## Nicht belegt

- Vollständiger Spät-Journal nach Evidence (Boot-Diagnostik nur Early/Boot ~12 s)
- Exact Exit-Status von auto-physical-e2e

---

## Zeitachse

| Zeit (UTC) | Ereignis |
|------------|----------|
| 20:04:32 | Boot 1.10.0.25, lab_auto + e2e_auto |
| 20:04:39 | auto-discovery **skipped**; auto-msi-evidence startet; tui.service skipped (.sh-Pfad) |
| ~20:04:55 | Session / TUI owned |
| 20:06:56 | Late-Evidence bei Uptime ~152 s |
| 20:06:57–20:07:00 | Collector + Supplement OK |
| 20:07:01 | msi-evidence-complete.json geschrieben |
| ~20:07–20:18 | TUI bleibt auf Evidence-complete, Heartbeat stirbt |
| ~20:18+ | Operator-Abbruch |

---

## Pflichtfixes (001D7B)

1. Discovery-Unit: **kein** kombiniertes ConditionKernelCommandLine-Token; Start über `ExecCondition` + Start-Gate.
2. TUI-Unit: `ConditionPathExists` / Runtime-Pfade ohne `.sh` (`setuphelfer-rescue-tui`, `setuphelfer-rescue-entrypoint`).
3. Bei `discovery-run-control` / `run_mode=auto_discovery_only`: Physical-E2E **nicht** starten; TUI-Phase nicht „physischer E2E startet“.
4. Nach MSI-Evidence: Discovery-Start-Gate + Session + Heartbeat; Run-Control verbrauchen.
5. Boot-Abschlussvalidator: Run-Control enabled aber Discovery nie gestartet → `failed_discovery_service_not_started`.
6. GRUB: `setuphelfer_auto_discovery=1` setzen; Physical-E2E per Run-Mode sperren.

---

## Nicht als Erfolg werten

Dieser Lauf erfüllt **nicht** `rescue_auto_discovery_evidence_complete`.
