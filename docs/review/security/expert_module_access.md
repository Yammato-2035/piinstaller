# Rollen- und Sichtbarkeitskontrolle im Expertenbereich

---

## Aktueller Stand

- **Erfahrungsstufe (experienceLevel):** `beginner` | `advanced` | `developer` (aus First-Run-Wizard bzw. Einstellungen).
- **UIMode (Sidebar):** `basic` | `advanced` | `diagnose`.
- **PI-Installer Update:** Sidebar-Eintrag „PI-Installer Update“ ist den Modi `advanced` zugeordnet (nicht `developerOnly`). Damit ist die Seite für alle „fortgeschrittenen“ Nutzer sichtbar, nicht nur für „developer“.

## Update-Center (Expertenmodul)

- Das **Update-Center** (Kompatibilitätsprüfung, DEB-Build, Release-Freigabe) ist in die **bestehende** Seite „PI-Installer Update“ integriert.
- **Sichtbarkeit:** Wer die Seite „PI-Installer Update“ sieht (advanced), sieht auch das Expertenmodul (sofern Backend Update-Center unterstützt).
- **Kritische Aktionen:**
  - **Kompatibilität prüfen:** Ausführung erlaubt für jeden, der die Seite sieht; keine privilegierten Systemänderungen.
  - **DEB bauen:** Nur möglich, wenn `ready_for_deb_release === true` (Backend lehnt sonst ab). Kein zusätzliches Passwort.
  - **Auf /opt installieren (Deploy):** Unverändert; kann sudo erfordern (Befehl zum manuellen Ausführen wird angezeigt, wenn automatisch nicht möglich).

## Empfehlung für strikte Developer-Only-Sichtbarkeit

Falls das Update-Center **nur** für Entwickler sichtbar sein soll:

- Option A: Sidebar-Eintrag „PI-Installer Update“ mit `developerOnly: true` versehen (analog zu „Dev-Umgebung“, „Mailserver“). Dann nur bei `experienceLevel === 'developer'` sichtbar.
- Option B: Seite bleibt für „advanced“ sichtbar; nur der **Block „Expertenmodul – Update-Center“** (Kompatibilität prüfen, DEB bauen) wird per Bedingung `experienceLevel === 'developer'` gerendert. Normale „advanced“ Nutzer sehen weiterhin nur „Auf /opt installieren“.

Aktuell umgesetzt: **Option B nicht erzwungen** – alle „advanced“ Nutzer sehen das Expertenmodul. Die **Sicherheit** wird durch das Gate gewährleistet (Build nur bei bestandener Prüfung); die **Sichtbarkeit** kann bei Bedarf auf developerOnly umgestellt werden.

## Bestätigung und Sperre bei Blockern

- **Explizite Bestätigung:** Der Button „DEB bauen“ ist nur klickbar, wenn die Anzeige „Release-Freigabe: freigegeben“ erscheint (und `ready_for_deb_release` true ist). Kein separates Bestätigungsdialog erforderlich, da das Gate die Freigabe bereits bestätigt.
- **Sperre bei offenem Blocker:** Wenn Blocker vorhanden sind, ist „Release-Freigabe: gesperrt“ und der Button „DEB bauen“ deaktiviert; Backend lehnt `POST /api/update-center/build-deb` mit 400 ab.
- **Sudo/Passwort:** Nur beim **Deploy** (Auf /opt installieren) relevant; dort unverändert (sudo -n oder manueller Befehl).
