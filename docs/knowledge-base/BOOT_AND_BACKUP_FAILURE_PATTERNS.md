# Boot and Backup Failure Patterns

## Zweck

Diese Wissensbasis beschreibt typische Fehlerketten aus einem realen Recovery-Fall und dient als Grundlage für spätere Setuphelfer-Diagnosen.

## Fehlerkette

```text
fstab → GPU/Xorg → Display Manager → systemd/nologin → Netzwerk → Backup
```

### Fehlerklasse: BOOT-FSTAB-BLOCKER

Symptome
- Boot hängt bei Mount-Jobs
- systemd wartet auf nicht vorhandene UUIDs
- GUI startet nicht

Ursache
- externe Datenträger in `/etc/fstab` ohne `nofail`
- falsche oder nicht verfügbare UUIDs

Erkennung
- `systemctl list-jobs`
- `journalctl -b`
- `findmnt`
- `lsblk -f`

Gegenmaßnahme
- externe Mounts mit `nofail`
- `x-systemd.device-timeout=5s`
- keine Bootblockade durch Backup-Ziele

### Fehlerklasse: GPU-CONFIG-MISMATCH-AFTER-RESTORE

Symptome
- schwarzer Bildschirm
- LightDM startet nicht
- Xorg meldet „no screens found“
- NVIDIA-/DRM-Fehler

Ursache
- inkonsistente GPU-Treiber nach Restore oder Paketänderungen
- alte Xorg-Konfiguration
- NVIDIA/Hybrid-GPU-Konflikt

Erkennung
- `systemctl status lightdm`
- `/var/log/Xorg.0.log`
- `ls /dev/dri`
- `glxinfo`

Gegenmaßnahme
- Xorg-Konfiguration prüfen
- Display Manager neu starten
- GPU-Fallback prüfen
- keine unkontrollierten Treiberwechsel

### Fehlerklasse: SYSTEMD-NOLOGIN-LOCK

Symptome
- Login verweigert
- Meldung: „System is booting up. Unprivileged users are not permitted...“

Ursache
- `/run/nologin` existiert
- systemd erreicht nicht running
- failed oder hängende Units

Erkennung
- `systemctl is-system-running`
- `systemctl --failed`
- `systemctl list-jobs`
- Prüfung auf `/run/nologin`

Gegenmaßnahme
- blockierende Unit ermitteln
- nur begründet `/run/nologin` entfernen
- Bootzustand erneut prüfen

### Fehlerklasse: NETWORK-STACK-NOT-INITIALIZED

Symptome
- kein Netzwerk
- DNS funktioniert nicht
- Interfaces offline

Ursache
- NetworkManager nicht aktiv
- rfkill
- Treiber-/Firmwareproblem
- Recovery-Zustand

Erkennung
- `systemctl status NetworkManager`
- `ip a`
- `nmcli device`
- `rfkill list`
- Ping auf IP und Domain

Gegenmaßnahme
- NetworkManager aktivieren/neustarten
- rfkill lösen
- DNS prüfen

### Fehlerklasse: BACKUP-SOURCE-SCOPE-TOO-BROAD

Symptome
- Full-Backup wird sehr groß
- Backup bleibt stehen
- externe Medien werden mitgesichert

Ursache
- Backup von `/`
- fehlender Exclude von `/media` und `/run/media`

Erkennung
- Prüfung des tar-Kommandos
- Prüfung der Exclude-Liste
- Vergleich mit Mount-Tabelle

Gegenmaßnahme
- `/media` und `/run/media` aus Full-Backup ausschließen
- Backup-Zielpfad ausschließen
- dynamische Mount-Erkennung langfristig ergänzen

### Fehlerklasse: TAR-PIPE-BACKPRESSURE

Symptome
- tar/gzip-Prozess läuft noch
- Backup-Dateigröße wächst nicht mehr
- keine Python-Exception

Ursache
- stdout/stderr als PIPE
- Lesen erst nach Prozessende
- Pipe-Puffer läuft voll

Erkennung
- Prozess läuft, aber Fortschritt stagniert
- keine I/O-Fehler
- keine Dateiänderung

Gegenmaßnahme
- stdout nach DEVNULL
- stderr während Lauf konsumieren
- Cancel-Logik erhalten

## Diagnoseprinzip

Setuphelfer sollte Recovery-Zustände als Kette behandeln:

- Bootstatus
- Mountstatus
- Grafikstatus
- systemd-Status
- Netzwerkstatus
- Backupfähigkeit

Ein einzelner Fix reicht oft nicht aus.
