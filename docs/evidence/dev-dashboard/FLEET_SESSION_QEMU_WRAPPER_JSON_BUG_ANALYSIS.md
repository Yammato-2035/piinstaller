# Fleet Session QEMU Wrapper — JSON Payload Bug Analysis

**Datum:** 2026-06-01  
**HEAD (Analyse):** `8ed0ff5`

## Betroffener Lauf

| Feld | Wert |
|------|------|
| **run_id** | `qemu_rescue_developer_autopilot_20260601_080405` |
| **session_id** | `fleet-qemu_rescue_developer_autopilot_20260601_080405` |
| **QEMU-Prozess** | lief weiter (nicht beendet durch diesen Fix) |

## Fehlerbild

```
NameError: name 'true' is not defined. Did you mean: 'True'?
SyntaxError: ... 'path':''/home/.../qemu-serial.log'','exists':true ...
```

## Ursache

**Datei:** `scripts/rescue-live/run-qemu-developer-iso-smoke.sh`  
**Funktion:** `_fleet_serial_patch_json()` (entfernt im Fix)

Shell baute Python-Code per String zusammen:

```bash
python3 -c "import json; print(json.dumps({'serial':{'path':''${SERIAL_LOG}'','exists':${exists},'size_bytes':${size}}, ...}))"
```

Probleme:

1. Bash-Variable `exists=true` wurde als Python-Identifier `true` eingefügt → **NameError** (Python braucht `True`).
2. Pfad `''${SERIAL_LOG}''` erzeugte **kaputte Quotes** im Python-Literal.
3. Gleiches Muster bei `qemu_starting` / `booting` Heartbeats mit `${HAS_KVM}`.

Zusätzlich: `scripts/rescue-live/fleet-session-api.sh` Fallback mit `json.loads('''${payload}''')` — brüchig bei Sonderzeichen.

## Fachliche Bewertung

Der Lauf `080405` wird **nicht** als Boot-Failure gewertet:

- Fleet-Telemetrie brach nach erstem Heartbeat-Fehler ab (`pid` blieb `null`, `kvm_enabled` nicht gesetzt).
- Session zeigt `timeout_warning` / verzögerten Heartbeat ohne QEMU-Metriken.
- QEMU selbst lief mit KVM; Serial/Ergebnis ohne Wrapper-Fix nicht belastbar.

## Fix-Richtung

- Alle Payloads über **Python-Heredoc + ENV** (`fleet-session-api.sh`).
- `fleet_validate_json` vor jedem `curl`.
- Proxy: Default `127.0.0.1`; QEMU-Smoke setzt `0.0.0.0` nur mit `OPERATOR_CONFIRM_LAN_BIND=true`.
