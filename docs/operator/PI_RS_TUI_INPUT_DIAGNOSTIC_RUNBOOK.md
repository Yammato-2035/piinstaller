# Operator-Runbook: TUI-Eingabediagnose

## Voraussetzungen

- Stick mit Payload ≥ 1.10.0.60 (Diagnose + Evidence-Persistenz)
- MSI GE63 oder anderes Testgerät
- Optional: externe USB-Tastatur
- Kein Backup/Restore/Partitionieren

## Ablauf

1. Stick booten, GRUB öffnen.
2. Eintrag wählen: **Setuphelfer – TUI-Eingabediagnose (read-only)**  
   (nicht den Standard-GUI-/Text-Eintrag).
3. tty1 zeigt das normale Textmenü (ggf. unbedienbar).
4. tty2 startet den Diagnoseassistenten (Ctrl+Alt+F2 falls nötig).
5. Assistenten-Anweisungen folgen (interne Tasten, ggf. externe Tastatur).
6. Am Ende Status prüfen:
   - Laufdaten temporär erfasst: ja
   - SETUP_LOGS gefunden: ja/nein
   - Persistente Speicherung: wartet | kopiert | prüft | abgeschlossen | fehlgeschlagen
   - Herunterfahren erlaubt: ja/nein
7. Erst herunterfahren, wenn „Evidence dauerhaft gespeichert“ und Herunterfahren freigegeben.
8. Stick in den Dev-PC stecken; Evidence unter  
   `SETUP_LOGS/tui-input-diagnostics/<RUN_ID>/` prüfen (keine `.<id>.partial`-Ordner importieren).

## Abbruch

- `Q` im Assistenten (wenn interaktiv).
- Wenn Persistenz fehlt: **nicht** neu starten, bis SETUP_LOGS gefunden wurde oder Laufdaten manuell gesichert sind.
- Keine Menüpunkte Backup/E2E/Reboot im Diagnosemodus bestätigen (Guard sperrt).

## Datenschutz

Keine Passwörter eingeben. Seriennummern werden redigiert/gehasht.
