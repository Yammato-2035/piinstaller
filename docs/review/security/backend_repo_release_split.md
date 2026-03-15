# Backend: REPO vs. RELEASE Trennung

Repo-only Endpunkte werden in der RELEASE-Version nicht registriert.

---

## Umsetzung

- **Einzige Quelle:** `get_app_edition()` (liest `APP_EDITION` aus der Umgebung, Default `release`).
- **Bei `get_app_edition() == "repo"`** werden die Update-Center-Routen registriert.
- **Bei `get_app_edition() == "release"`** werden sie **nicht** registriert (kein `@app.get`/`@app.post` für diese Pfade). Anfragen an `/api/update-center/*` erhalten dann 404 (FastAPI: keine Route).

Es wird **keine** reine Frontend-Verstecklösung verwendet; die Endpunkte existieren im Release-Backend gar nicht.

---

## Repo-only Endpunkte (nur bei APP_EDITION=repo registriert)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | /api/update-center/status | Gesamtstatus, Quell-/Install-Version, letzter Check/Build |
| POST | /api/update-center/check-compatibility | Kompatibilitätsprüfung ausführen |
| GET | /api/update-center/release-readiness | Freigabestatus, Blocker, Warnungen |
| POST | /api/update-center/build-deb | DEB bauen (nur bei bestandenem Gate) |
| GET | /api/update-center/history | Letzte Prüf-/Build-Läufe |

Diese sind in `backend/app.py` in einem Block `if get_app_edition() == "repo":` definiert und mit `[repo-only]` in der Docstring-Kennzeichnung versehen.

---

## Nicht betroffen (in beiden Modi verfügbar)

- `/api/self-update/status`, `/api/self-update/install` – bleiben registriert (Deploy auf /opt). In der RELEASE-Version ist die zugehörige Seite im Frontend nicht verlinkt und nicht routbar; ein Aufruf der API aus dem Frontend erfolgt in Release nicht (keine entsprechende UI). Optional können diese bei Bedarf ebenfalls nur im Repo-Modus registriert werden.
- Alle übrigen API-Routen (System, Backup, Security, Users, …) sind in beiden Modi verfügbar.

---

## Alternative: harte serverseitige Sperre

Falls eine spätere Architektur eine gemeinsame Registrierung aller Routen erfordert: Statt Nicht-Registrierung könnte jeder Update-Center-Handler zu Beginn prüfen `if get_app_edition() != "repo": return JSONResponse(status_code=403, ...)`. Aktuell ist **keine Registrierung in Release** umgesetzt (bevorzugt).
