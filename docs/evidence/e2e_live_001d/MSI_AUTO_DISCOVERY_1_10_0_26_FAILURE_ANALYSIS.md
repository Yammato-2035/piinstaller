# MSI Auto-Discovery Failure Analysis — Payload 1.10.0.26

## Session

```text
Session:     20260715_213638_boot
Boot-ID:     9f573ac5-281a-4cb8-a130-1335fd470875
Payload:     1.10.0.26
Boot UTC:    ~2026-07-15T21:36:29Z
MSI Evidence:2026-07-15T21:39:03Z (uptime ~159 s)
Operator:    TUI beendet → nur noch Kommandozeile; Stick zurück nach Failsafe
```

## Structured verdict (001D7B retest)

```text
primary_failure:
  discovery_session_never_persisted

secondary_failure:
  tui_exited_to_bare_console

mode_display_failure:
  inconclusive_late_journal_missing

discovery_started:
  false   # no SETUP_LOGS/.../evidence/sessions/

destructive_actions_started:
  false

internal_disks_written:
  false

run_control_consumed:
  false   # still enabled after boot
```

## Gesamturteil

```text
failed_auto_discovery_service_skipped
  (oder: discovery lief, aber Evidence nur in /run Fallback — nicht nachweisbar)
```

Zusätzlich sichtbar:

```text
failed_tui_runtime_path   # diesmal NEIN (Unit startete)
failed_run_control_not_consumed
```

Produktion: `production_ready=false`

---

## confirmed (001D7C)

```text
confirmed:
- TUI-Display-Prozess endete
- TUI-Service beendete sich danach erfolgreich (exit 0 nach _tui_auto_e2e_menu)
- tty1 hatte danach keinen Halteprozess
- Discovery-Session fehlt (keine evidence/sessions/)
- Run-Control blieb aktiv (enabled=true, consumed=false)
- MSI-Evidence passed
- TUI-Unit startete (kein .sh-Pfad-Skip)
- Physical-E2E nicht gestartet
- Shutdown via Failsafe-Timeout
```

## unknown (001D7C — Beobachtungslücke)

```text
unknown:
- Discovery-Service startete oder nicht
- Discovery-Prozess-Exitcode
- Python-Exception / Stacktrace
- Start-Gate-Ausgabe / Exitcode
- ConditionResult / ExecMainStatus der Discovery-Unit nach MSI-Evidence
```

Genau diese Lücke schließt 001D7C (Start-Gate-Audit, Runner-Exit, Spät-Journal, TUI-Halt).

---

## Belegt — was diesmal besser war als 1.10.0.25

### Payload / GRUB

```text
cmdline enthält:
  setuphelfer_msi_lab_auto=1
  setuphelfer_auto_discovery=1
  setuphelfer_msi_e2e_auto=0
  setuphelfer_auto_shutdown=1
  setuphelfer_msi_lab_late_sec=120

api-version / collector: 1.10.0.26
```

### TUI-Unit startete

```text
journal @ 21:36:36:
  Started setuphelfer-rescue-tui.service
```

Kein `ConditionPathExists=...tui.sh`-Skip mehr.

### MSI-Evidence erneut bestanden

```text
msi-evidence-complete.json: status=passed
late_gate_completed: true
lab-auto-result: passed (uptime 159.5 s)
console_owner: tui
```

### Physical E2E

```text
kein neuer e2e-rescue-* Run
run-control.json physical weiterhin disabled
```

---

## Belegt — was weiterhin fehlschlägt

### Keine Discovery-Session

```text
SETUP_LOGS/.../evidence/sessions/  → fehlt komplett
```

### Discovery-Run-Control nicht verbraucht

```text
enabled=true
consumed=false
expected_payload_version=1.10.0.26
run_nonce=187880e1300dbb3dc2076eccf89ad888
```

Boot-Abschlussvalidator / Failsafe hat das Control **nicht** konsumiert
(trotz `auto_shutdown_failsafe_timeout` in `boot_state_redacted.json`).

### TUI → nackte Kommandozeile

Operator-Beobachtung:

```text
TUI beendet, nur noch Kommandozeile
```

Codepfad (`setuphelfer-rescue-tui.sh`):

```bash
_tui_auto_e2e_menu   # display.py läuft
exit 0                 # Service beendet → tty1 ohne Ersatz-Owner
```

Sobald `setuphelfer-rescue-auto-e2e-tui-display.py` endet oder abstürzt,
endet die TUI-Unit sofort. Es gibt kein Fallback-Menü und keinen getty auf tty1.

### Spät-Journal fehlt

Boot-Diagnostik wurde bei Uptime **~10 s** geschrieben:

```text
stamp_utc=20260715_213634
uptime=10.59
```

Darin sichtbar:

- TUI startet
- auto-msi-evidence **startet**

Nicht sichtbar (weil zu früh):

- Ende von MSI-Evidence
- ExecCondition / Start von auto-discovery
- Abbruchgründe der TUI-Display-Schleife

---

## Stark wahrscheinlich

1. **Discovery-Service lieferte keine persistierte Session**  
   Entweder ExecCondition/Start blieb aus, oder der Orchestrator brach ab,
   bevor `00-session.json` auf SETUP_LOGS lag (Fallback nur unter `/run` wäre nach Shutdown weg).

2. **TUI-Display beendete die Auto-Schleife**  
   Danach `exit 0` der TUI-Unit → sichtbare Kommandozeile / Shell-Reste.

3. **Failsafe/Watchdog** (`OnBootSec=300s`, danach 60s) fuhr nach tot/stillem Heartbeat
   herunter (`phase=auto_shutdown_failsafe_timeout`), ohne Run-Control zu konsumieren.

---

## Nicht belegt

- Exact `systemctl status setuphelfer-rescue-auto-discovery` nach MSI-Evidence
- Exit-Code von `setuphelfer-rescue-auto-discovery-start-gate`
- Python-Traceback der TUI-Display-Schleife
- Ob `/run/setuphelfer-rescue/fallback-evidence/` jemals existierte

---

## Zeitachse

| Zeit (UTC) | Ereignis |
|------------|----------|
| 21:36:29 | Boot 1.10.0.26, Lab-Auto + Auto-Discovery, e2e_auto=0 |
| 21:36:36 | TUI started; auto-msi-evidence starting |
| ~21:36:39 | console owner = tui |
| 21:38:58 | Late-Evidence (uptime ~155 s) |
| 21:39:02–03 | Collectors + msi-evidence-complete |
| danach | keine Discovery-Session; TUI endet → Kommandozeile |
| später | Failsafe-Timeout-Shutdown |

---

## Pflichtfixes für nächsten Lauf (001D7C)

1. **Spät-Journal / Service-Status nach MSI-Evidence und Discovery** auf SETUP_LOGS schreiben  
   (nicht nur Early-Boot bei 10 s).
2. **TUI darf nach Exit der Auto-Display-Schleife nicht nackt enden**  
   → Display neu starten oder Halte-Screen „Warte auf Discovery / Fehler“ bis Shutdown.
3. **Discovery-Start und Orchestrator hart instrumentieren**  
   (`auto-discovery.started`, Gate-Result, Log auf SETUP_LOGS).
4. **Failsafe muss Discovery-Run-Control immer konsumieren**, wenn enabled und keine Session.
5. Import-Pfad: Host-Mount `SETUP_LOGS2` korrekt erkennen (nicht leeres `/media/volker/SETUP_LOGS`).

---

## Nicht als Erfolg werten

Dieser Lauf erfüllt **nicht** `rescue_auto_discovery_evidence_complete`.
