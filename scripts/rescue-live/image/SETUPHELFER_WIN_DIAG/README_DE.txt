Setuphelfer WinPE / Windows-Setup Diagnosehilfe
================================================

Zweck:
  Setup-Logs und Datenträgerinformationen nach einem abgebrochenen
  Windows-11-Setup sichern — ohne Partitionierung und ohne Änderung
  an Installationsdateien.

Ablauf:
  1. SETUPHELFER_WIN_DIAG von diesem Stick/Medium in WinPE oder dem
     Windows-Setup-Umfeld erreichbar machen (FAT32).
  2. collect-win11-setup-logs.cmd als Administrator ausführen
     (ruft bei Verfügbarkeit die .ps1-Helfer auf).
  3. Optional separat:
       - collect-win11-disk-info.cmd
       - collect-win11-boot-info.cmd OUTDIR
  4. Zielvolumen mit Label SETUP_LOGS bzw. Datei SETUP_LOGS.TAG wird
     automatisch gesucht (Laufwerksbuchstaben sind variabel).
  5. Ergebnisordner mit Zeitstempel und Run-ID prüfen und Stick erneut
     mit dem Rettungssystem booten, um die Logs zu importieren.

Erfasst unter anderem:
  - Panther / Rollback / SetupDiag / DISM / CBS / setupapi
  - Get-Disk / Get-PhysicalDisk / UniqueId / Seriennummer (falls vorhanden)
  - diskpart list (nur Lesen), bcdedit /enum, mountvol, EFI-Probe

Hinweise:
  - Keine Passwörter oder BitLocker-Keys werden erfasst.
  - Keine diskpart-Schreibbefehle (clean/format/convert/online).
  - Keine Registryänderungen.
  - Roh-Identifier nur lokal auf SETUP_LOGS; Git-Import nur redaktiert.
  - Bei erneutem Setup-Abbruch: Collector ausführen, dann Ursachenanalyse —
    keine blinde dritte Wiederholung.

Setuphelfer ändert das BIOS nicht und flasht keine Firmware.
