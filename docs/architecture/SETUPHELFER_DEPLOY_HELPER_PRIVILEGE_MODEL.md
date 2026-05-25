# Setuphelfer Deploy Helper Privilege Model

## Ziel

Der unprivilegierte Backend-Prozess soll genau **eine** privilegierte Aktion anfordern koennen:

- `setuphelfer-deploy-helper.service` starten

Nicht erlaubt ist ein allgemeines Root-Gateway fuer Shell, `deploy-to-opt.sh`, Wildcards oder andere Systemaenderungen.

## Variante A - systemd start + Polkit

### Idee

Das Backend bzw. der Desktop-Benutzer darf genau den Start der Unit `setuphelfer-deploy-helper.service` ueber einen passenden Polkit-Pfad ausloesen.

### Vorteile

- sauberer systemd-/Desktop-Weg
- Berechtigung bezieht sich auf die Unit, nicht auf eine Shell
- spaeter fuer produktionsnaeheres Setup besser geeignet
- gut mit Audit und Desktop-Dialogen kombinierbar

### Nachteile

- Einrichtung komplexer als ein enges `sudoers`-Snippet
- Polkit-Regeln muessen distributionsspezifisch sauber getestet werden
- fuer reine Entwicklungsrechner etwas mehr Initialaufwand

## Variante B - sudoers NOPASSWD nur fuer systemctl start/status

### Idee

Ein sehr enges `sudoers`-Snippet erlaubt ausschliesslich:

- `/bin/systemctl start setuphelfer-deploy-helper.service`
- `/bin/systemctl status setuphelfer-deploy-helper.service`

### Vorteile

- fuer Development schnell und einfach einrichtbar
- kein direkter Zugriff auf `deploy-to-opt.sh`
- keine Wildcards, kein `/bin/bash`, kein freier Root-Command

### Nachteile

- `sudoers` bleibt trotzdem ein sensibler Pfad
- nur tragbar, wenn der Befehl **streng** eingegrenzt bleibt
- weniger elegant als ein sauberer Polkit-/systemd-Weg

## Bewertung

### Empfohlen fuer spaeter / systemnah

**Variante A - Polkit**  
Das ist langfristig der sauberere Ansatz, weil die Berechtigung semantisch an der systemd-Unit haengt.

### Empfohlen fuer lokale Entwicklung

**Variante B - eng begrenztes sudoers-Beispiel**  
Nur als bewusst manuell installierbare Entwicklungsoption, niemals automatisch und niemals breiter als `systemctl start/status` fuer genau diese Unit.

## Wichtige Verbote

Unabhaengig von der Variante gilt:

- kein NOPASSWD fuer `deploy-to-opt.sh` direkt
- kein NOPASSWD fuer `/bin/bash`
- kein NOPASSWD mit Wildcards
- kein Root-Zugriff fuer `apt`, `dd`, `mkfs`, `parted`, `mount`, `umount`
- kein Root-Zugriff fuer Backup, Restore oder USB-Write

## Beispiel-Snippet

Datei:

- `packaging/sudoers.d/setuphelfer-deploy-helper.example`

Inhalt:

```text
setuphelfer ALL=(root) NOPASSWD: /bin/systemctl start setuphelfer-deploy-helper.service, /bin/systemctl status setuphelfer-deploy-helper.service
```

## Fazit

- **Polkit** ist der saubere Zielpfad.
- **sudoers** ist nur als enge Development-Bruecke akzeptabel.
- In beiden Faellen bleibt die Root-Aktion an die feste systemd-Unit gebunden.
