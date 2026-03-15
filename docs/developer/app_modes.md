# App-Modi (APP_EDITION)

Zentrale technische Trennung zwischen **REPO-Modus** (Entwicklung) und **RELEASE-Version** (Endnutzer).

---

## Modi

| Modus | Bedeutung |
|-------|-----------|
| **repo** | Entwickler-Build: Update-Center, DEB-Build, Kompatibilitätsprüfung, Expertenseiten und -endpunkte sind vorhanden und nutzbar. |
| **release** | Endnutzer-Build: Keine Experten-/Developer-Funktionen; nur Benutzerfunktionen (Vorlagen, Presets, Zielsysteme, Setup). |

Es gibt **nur eine zentrale Wahrheit**: die Umgebungsvariable **APP_EDITION**.

- Gültige Werte: `repo` | `release`
- **Default:** `release` (wenn nicht gesetzt oder ungültig)
- Frontend und Backend nutzen dieselbe Definition: Backend liest `APP_EDITION` und liefert `app_edition` in `/api/system-info` und `/api/init/status`; das Frontend entscheidet anhand dieses Werts über Sichtbarkeit und Routen.

---

## Was „repo“ bedeutet

- **Backend:** Update-Center-Endpunkte (`/api/update-center/*`) sind registriert und antworten.
- **Frontend:** Seite „PI-Installer Update“ zeigt das Expertenmodul (Kompatibilität prüfen, DEB bauen, Release-Freigabe, Blocker). Eintrag in der Sidebar, Route erreichbar.
- **Build/Packaging:** Repo-Build kann mit `APP_EDITION=repo` gebaut werden; das gebündelte Frontend enthält die Experten-UI, Backend wird mit repo-Modus gestartet.

---

## Was „release“ bedeutet

- **Backend:** Update-Center-Endpunkte sind **nicht** registriert (oder hart mit 403/404 gesperrt). Keine DEB-Build-, Kompatibilitäts- oder Release-Readiness-API.
- **Frontend:** Keine Sidebar-Verlinkung zum Experten-Update-Modul, keine Route zu dessen Inhalten, keine Expertenkarten/Build-Historie/DEB-Freigabe. Nur die benutzerseitige Funktionalität (z. B. Zielsystem auswählen, Vorlagen/Presets/Images erzeugen) mit verständlichen Endnutzertexten.
- **Build/Packaging:** Release-Build wird mit `APP_EDITION=release` (oder ohne Setzen) erzeugt; Expertencode kann beim Build ausgelassen werden, sodass er nicht ausgeliefert wird.

---

## Wie der Build den Modus bestimmt

1. **Backend (Laufzeit):** Liest `APP_EDITION` aus der Umgebung (z. B. gesetzt durch systemd, Startskript oder `.env`). Bei Installation aus DEB-Paket: in der systemd-Unit oder in einer Konfigurationsdatei, die vor dem Start geladen wird, `APP_EDITION=release` setzen (oder weglassen, dann Default release).
2. **Frontend (Build-Zeit + Laufzeit):**
   - **Build-Zeit:** Optional `VITE_APP_EDITION=repo` bzw. `VITE_APP_EDITION=release` beim `npm run build`. Damit kann das Frontend-Bundle nur die zum Modus passenden Routen/Komponenten enthalten (repo-Bundle mit Expertenmodul, release-Bundle ohne).
   - **Laufzeit:** Beim App-Start wird `/api/system-info` oder `/api/init/status` aufgerufen; das Backend liefert `app_edition`. Das Frontend blendet Routen und Menüeinträge nur ein, wenn `app_edition === 'repo'`. So bleibt die Backend-Entscheidung maßgeblich, auch wenn jemand ein repo-Bundle gegen ein release-Backend verwendet.
3. **Einheit:** Backend ist die autoritative Quelle. Frontend sollte in der Release-Build-Variante die Experten-Routen gar nicht einbinden (kein toter Code), in der Repo-Build-Variante einbinden, aber nur anzeigen/routbar machen, wenn `app_edition === 'repo'`.

---

## Konfiguration

- **.env (optional):** `APP_EDITION=repo` oder `APP_EDITION=release`. Siehe `.env.example`. Startskripte können `.env` laden (z. B. `set -a; [ -f .env ] && . ./.env; set +a`).
- **systemd:** In `Environment=` der Service-Datei z. B. `Environment=APP_EDITION=release` für die installierte Version.
- **Skripte:** In `scripts/start-backend.sh` kann vor dem Start `export APP_EDITION=repo` gesetzt werden, wenn aus dem Quellbaum entwickelt wird (oder aus `.env` übernommen).

Es wird **kein** separates `REPO_MODE` verwendet; allein **APP_EDITION** ist die zentrale Wahrheit.
