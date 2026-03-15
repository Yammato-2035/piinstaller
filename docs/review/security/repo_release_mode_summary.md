# REPO vs. RELEASE – Moduszusammenfassung

Überblick über die technische Trennung, geänderte/neue Dateien und Absicherung.

---

## Moduslogik

- **Zentrale Wahrheit:** Umgebungsvariable **APP_EDITION** mit Werten `repo` | `release` (Default: `release`).
- **Backend:** Liest APP_EDITION beim Start; liefert `app_edition` in `/api/system-info` und `/api/init/status`. Registriert die Update-Center-Routen **nur** bei `APP_EDITION=repo`.
- **Frontend:** Liest `app_edition` aus der System-Info; zeigt und routet das Expertenmodul (PI-Installer Update) **nur** bei `app_edition === 'repo'`. Bei Release: kein Menüeintrag, keine Route, Redirect auf Dashboard.

---

## Repo-only Funktionen

- **Frontend:** Seite „PI-Installer Update“ (Komponente PiInstallerUpdate) inkl. Expertenmodul (Kompatibilität prüfen, DEB bauen, Release-Freigabe, Blocker, History). Sichtbar und routbar nur bei app_edition === 'repo'.
- **Backend:** Endpunkte `/api/update-center/status`, `/api/update-center/check-compatibility`, `/api/update-center/release-readiness`, `/api/update-center/build-deb`, `/api/update-center/history`. Registriert nur bei APP_EDITION=repo.

---

## Release: Benutzerumfang

- Alle anderen Seiten und APIs (Dashboard, Wizard, Presets, Apps, Backup, Monitoring, Documentation, Settings, Security, Users, Control Center, Periphery, Webserver, NAS, Homeautomation, Musicbox, Kino, Learning, Raspberry Pi Config, Remote, DSI-Radio, ggf. Dev-Umgebung/Mailserver bei experienceLevel developer).
- Kein PI-Installer Update (Expertenmodul), keine Update-Center-API, keine Packaging-/Entwicklertexte in der erreichbaren UI.

---

## Technische Absicherung

1. **Frontend:** Kein reines Verstecken per CSS – Sidebar-Eintrag und Route sind an `appEdition` gekoppelt; bei Release wird die Expertenseite nicht gerendert und bei Aufruf auf Dashboard umgeleitet.
2. **Backend:** Update-Center-Routen werden bei Release **nicht** registriert (kein 403, sondern 404).
3. **Packaging:** DEB-Service setzt `APP_EDITION=release` in der systemd-Unit; Entwicklung aus Repo kann `.env` mit `APP_EDITION=repo` nutzen.

---

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| backend/app.py | get_app_edition(); app_edition in /api/system-info und /api/init/status; Update-Center-Routen nur bei get_app_edition() == "repo" registriert |
| frontend/src/App.tsx | appEdition aus systemInfo; an Sidebar; case pi-installer-update nur bei repo; useEffect Redirect bei release |
| frontend/src/components/Sidebar.tsx | Prop appEdition; Menüeintrag PI-Installer Update nur bei appEdition === 'repo' |
| scripts/start-backend.sh | Lädt .env aus Repo-Root (optional APP_EDITION=repo) |
| debian/pi-installer.service | Environment="APP_EDITION=release" |

---

## Neue Dateien

| Datei | Inhalt |
|-------|--------|
| .env.example | APP_EDITION=release, optionale Hinweise |
| docs/developer/app_modes.md | Modi repo/release, Bedeutung, wie Build den Modus bestimmt |
| docs/review/security/frontend_repo_release_split.md | Frontend-Trennung, Routen, Sidebar |
| docs/review/security/backend_repo_release_split.md | Repo-only Endpunkte, keine Registrierung in Release |
| docs/release/release_user_generation_scope.md | In Release sichtbare Benutzerfunktionen |
| docs/review/security/build_packaging_repo_release_split.md | Build/Packaging, DEB = Release |
| docs/review/security/repo_vs_release_separation_checklist.md | Ampel-Checkliste |
| docs/review/security/repo_release_mode_summary.md | Diese Datei |

---

## Offene Restrisiken der Trennung

- Wenn ein installiertes System (z. B. nach manueller Anpassung) mit `APP_EDITION=repo` gestartet wird, wären die Update-Center-Funktionen erreichbar. Abhilfe: Dokumentation und ggf. Konfiguration nur über berechtigte Stellen.
- Ein einzelner Frontend-Build enthält weiterhin den Code für PiInstallerUpdate; er wird in Release nur nicht gerendert/routet. Gewollt (einfache Build-Struktur); bei Bedarf könnte ein strikter Release-Build den Expertencode weglassen.

---

## Kurze Gesamtbewertung

Die Trennung zwischen REPO- und RELEASE-Version ist **technisch umgesetzt**: Eine zentrale Modusdefinition (APP_EDITION), bedingte Backend-Routenregistrierung, frontendseitige Anzeige und Routing nur bei repo, sowie APP_EDITION=release im DEB-Service. Das Experten-Update-Modul existiert ausschließlich im REPO-Modus; in der RELEASE-Version ist es weder sichtbar noch routbar noch backendseitig nutzbar. Bestehende Benutzerfunktionen bleiben unverändert.
