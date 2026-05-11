# Recovery Case Analysis – Setuphelfer

## Kurzfazit

Ein vollständiger Real-World-Recovery-Fall wurde durchlaufen:

fstab → GPU → Display Manager → systemd/nologin → Netzwerk → Backup

Das System wurde wieder betriebsfähig gemacht. Der Fall zeigte aber mehrere relevante Fehlerketten, die künftig im Setuphelfer erkannt, bewertet und teilweise automatisiert abgefangen werden sollten.

## Fehlerkette

### 1. fstab / externe Mounts

Problem:
- Boot wurde durch fehlende oder nicht verfügbare Mounts blockiert.
- Betroffene Pfade waren u. a. Backup- und Windows-Backup-Mounts.

Erkenntnis:
- Externe Backup-Ziele dürfen den Boot nicht blockieren.
- fstab-Einträge für externe Medien benötigen `nofail` und kurze systemd-Timeouts.

### 2. Grafik / Xorg / NVIDIA

Problem:
- LightDM startete nicht.
- Xorg meldete u. a. NVIDIA-/DRM-Probleme und „no screens found“.

Erkenntnis:
- Nach Restore oder Treiberänderungen kann eine GPU-Konfiguration inkonsistent sein.
- Setuphelfer benötigt GPU-/Display-Manager-Diagnosen und Fallback-Empfehlungen.

### 3. systemd / pam_nologin

Problem:
- Login wurde mit „System is booting up. Unprivileged users are not permitted...“ blockiert.
- Ursache war ein nicht vollständig abgeschlossener Boot-Zustand mit `/run/nologin`.

Erkenntnis:
- Setuphelfer sollte `systemctl is-system-running`, failed Units und `/run/nologin` gemeinsam auswerten.

### 4. Netzwerk

Problem:
- Nach Wiederherstellung war das Netzwerk zeitweise nicht funktionsfähig.

Erkenntnis:
- NetworkManager-Status, Interfaces, rfkill und DNS müssen Teil einer Recovery-Baseline sein.

### 5. Backup-Stall

Problem:
- Ein Full-Backup blieb bei ca. 27,46 GB stehen.
- Der Job musste kontrolliert abgebrochen werden.

Ursachen:
- Full-Backup nutzte `/` als Quelle und schloss `/media` nicht aus.
- Dadurch lagen externe Medien und das Backup-Zielmedium im Backup-Scope.
- Zusätzlich bestand ein Risiko für Pipe-Backpressure durch stdout/stderr bei tar.

Fix:
- `/media` und `/run/media` wurden als Full-Backup-Excludes ergänzt.
- stdout wurde auf DEVNULL gesetzt.
- stderr wird während des Laufs konsumiert.

## Bewertung

Der Fall zeigt, dass reale Recovery-Probleme selten isoliert sind. Typisch ist eine Fehlerkette:

1. Bootblocker
2. Grafikfehler
3. systemd-Zwischenzustand
4. Netzwerkproblem
5. Backup-/Storage-Problem

Setuphelfer sollte deshalb nicht nur Einzelchecks anbieten, sondern eine zustandsbasierte Recovery-Diagnosekette.

## Status

- System wieder betriebsfähig: JA
- Backup-Fix implementiert: JA
- Backup nach Fix final erfolgreich verifiziert: NOCH NICHT DOKUMENTIERT
- Freigabe für Monolith-Refactoring: erst nach erfolgreichem Backup + Verify
