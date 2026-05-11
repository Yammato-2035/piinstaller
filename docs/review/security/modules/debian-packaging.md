# Security Review: Debian Packaging

## Kurzbeschreibung

debian/control, changelog, rules, postinst, postrm, prerm, pi-installer.service, Desktop-Dateien, pi-installer.sh. Build mit dpkg-buildpackage; Installation mit apt/dpkg.

## Angriffsfläche

- postinst/postrm/prerm laufen als root bei install/remove.
- Inhalt von control/changelog/rules: Abhängigkeiten, Befehle in rules (make/build).

## Schwachstellen

1. **postinst:** Legt User an, startet systemd – muss fehler tolerant sein; keine unsicheren Eingaben aus Umgebung.
2. **Versionskonsistenz:** Versionsnummer in control/changelog und z. B. config/version.json, package.json sollten übereinstimmen – sonst Verwechslungsrisiko.
3. **Reproduzierbarkeit:** Build-Umgebung (Python/Node-Versionen) sollte dokumentiert sein; Gate prüft Kompatibilität.

## Empfohlene Maßnahmen

- Versions-Gate: Vor Build prüfen, dass VERSION/config/version.json und package.json konsistent sind.
- debian/rules: Keine unsicheren Downloads ohne Integritätsprüfung.
- Dokumentation: Erforderliche Build-Umgebung (Debian/Raspberry Pi OS, Python 3.x, Node 18+).

## Ampelstatus

**GRÜN.** Ausreichend abgesichert; Restverbesserung Versionskonsistenz über Update-Center-Gate.

## Betroffene Dateien

- debian/control, changelog, rules, postinst, postrm, prerm, pi-installer.service, pi-installer.sh.
