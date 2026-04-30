# TODO – Recovery, Rettungsstick und Monolith-Refactoring

## Statusregel

Monolith-Refactoring darf erst beginnen, wenn folgende Punkte erfüllt sind:

- Target-Check für Backup-Ziel erfolgreich
- Full Backup erfolgreich abgeschlossen
- Backup-Archiv vorhanden
- MANIFEST.json vorhanden
- Basic Verify erfolgreich
- Deep Verify erfolgreich oder begründet nicht verfügbar
- keine roten Blocker im Systemstatus

## Priorität 1 – Backup-Freigabe nach Fix

- [ ] Backend mit aktuellem Code starten
- [ ] Target-Check für `/media/volker/setuphelfer-back/backups` erneut prüfen
- [ ] Full Backup erneut starten
- [ ] Jobstatus überwachen
- [ ] Backup-Datei prüfen
- [ ] MANIFEST.json im Archiv prüfen
- [ ] Basic Verify durchführen
- [ ] Deep Verify durchführen, falls verfügbar
- [ ] Abschlussbericht erstellen
- [ ] Bei Erfolg Commit/Push vorbereiten
- [ ] Tag `stable-pre-monolith-refactor` setzen

## Priorität 2 – Rettungsstick-Maßnahmen

- [ ] Minimal bootfähiges Livesystem definieren
- [ ] RAM-only Betriebsmodus konzipieren
- [ ] Read-only Root-Dateisystem prüfen
- [ ] Automatische Storage-Erkennung integrieren
- [ ] safe_device-Klassifikation im Rettungsstick nutzen
- [ ] Systemdisk, Windowsdisk, EFI und Bootdisk sicher erkennen
- [ ] Backup-Ziele nur auf sicheren externen Medien erlauben
- [ ] Restore nur nach Preview und Hardstop-Prüfung erlauben
- [ ] Netzwerk-Fallback mit DHCP integrieren
- [ ] SSH-Notzugang optional absichern
- [ ] Diagnosebericht beim Start erzeugen
- [ ] Bootstatus-Ampel implementieren
- [ ] Rescue-UI für Anfänger/Fortgeschrittene/Experten skizzieren
- [ ] Keine automatische destruktive Reparatur ohne Bestätigung

## Priorität 3 – Boot-/Recovery-Diagnosen

- [ ] fstab-Checker implementieren
- [ ] Fehlende UUIDs erkennen
- [ ] Externe Mounts ohne `nofail` melden
- [ ] systemd `is-system-running` auswerten
- [ ] `systemctl --failed` auswerten
- [ ] `/run/nologin` erkennen
- [ ] Display-Manager-Status prüfen
- [ ] Xorg-Fehler auswerten
- [ ] GPU-/DRM-Status prüfen
- [ ] NetworkManager-Status prüfen
- [ ] rfkill prüfen
- [ ] DNS-Test integrieren
- [ ] Bootloader-/GRUB-Erkennung vorbereiten
- [ ] Raspberry-Pi-Bootdateien (`config.txt`, `cmdline.txt`) prüfen

## Priorität 4 – Backup-Engine-Härtung

- [ ] Logging der zuletzt bearbeiteten Datei prüfen
- [ ] Stall-Erkennung für Backup-Jobs konzipieren
- [ ] Timeout-/No-progress-Watcher entwerfen
- [ ] Cancel-Verhalten weiter testen
- [ ] Exclude-Liste dokumentieren
- [ ] Exclude-Liste langfristig konfigurierbar machen
- [ ] Dynamische Mount-Excludes prüfen
- [ ] Self-recursion-Schutz testen
- [ ] Verify-Fehlercodes vereinheitlichen
- [ ] Deep Verify dokumentieren

## Priorität 5 – Monolith-Refactoring

Erst nach erfolgreichem Backup + Verify.

- [ ] Ist-Analyse Backend-Struktur
- [ ] API-Routen von Fachlogik trennen
- [ ] Backup-Modul isolieren
- [ ] Restore-Modul isolieren
- [ ] Storage-/safe_device-Modul konsolidieren
- [ ] Boot-Diagnosemodul vorbereiten
- [ ] systemd-Diagnosemodul vorbereiten
- [ ] Netzwerk-Diagnosemodul vorbereiten
- [ ] Grafik-Diagnosemodul vorbereiten
- [ ] einheitlichen Response-Contract zentralisieren
- [ ] Diagnosecodes zentralisieren
- [ ] Tests vor jeder Verschiebung sichern
- [ ] Keine Verhaltensänderung ohne Test

## Noch nicht umgesetzte Prompts

### Prompt: Erneuter Full-Backup-Test nach Fix

```text
Du arbeitest im Setuphelfer-Projekt.

Ziel:
Nach dem Minimalfix für den Full-Backup-Stall wird genau ein erneuter Full-Backup-Test durchgeführt, anschließend Manifest geprüft und Verify ausgeführt. Kein Refactoring.

Regeln:
- Kein Monolith-Refactoring.
- Keine neuen Features.
- Keine Änderungen an Storage-Schutzlogik, Restore oder Target-Check.
- Kein manuelles tar-Backup.
- Kein alternatives Ziel.
- Bei Fehler: abbrechen, Fehlercode dokumentieren, nicht improvisieren.

Ausgangslage:
- Backup-Ziel: /media/volker/setuphelfer-back/backups
- Medium: /dev/sda1 ext4 extern
- Rechte: root:setuphelfer, 2770
- /media und /run/media sind jetzt im Full-Backup ausgeschlossen
- stdout/stderr-Pipe-Stall wurde entschärft

Aufgaben:
1. Backend mit aktuellem Code starten oder sicherstellen, dass aktueller Code aktiv ist.
2. Storage-Validierung erneut prüfen.
3. Full Backup starten.
4. Job überwachen.
5. Backup-Datei prüfen.
6. Verify durchführen.
7. Abschlussbericht erstellen.
```

### Prompt: Monolith-Refactoring vorbereiten

```text
Du arbeitest im Setuphelfer-Projekt.

Ziel:
Bereite das Monolith-Refactoring ausschließlich analytisch vor. Keine Codeverschiebungen, solange Backup + Verify nicht erfolgreich abgeschlossen und getaggt sind.

Aufgaben:
1. Backend-Struktur erfassen.
2. API-Routen mit Fachlogik identifizieren.
3. Module vorschlagen.
4. Risiken benennen.
5. Reihenfolge für risikoarme Extraktion definieren.
6. Testabdeckung je Modul prüfen.
7. Abschlussbericht mit Refactoring-Plan erstellen.
```

### Prompt: Rettungsstick-Konzept aktualisieren

```text
Du arbeitest im Setuphelfer-Projekt.

Ziel:
Aktualisiere das Rettungsstick-Konzept anhand des realen Recovery-Falls.

Berücksichtige:
- fstab-Bootblocker
- GPU-/Display-Fehler
- systemd/nologin
- Netzwerk-Recovery
- Backup-Zielvalidierung
- Restore-Hardstops
- sichere externe Medien
- Anfänger-/Fortgeschrittenen-/Expertenmodus

Erstelle:
1. Architekturvorschlag
2. Boot-Ablauf
3. Diagnosemodule
4. Sicherheitsregeln
5. UI-Ablauf
6. Testmatrix
```
