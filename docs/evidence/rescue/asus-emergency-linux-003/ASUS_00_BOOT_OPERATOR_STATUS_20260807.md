# ASUS-00 physischer Boot — Operator-Status

Stand: 2026-08-07 (~16:09–16:11 UTC auf dem Stick)

## Ergebnis (kurz)

| Frage | Befund |
|---|---|
| Boot ASUS-00? | ja (`setuphelfer_asus_profile=ASUS-00`) |
| TUI erschienen? | ja — Startassistent Phase `main_menu` |
| GUI? | nein — **erwartet** (ASUS-00: `setuphelfer_mode=text`, `setuphelfer_kiosk=0`; UI-Unit übersprungen) |
| Daten auf Stick? | **ja** — `SETUP_LOGS` / `setuphelfer/diagnostics/` |
| Hardware | ROG Strix G513QM, BIOS G513QM.331 |

## Aufzeichnung

- Pfad: `SETUP_LOGS` → `setuphelfer/diagnostics/`
- Latest: `20260807_161048_boot` (`persistent_to_stick=true`)
- Mehrere Boot-/Early-Snapshots (Timer + vorherige Bootversuche)
- Media-Check: SquashFS-Hash ok (`7431fbe3…`), Medium stabil
- Netzwerk: Ethernet verbunden, Default-Route vorhanden
- Telemetrie-Assistent: `telemetry_ok=false` (kein erfolgreicher Push/ACK in dieser Session)
- Keine failed systemd units in `51-systemd-failed.txt`

## „Kommandozeile zerstört Menü“

ASUS-00-Cmdline **ohne** `quiet`/`loglevel=` → Kernel-/Boot-Meldungen und systemd-Ausgabe
laufen weiter auf tty1 und übermalen Whiptail. Console-Shield existiert, reicht hier
nicht gegen sichtbaren Scrollback.

Empfohlener Folge-Hotfix (nur nach Freigabe): `quiet loglevel=3` in ASUS-Textprofilen
in ESP-`grub.cfg` / Generator.

## GUI-Hinweis

GUI erst bei ASUS-02 / ASUS-05 (`setuphelfer_kiosk=1`) — nicht Teil von ASUS-00.
