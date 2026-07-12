# PI-RS-MSI-RETEST-003 — Operator Boot Runbook

**Stand:** 2026-07-12  
**Payload:** 1.10.0.16  
**SHA256:** `cada647ccc11a545a8b4eb6f42deb8745bdedcd5b1662e738c96d68c987621b5`  
**Testgerät:** MSI GE63 Raider RGB 8RF / MS-16P5  
**Repository:** `main @ 60440cdd`

## Pre-Boot (Entwicklungsrechner — erledigt)

- [x] Stick nach Power-Off neu erkannt (UUIDs 9BB9-A4A6 / 9BC7-3950)
- [x] Payload-SHA256 verifiziert
- [x] Content-Gate + Secret-Gate auf Stick-Payload grün
- [x] Versionsträger konsistent (1.10.0.16)
- [x] SETUP_LOGS Vorher-Inventar (964 Dateien)
- [x] Stick ausgehängt und power-off

Evidence: `docs/evidence/pi_rs_msi_retest_003/`

## Nicht erlaubt

- Kein Backup, Restore, Wipe, Partitionierung, Installation
- Kein USB-Update, kein Payload-Repack
- Kein Telemetrie-Live-Send
- Keine Codeänderung bei Failure
- Keine gefährlichen TUI-Menüpunkte

## Vorbereitung am MSI

1. MSI vollständig herunterfahren.
2. Netzteil anschließen.
3. Alle externen Backup-Datenträger entfernen.
4. **Nur** Setuphelfer-Rettungsstick anschließen.
5. Keine zweite USB-Festplatte, keine SD-Karte.
6. Kamera/Smartphone für Fotos bereithalten.

## Boot — Menüauswahl

**Nicht** den Default „sicherer Textmodus“ wählen (fehlt `pci=noaer`).

**Wählen:** „Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus (Text)“

Erwartete Kernelparameter:

```text
setuphelfer_msi_compat=1
nomodeset
nouveau.modeset=0
pci=noaer
```

## Boot-Checkliste

1. Bootmenü erscheint — **Foto**
2. MSI-Kompatibilitätsprofil gewählt — **Foto**
3. Boot ohne manuellen Zusatzfix
4. **Keine** Meldung „Grafische Oberfläche wird gestartet …“ / kein `x11_starting`
5. Stattdessen sinngemäß: MSI-Kompatibilitätsmodus / Textoberfläche / stabile Textoberfläche

## TUI-Stabilität (≥ 120 Sekunden)

Ab sichtbarer TUI:

1. Startzeit notieren
2. Zwei Minuten **keine** gefährliche Aktion
3. Prüfen: Rahmen vollständig, kein Boot-Progress über Whiptail, Tastatur ok, kein Flackern, kein TTY-Wechsel

**Foto:** erste TUI, Hauptmenü nach 2 Minuten

## Read-only Navigation

1. Hauptmenü
2. Analyse/Systeminformationen öffnen → zurück
3. Einstellungen/Systeminformationen → zurück

Nicht: Backup, Restore, Partitionierung, Installation, Wipe, Telemetrie senden.

## GUI-Sperre

- GUI-Menüpunkt ausgeblendet/deaktiviert **oder** Sperrmeldung:
  „Im MSI-Kompatibilitätsmodus wird die stabile Textoberfläche verwendet …“
- Falls auswählbar: öffnen → Meldung lesen → schließen → TUI erneut bedienen
- **Foto:** Sperrmeldung

Failure: schwarzer Bildschirm, openvt/chvt/startx/Xorg/Chromium, TUI nicht mehr bedienbar.

## Runtime read-only (optional, Shell/Diagnose)

```bash
cat /proc/cmdline
ps -ef | grep -E 'openvt|chvt|startx|Xorg|chromium' | grep -v grep || true
find /run/setuphelfer -maxdepth 5 -type f -print 2>/dev/null | sort
```

Keine schreibenden oder mountenden Befehle auf interne Platten.

## Herunterfahren

Über TUI-Menü „Herunterfahren“. Falls nicht möglich: 30 s warten, dokumentieren, kontrolliert ausschalten.

## Nach dem Test

1. Stick am MSI abziehen
2. Am Entwicklungsrechner einstecken
3. Agent importiert **nur die neue Session** nach `docs/evidence/pi_rs_msi_retest_003/msi_session/`

**Nicht importieren:** `20260712_015835`, `20260712_111206_boot`, ältere Sessions.

## Operator-Dokumentation

Nach dem Test ausfüllen: `docs/evidence/pi_rs_msi_retest_003/OPERATOR_OBSERVATION.md`
