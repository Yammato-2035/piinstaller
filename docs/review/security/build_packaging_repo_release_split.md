# Build und Packaging: REPO vs. RELEASE

Saubere Trennung ohne unnötig komplizierte Build-Matrix.

---

## Prinzip

- **Ein Frontend-Build:** Das gebündelte Frontend fragt zur Laufzeit das Backend nach `app_edition` (/api/system-info). Es gibt **keinen** separaten „release“- und „repo“-Frontend-Build (keine doppelte Build-Matrix). Im Release-Modus zeigt die gleiche App nur die Benutzerfunktionen und blendet das Expertenmodul aus; im Repo-Modus zeigt sie zusätzlich das Update-Center.
- **Backend-Modus zur Laufzeit:** Das Backend liest `APP_EDITION` aus der Umgebung beim Start. Bei `repo` werden die Update-Center-Routen registriert, bei `release` (oder ungesetzt) nicht.
- **DEB-Paket = Release:** Das über build-deb.sh gebaute und mit apt installierte Paket läuft mit **APP_EDITION=release** (in der systemd-Unit gesetzt). Damit enthält die installierte Version kein Update-Center (weder Frontend-Menü/Route noch Backend-Endpunkte).

---

## Build

| Kontext | APP_EDITION | Update-Center |
|---------|-------------|---------------|
| Entwicklung aus Repo (z. B. `./scripts/start-backend.sh`, .env mit `APP_EDITION=repo`) | repo | Backend: Routen registriert. Frontend: Seite sichtbar und routbar (app_edition kommt von API). |
| Installiertes DEB (systemd startet mit Environment aus debian/pi-installer.service) | release | Backend: Routen nicht registriert. Frontend: keine Sidebar, keine Route, Redirect auf Dashboard. |

- **scripts/build-deb.sh:** Baut das Paket unverändert; setzt **keine** APP_EDITION (die wird erst zur Laufzeit in der systemd-Unit gesetzt).
- **scripts/start-backend.sh:** Lädt optional `.env` aus Repo-Root; dort kann `APP_EDITION=repo` für Entwicklung gesetzt werden.

---

## Packaging (debian/)

- **debian/pi-installer.service:** Enthält `Environment="APP_EDITION=release"`. Bei Installation des DEB-Pakets startet der Dienst damit in der Release-Fassung (kein Update-Center).
- **debian/postinst, control, rules, etc.:** Keine Änderung nötig; es werden keine repo-only Assets separat ausgeliefert – die gleichen Dateien laufen je nach APP_EDITION unterschiedlich.
- Keine toten Verweise: Im Release-Build werden die Update-Center-Routen gar nicht registriert; das Frontend ruft sie nicht auf (Seite nicht erreichbar).

---

## Sicherheit

- Repo-only Funktionen werden in der Release-Version **nicht** ausgeliefert (Backend: keine Registrierung; Frontend: keine Menüeinträge/Routen für das Expertenmodul).
- Die Trennung wird durch die **zentrale Modusdefinition** (APP_EDITION) und die **Laufzeit-Entscheidung** im Backend und Frontend abgesichert.
