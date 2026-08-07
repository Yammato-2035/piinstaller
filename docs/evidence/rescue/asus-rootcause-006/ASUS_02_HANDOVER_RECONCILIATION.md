# ASUS_02 Handover Reconciliation — PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006

Quellen:

- `docs/evidence/rescue/asus-emergency-linux-003/ASUS_02_HANDOVER_ABSCHLUSSBERICHT.md`
- `docs/evidence/rescue/asus-emergency-linux-003/ASUS_02_HANDOVER_SUMMARY.json`
- Boot-Snapshot `asus02_boot_20260807_192914/`

## Alter Fehler (überwunden als *aktueller* Primärcode)

| Code | Bedeutung |
|---|---|
| `openvt_console_2_not_released` | getty@tty2 / openvt VT2; später mask→systemd Reloading |

Nicht mehr der führende Fehlercode auf Payload `a68baa31…`.

## Neuer Fehler (aktuell)

| Code | Bedeutung |
|---|---|
| **`startx_not_started`** | VT7/`STARTX_VT_EXEC` erreicht; Kiosk ~4 s tot; **kein** X-Socket; **kein** brauchbares Xorg-Log |

Primäre Kausalkette (Hypothese, unbewiesen bis Forensic-Wrapper):

```
TUI/entrypoint → gui_transition → VT7 → startx-Aufruf → (Xorg fehlt/bricht) → kein Socket
```

## Bestätigte Verbesserung

- Payload-Hash auf Stick stimmte mit Staging überein.
- Neuer Codepfad lief: `kiosk_vt=7`, `STARTX_VT_EXEC`, `stop_no_mask`.
- DRM/Panel weiter OK (`amdgpudrmfb`, eDP-1 connected) — kein „Panel tot“.
- `setuphelfer-rescue-ui.service` disabled (kein tty1-Storm mehr).
- Fehler isoliert sich Richtung **startx/Xorg-Start**, nicht Chromium-Rendering.

## Weiterhin offene Ursache

1. Warum startx/Xorg keinen Socket und kein Log erzeugt (Exitcode bisher nicht forensisch erfasst).
2. Chromium-Frühstart ohne DISPLAY.
3. UI-Port `Address already in use`.
4. Backend `/api/version` → 503 während GUI-Kette (`backend_not_ready_yet` vs echt fail).
5. Console Ownership bleibt `gui_transition` statt `tui_owned`.
6. Diagnostics-Timer (~15 s) + fbcon stören sichtbares TUI.

## Konkurrierende Fehler (nicht vermischen)

| Symptom | Track |
|---|---|
| startx_not_started | XORG-FORENSIC |
| Chromium ohne DISPLAY | Browser-Gate |
| Port already in use | Port-Ownership |
| Backend 503 | Backend-Readiness |
| TUI optisch kaputt | Console-Shield + Timer-Isolation |

## Fehlende Evidence (Pflicht für nächsten Lauf)

- `STARTX_EXIT_CODE`
- `STARTX_STDOUT` / `STARTX_STDERR`
- erzwungenes Xorg-Log (Pfad + warum fehlend)
- X-Socket Zeitstempel relativ zu startx
- Port-Owner PID/Unit für 8000/8765/3001
- Backend-Stage-Marker (`process` / `socket` / `health` / `api`)
- Console owner nach TUI-ready = `tui_owned`

## Nächste kausale Variable

**Nicht GUI.** Nächster physischer Test:

1. **ASUS-TUI-BASELINE** (2×) — kein startx, kein Chromium, saubere TUI.
2. Erst danach **ASUS-XORG-FORENSIC** — nur startx→Xorg→Socket, kein Chromium.

Endzustand dieser Reconciliation: `insufficient_evidence` für startx-Rootcause;  
`asus_tui_baseline_stable` noch **nicht** erreicht.
