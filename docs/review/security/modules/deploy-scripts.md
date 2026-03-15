# Security Review: Deploy-/Install-Skripte

## Kurzbeschreibung

Kritische Shell-Skripte: create_installer.sh, deploy-to-opt.sh, install-system.sh, build-deb.sh, release-service.sh, uninstall-system.sh, install-backend-service.sh. Werden von Backend oder manuell ausgeführt; teilweise mit sudo.

## Angriffsfläche

- Aufruf mit Argumenten (z. B. Repo-Pfad, Optionen); Umgebungsvariablen.
- Risiko: Argumente oder ENV von außen (z. B. Backend) beeinflusst.

## Schwachstellen

1. **Parameter:** Skripte dürfen keine unvalidierten Parameter in Befehle einbauen (z. B. Pfad muss fest oder strikt validiert sein). deploy-to-opt.sh wird mit repo_root aufgerufen – aus Backend stammend (Path(__file__)), nicht aus Request.
2. **Reproduzierbarkeit:** build-deb.sh sollte deterministisch sein; Abhängigkeiten dokumentiert.
3. **Rechte:** Minimale nötige Rechte; keine unnötigen world-writable Verzeichnisse.

## Empfohlene Maßnahmen

- Keine Nutzer- oder Request-Daten als Argumente an diese Skripte übergeben; nur Backend-interne Pfade.
- Dokumentation: Welche ENV/Pakete für Build nötig sind; Gate vor release-service (apt install .deb).

## Ampelstatus

**GELB.** Relevante Sorgfalt (Parameterquelle); kein ROT wenn Aufruf nur aus Backend mit festem Repo-Pfad.

## Betroffene Dateien

- scripts/deploy-to-opt.sh, build-deb.sh, release-service.sh, install-system.sh, create_installer.sh, install-backend-service.sh, uninstall-system.sh.
