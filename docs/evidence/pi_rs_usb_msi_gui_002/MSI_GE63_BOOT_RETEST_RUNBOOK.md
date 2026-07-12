# MSI GE63 Raider — Boot-Retest Runbook (PI-RS-USB-MSI-GUI-002)

Stand: 2026-07-12  
Payload auf Stick: **1.10.0.15**  
SHA256: `307ae9a381e2792fddd2ca8ebb6c20550544f0b167e2461c323c596651ecd318`

## Testgerät

```text
MSI GE63 Raider RGB 8RF
MS-16P5
```

## Bootparameter (MSI-Compat)

```text
setuphelfer_msi_compat=1
nomodeset
nouveau.modeset=0
pci=noaer
```

## Vor Boot

- [ ] Stick-Version `1.10.0.15` auf SETUPHELFER notiert
- [ ] Payload-SHA256 notiert
- [ ] Kein USB-Update in diesem Lauf (bereits erledigt)
- [ ] Keine produktiven Telemetry Sends

## A. Start und TUI

- [ ] Bootmenü erscheint
- [ ] MSI-Compat-Profil aktiv
- [ ] TUI auf vorgesehenem Terminal
- [ ] Keine Grafikartefakte durch automatischen Terminalwechsel
- [ ] Whiptail vollständig lesbar
- [ ] Tastaturnavigation funktioniert
- [ ] Menü ≥2 Minuten stabil

## B. GUI-Verfügbarkeit (MSI-Compat)

- [ ] GUI-Menüpunkt deaktiviert/ausgeblendet oder klar als nicht verfügbar
- [ ] Operator-Meldung: MSI-Kompatibilitätsmodus → stabile Textoberfläche
- [ ] Kein schwarzer Bildschirm bei GUI-Wunsch
- [ ] TUI wird nach Blockierung sauber neu gerendert

## C. Verbotene GUI-Prozesse

Darf **nicht** durch GUI-Pfad gestartet werden:

```text
openvt
chvt
startx
Xorg
Chromium (Kiosk-GUI-Pfad)
```

## D. TUI-Bedienung

- [ ] Hauptmenü → Informationspunkt (read-only) → zurück
- [ ] Einstellungen/Systeminfo → zurück
- [ ] Keine abgeschnittenen Dialoge
- [ ] Kein eingefrorenes Whiptail
- [ ] Keine unbeabsichtigte Umschaltung auf tty2

## E. Shell (tty2) — separat

Menüpunkt „Shell öffnen (tty2)“ ist **nicht** Teil des GUI-Fixes.  
Fehler hier separat klassifizieren.

## F. Verboten

- Backup / Restore / Partitionierung / Wipe
- Produktiver Telemetrieversand
- Schreiben auf interne NVMe/SATA

## Nach Boot

Evidence nach `docs/evidence/pi_rs_usb_msi_gui_002/msi_boot_retest/` importieren (nur neue Session).
