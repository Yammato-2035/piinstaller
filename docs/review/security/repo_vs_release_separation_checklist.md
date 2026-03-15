# REPO vs. RELEASE – Trennung Checkliste (Ampel)

Prüfpunkte für die technische Trennung zwischen REPO- und RELEASE-Version.

---

## A. Frontend

| Prüfpunkt | Erwartung | Ampel | Anmerkung |
|-----------|-----------|-------|-----------|
| Expertenmodul (Update-Center) in Release unsichtbar | Sidebar zeigt „PI-Installer Update“ nur bei app_edition === 'repo' | GRÜN | Sidebar erhält appEdition, Eintrag nur bei repo. |
| Expertenmodul in Release nicht routbar | Bei app_edition === 'release' und currentPage === 'pi-installer-update' wird Dashboard gerendert und Redirect auf dashboard ausgeführt | GRÜN | Route nicht anwählbar; URL ?page=pi-installer-update leitet um. |
| Keine Menüreste in Release | Kein Eintrag „PI-Installer Update“ in der Sidebar, wenn Backend app_edition=release liefert | GRÜN | Eintrag nur bei appEdition === 'repo'. |

---

## B. Backend

| Prüfpunkt | Erwartung | Ampel | Anmerkung |
|-----------|-----------|-------|-----------|
| Repo-only Endpunkte in Release unbrauchbar / nicht registriert | /api/update-center/* bei APP_EDITION=release nicht registriert → 404 | GRÜN | Routen nur unter `if get_app_edition() == "repo"` registriert. |
| app_edition in API | /api/system-info und /api/init/status liefern app_edition (repo | release) | GRÜN | get_app_edition() wird in beiden Antworten gesetzt. |

---

## C. Packaging

| Prüfpunkt | Erwartung | Ampel | Anmerkung |
|-----------|-----------|-------|-----------|
| Keine interne Update-/Developer-Logik versehentlich mit ausgeliefert | Installiertes DEB startet mit APP_EDITION=release; Update-Center-Routen sind nicht registriert | GRÜN | debian/pi-installer.service setzt APP_EDITION=release. |
| Keine toten Verweise | Frontend ruft in Release keine update-center-Endpunkte auf (Seite nicht erreichbar) | GRÜN | Kein Menü, keine Route. |

---

## D. UX (Release)

| Prüfpunkt | Erwartung | Ampel | Anmerkung |
|-----------|-----------|-------|-----------|
| Benutzer sieht nur für ihn relevante Funktionen | Wizard, Presets, Apps, Backup, Monitoring, Einstellungen, Sicherheit, etc. – keine Entwickler-/Packaging-Texte auf der Update-Seite | GRÜN | Update-Seite in Release nicht erreichbar; Nutzerfunktionen über andere Seiten. |
| Entwicklerbegriffe in Release entfernt | Keine „DEB-Build“, „Release-Freigabe“, „Kompatibilitätsprüfung“ in der für Release erreichbaren UI | GRÜN | Diese Begriffe erscheinen nur in PiInstallerUpdate, die in Release nicht gerendert wird. |

---

## Ampel-Zusammenfassung

- **ROT:** Kein Punkt – Expertenfunktion in Release ist weder sichtbar noch routbar noch backendseitig nutzbar.
- **GELB:** Kein Punkt – Trennung ist umgesetzt (Frontend: appEdition-Gate; Backend: bedingte Registrierung; Packaging: APP_EDITION=release in systemd).
- **GRÜN:** Alle geprüften Punkte – sauber getrennt.

---

## Hinweis

Sollte ein Release-Backend versehentlich mit APP_EDITION=repo (oder ohne Setzen in einer Umgebung, die repo setzt) gestartet werden, wären die Update-Center-Endpunkte erreichbar. Abhilfe: Bei Installation aus DEB ist APP_EDITION=release in der systemd-Unit gesetzt. Bei manueller Installation aus dem Repo muss der Betreiber APP_EDITION selbst setzen (Dokumentation: docs/developer/app_modes.md).
