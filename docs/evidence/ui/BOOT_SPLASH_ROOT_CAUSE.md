# Boot-Splash Root Cause — Setuphelfer Rettungsstick

**Datum:** 2026-06-24  
**Version:** `1.9.16.1` (`config/version.json`)  
**Scope:** Analyse + Fix (kein Live-MSI-Boot in dieser Session)

## Symptom

Beim Boot erscheint neben dem erwarteten Text *„Setuphelfer Rettungsstick – Rettungsumgebung wird vorbereitet“* Textfragmente, Steuerzeichen oder unsaubere Konsolenausgabe.

## Ist-Stand (Phase 0)

| Bereich | Stand |
|--------|--------|
| Version | `1.9.16.1` |
| Letzter MSI-Nachweis | P3S GE63 Boot 2026-06-21 (`docs/evidence/runtime-results/rescue/p3s_msi_boot_20260621/`) |
| React-Splash | `frontend/src/rescue/RescueBootSplash.tsx` + `i18n/de.json` (`boot.cardTitle`, `boot.cardSubtitle`, `boot.steps.*`) |
| X11-Hold (pre-Chromium) | `scripts/rescue-live/image/setuphelfer-rescue-x11-hold` |
| GUI-Kette | `setuphelfer-rescue-x11-early.sh` → `setuphelfer-rescue-gui-watchdog.sh` → `setuphelfer-rescue-ui-launch` |

## Root-Cause-Tabelle

| Quelle | Befund |
|--------|--------|
| **Framebuffer TTY1 (`chvt 1`)** | `setuphelfer-rescue-gui-watchdog.sh` schaltete vor Kiosk-Start auf TTY1. Dort laufen Kernel-/systemd-/Journal-Meldungen (`loglevel=7`, PCIe AER, nouveau, FAT-fs) sichtbar neben dem Splash-Zeitraum. |
| **x11-hold (pre-React)** | Box-Drawing-Zeichen (`╔═╗`) und xterm-Fallback mit inline-`printf`/`sh -c`-Quoting → bei falscher Font/VT unsaubere Fragmente und Escape-Sequenzen. |
| **React `RescueBootSplash`** | **Sauber** — nur i18n-Strings, keine API-/Journal-Texte. Nicht Ursache der Steuerzeichen. |
| **systemd stdout** | Boot-Logs auf Konsole, nicht in React eingebettet; sichtbar wegen TTY1-Fokus. |
| **Journal/ANSI** | Kernel/systemd nutzen ANSI-Farben; auf Framebuffer ohne Clear erscheinen als Steuerzeichen-Müll. |

## Fix (Phase 2)

1. **`setuphelfer_rescue_blank_fb_tty`** in `setuphelfer-rescue-common.sh` — leert Framebuffer-TTY, Cursor aus.
2. **`setuphelfer-rescue-gui-watchdog.sh`** — kein `chvt 1` mehr beim GUI-Start; TTY1 wird geblankt, Fokus direkt auf Kiosk-VT (`SETUPHELFER_RESCUE_KIOSK_VT=2`).
3. **`setuphelfer-rescue-x11-early.sh`** — nach X11-Ready: TTY1 blanken + `chvt` auf Kiosk-VT.
4. **`setuphelfer-rescue-x11-hold`** — nur Klartext (keine Box-Drawing-Zeichen), zenity/xmessage/xterm mit `-file`, optional `feh` für Logo auf schwarzem Hintergrund.
5. **React-Splash** — vier saubere Fortschrittszeilen: Datenträger / Netzwerk / Dienste / Oberfläche (`RescueBootSplash.tsx`, `i18n/de.json`).

## Nachweis

| Prüfung | Ergebnis |
|---------|----------|
| `pytest backend/tests/test_rescue_p3v3_contract_v1.py` | **GRÜN** (Splash-Contract inkl. x11-hold-Text) |
| Live-MSI-Boot GE63 | **UNBESTÄTIGT** — Dev-Host, kein Rettungsstick-Boot in dieser Session |

## Geänderte Dateien

- `scripts/rescue-live/image/setuphelfer-rescue-common.sh`
- `scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh`
- `scripts/rescue-live/image/setuphelfer-rescue-x11-early.sh`
- `scripts/rescue-live/image/setuphelfer-rescue-x11-hold`
- `frontend/src/rescue/RescueBootSplash.tsx`
- `frontend/src/rescue/i18n/de.json`
- `backend/tests/test_rescue_p3v3_contract_v1.py`

## Status

**GELB** — Fix implementiert und Unit-Contract grün; Live-Boot auf MSI-Hardware noch offen.
