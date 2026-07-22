Setuphelfer WinPE / Windows-Setup Diagnosehilfe
================================================

Zweck:
  Setup-Logs und Datenträgerinformationen nach einem abgebrochenen
  Windows-11-Setup sichern — ohne Partitionierung und ohne Änderung
  an Installationsdateien.

Ablauf:
  1. SETUPHELFER_WIN_DIAG von diesem Stick/Medium in WinPE oder dem
     Windows-Setup-Umfeld erreichbar machen (FAT32).
  2. collect-win11-setup-logs.cmd als Administrator ausführen.
  3. Optional collect-win11-disk-info.cmd ausführen.
  4. Zielvolumen mit Label SETUP_LOGS bzw. Datei SETUP_LOGS.TAG wird
     automatisch gesucht.
  5. Ergebnisordner mit Zeitstempel prüfen und Stick erneut mit dem
     Rettungssystem booten, um die Logs zu importieren.

Hinweise:
  - Keine Passwörter oder BitLocker-Keys werden erfasst.
  - Keine diskpart-Schreibbefehle (clean/format/convert).
  - Laufwerksbuchstaben sind variabel — C: wird nicht blind angenommen.
  - Bei erneutem Setup-Abbruch: Collector ausführen, dann Ursachenanalyse
    auf dem Rettungsstick — keine blinde dritte Wiederholung.

Setuphelfer ändert das BIOS nicht und flasht keine Firmware.
