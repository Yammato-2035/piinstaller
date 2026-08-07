# ASUS-02 Handover — Abschlussbericht (kein Fake-Green)

**Stand:** 2026-08-07 ~19:30 UTC+2  
**Zweck:** Übergabe an ChatGPT / Folgesession — ehrlicher Status, keine „behoben“-Behauptung ohne physischen Beweis.  
**Maschinenlesbar:** `ASUS_02_HANDOVER_SUMMARY.json`

---

## 1. Verdict (verbindlich)

| Feld | Wert |
|---|---|
| **Gesamt** | **NICHT produktionsreif** |
| **ASUS-02 GUI** | **FAIL** — nie physisch grün gewesen |
| **ASUS-02 TUI** | **STARTET**, aber **optisch degradiert** (Konsolen-/Service-Spam) |
| **Fake-Green** | **verboten / nicht behauptet** |
| **production_ready** | `false` |

Operator (diese Session): *keine GUI, wieder TUI, Services zerstören Textmenü.*  
Daten auf Stick bestätigen das.

---

## 2. Kontext / Artefakte

| Item | Wert |
|---|---|
| Workspace | `/home/volker/piinstaller-asus-emergency-linux-telemetry-003` |
| Branch | `pi-rs-asus-emergency-linux-telemetry-003` |
| Git HEAD | `b425097ba06b8a889ab95a2feb1ebcf5525ff7fa` |
| project_version | `1.10.2.0` |
| Stick | Intenso Ultra Line `/dev/sda`, Serial `24111412110212`, Fingerprint `ce2e34b7f5ea4e41` |
| Labels | `SETUPHELFER` + `SETUP_LOGS` |
| Letzter Payload auf Stick | SHA256 `a68baa316413e66bbb56602536f0cf268249c98993d437ca07f2a6a44b692fcd` |
| Letzter Boot | Stamp `20260807_192914`, Profil **ASUS-02** |
| Gerät | ASUS ROG Strix G513QM, BIOS G513QM.331, Ryzen 9 5900HX, AMD Cezanne + RTX 3060 (NVIDIA blacklisted) |

Evidence-Ordner: `docs/evidence/rescue/asus-emergency-linux-003/`  
Letzter Boot-Snapshot: `asus02_boot_20260807_192914/`

---

## 3. Was physisch bestätigt ist (km/h)

| Profil | Ergebnis | Beleg |
|---|---|---|
| **ASUS-00** | Baseline OK (TUI, Capture, Ethernet); Display/KMS absichtlich aus (`nomodeset`) | frühere Findings |
| **ASUS-01** | **Pass** — `amdgpu` + eDP connected | `ASUS_01_HARDWARE_FINDINGS_KM_H.*` |
| **ASUS-02** | **GUI FAIL** über mehrere Payload-Iterationen | siehe §5 |

Hardware für GUI (ASUS-02): DRM **OK** — `amdgpudrmfb`, **eDP-1 connected**. Das ist **kein** „Panel tot“-Problem.

---

## 4. Fix-Iteration (ehrlich: Teilfortschritt ≠ behoben)

Jede Iteration wurde auf den Stick geschrieben (FAT32 ESP Payload-Update, Operator-Doppelbestätigung).  
**Kein** Full-USB-Rewrite in den letzten Schritten.

| Payload SHA (kurz) | Ziel des Fixes | Ergebnis physisch |
|---|---|---|
| … frühere | `setuphelfer_start_assistant=1`, UI-Unit-Gate, tty1-SIGHUP | TUI teilweise nutzbar; GUI weiter kaputt |
| `55a144ae…` | tty1-Owner / UI nicht stormen | GUI: `openvt_console_2_not_released` |
| `6635ff89…` | getty@tty2 freigeben vor openvt | Fix **lief** (`VT_RELEASE`), aber `systemctl mask --runtime` → **systemd Reloading** riss Kette ab; GUI weiter fail; TUI mit Spam |
| `a68baa31…` (**aktuell auf Stick**) | kein mask; **startx VT7** statt openvt/VT2; Console-quiet nach Fail | Fix **lief** (`kiosk_vt=7`, `STARTX_VT_EXEC`, `stop_no_mask`); GUI: **`startx_not_started`**; TUI wieder da, **weiter Spam** |

### Wichtige Meta-Lehre

„Code/Patch auf Stick + Logmarker vom neuen Pfad“ bedeutet nur: *der neue Code wurde ausgeführt*.  
Es bedeutet **nicht**: GUI funktioniert / TUI ist sauber.  
Frühere Formulierungen in der Session waren zu optimistisch („behoben“) — **dieser Bericht korrigiert das**.

---

## 5. Letzter Boot `20260807_192914` — Fakten

### 5.1 GUI

- Cmdline: `setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 setuphelfer_asus_profile=ASUS-02`
- `gui-watchdog.json`: `gui_started=false`, **`gui_error_code=startx_not_started`**
- `gui-start.log`: VT7, `STARTX_VT_EXEC`, Kiosk-PID exit nach **~4 s**
- **Kein** `/tmp/.X11-unix`-Socket, **kein** brauchbares `Xorg.0.log` in Forensik
- Sehr früh (vor Watchdog): Chromium `Missing X server or $DISPLAY`
- Parallel: `OSError: Address already in use` (HTTP-Server / UI-Port-Kollision)
- Backend während GUI-Kette: `/api/version` → **HTTP 503** (uvicorn läuft, App nicht ready)
- `setuphelfer-rescue-ui.service`: disabled/inactive (korrekt nach früherem Fix)

### 5.2 TUI / Console-Zerstörung

- TUI-Prozess auf tty1: `setuphelfer-rescue-tui --boot-trigger`
- Fallback-Marker: `tui_rerendered_after_gui_failure=true`
- **Console-Ownership** im Snapshot: weiterhin `lifecycle_state=gui_transition`, Owner `gui` — Restore auf `tui_owned` greift nicht zuverlässig / zu spät
- `boot_state.text_mode_started=false` trotz laufender TUI (State-Lüge / veralteter State)
- Viele Auto-Services unter `multi-user.target.wants`, u. a.:
  - `setuphelfer-rescue-boot-diagnostics.service` + **Timer** (Snapshots ~alle 15 s während Boot)
  - `setuphelfer-rescue-boot-logs.service`
  - `setuphelfer-backend.service`, `setuphelfer.service` (Web-UI :3001)
  - Sentinels, telemetry-spooler, task-pull, autocapture-finalizer, …
- Kernel: `Console: switching to colour frame buffer device` (fbcon) — konkurriert mit Text-UI
- Operator sieht: Kommandzeilen-/Service-Meldungen **übermalen** das Whiptail-Menü

### 5.3 Was am letzten Fix *technisch* fortgeschritten ist

- openvt/VT2/getty-mask-Pfad ist **nicht mehr** der aktuelle Fehlercode
- Fehler hat sich verschoben zu: **X/startx startet nicht** (`startx_not_started`)
- Das ist Fortschritt in der Diagnose, **kein** Produkterfolg

---

## 6. Offene Root-Cause-Hypothesen (priorisiert für Folgesession)

1. **Xorg/startx bricht sofort ab** ohne Log — prüfen: xinitrc fehlt/kaputt, Rechte auf VT7, amdgpu DRI, `startx` Exitcode, absichtlich `Xorg.0.log` nach `/run/setuphelfer/` umleiten und spiegeln.
2. **Frühstart Chromium/UI ohne Display** + Port-Konflikt — wer startet Browser/HTTP vor der GUI-Kette? (`setuphelfer.service` :3001 vs Rescue-UI :8765).
3. **Backend 503** — GUI-Health wartet auf `/api/version`; Async-Backend-Start unzureichend; ggf. Health von Backend entkoppeln bis X steht.
4. **Console-Ownership / Multi-Writer auf tty1** — solange GUI-Versuch läuft und viele Units journaln/fbcon switchen, ist TUI nicht „owned“. Braucht: **ein** Owner, Diagnostics **nicht** auf Console, Timer nach TUI pausieren, `dmesg --console-off` + printk hart, kein paralleler GUI-Watchdog-Output auf tty1.
5. **Architektur:** ASUS-02 bootet mit `mode=gui` → Watchdog **vor** stabiler TUI → Fail → TUI unter Trümmern. Besser: **TUI first**, GUI nur explizit / nach Idle, oder GUI auf separatem VT ohne tty1-Schreiben.

---

## 7. Empfohlene nächste Arbeit (strikt, klein)

**Nicht** weitere „ein Patch und fertig“-Claims. Stattdessen:

### A) TUI-Stabilität zuerst (Operator-Schmerz #1)

1. Bei `setuphelfer_start_assistant=1`: **kein** automatischer GUI-Watchdog am Boot **oder** GUI erst nach erfolgreicher TUI-Owner-Transition.
2. `setuphelfer-rescue-boot-diagnostics.timer` während interaktiver TUI **stoppen**/maskenlos disable.
3. Alle Rescue-Units: `StandardOutput=journal` / kein tty1; Console-Shield erzwingen bevor Whiptail.
4. Nach GUI-Fail: Ownership **zwingend** `tui_owned`, Screen clear, Whiptail neu — physisch verifizieren.

### B) GUI-Diagnose (separater Track)

1. `startx`/`Xorg` mit explizitem Log-Pfad + Exitcode in `gui-start.log`.
2. Ein Boot nur mit manuellem `startx` auf VT7 (Shell), Evidence sammeln.
3. Port/Chromium-Frühstart eliminieren bevor Watchdog läuft.

### C) Gates

- `asus_boot_passed` / GUI-grün **nur** nach Operator-Sicht + Evidence (`gui_started=true`, X-Socket, sichtbares Menü).
- USB-Write weiter nur mit Doppelbestätigung; keine NVMe-Writes.

---

## 8. Dateien für die Folgesession

| Datei | Inhalt |
|---|---|
| `ASUS_02_HANDOVER_SUMMARY.json` | Maschinen-Verdict |
| `ASUS_02_HANDOVER_ABSCHLUSSBERICHT.md` | dieser Bericht |
| `asus02_boot_20260807_192914/` | Evidence letzter Fail |
| `ASUS_02_BOOT_185015_DATA_REVIEW.md` | vorheriger Fail (openvt/mask) |
| `ASUS_02_OPENVT_VT2_FIX.md` / `ASUS_02_COLLECTED_DATA_AND_GUI_FAIL.md` | Historie |
| `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260807_191929/` | letztes erfolgreiches Stick-Update |
| Live-Skripte | `scripts/rescue-live/image/setuphelfer-rescue-{common,gui-watchdog,kiosk-start,entrypoint,tui,x11-early}*` |

---

## 9. Kurztext zum Einfügen in ChatGPT

```
Handover PI-RS ASUS G513QM / ASUS-02 (2026-08-07).

VERDICT: NICHT produktionsreif. GUI auf ASUS-02 nie physisch grün.
Letzter Stick-Payload a68baa31… (startx VT7). Boot 20260807_192914:
gui_error=startx_not_started (Kiosk ~4s tot, kein X-Socket/Xorg-Log).
TUI startet, aber Console/Services zerstören Whiptail optisch.
Ownership bleibt gui_transition; boot-diagnostics-Timer ~15s;
früh Chromium ohne DISPLAY; UI-Port already in use; backend /api/version 503.
ASUS-01 DRM/amdgpu war pass; ASUS-02 Panel DRM OK — Problem ist Software-Startkette.
Workspace: /home/volker/piinstaller-asus-emergency-linux-telemetry-003
Branch pi-rs-asus-emergency-linux-telemetry-003 @ b425097b
Bericht: docs/evidence/rescue/asus-emergency-linux-003/ASUS_02_HANDOVER_ABSCHLUSSBERICHT.md
Nächster Fokus: (1) TUI-only-Boot ohne GUI-Autostart + Console-Shield,
(2) startx/Xorg Exitcode+Log, (3) Port/Chromium-Frühstart killen.
Kein Fake-Green. USB nur mit Operator-Doppelbestätigung.
```

---

**Ende Abschlussbericht.** ASUS-02 bleibt **FAIL** bis physischer Gegenbeweis.
