# Screenshot-Issues – Technische Analyse

Datum: 2026-03-20

## Update (Sanierung A1)

- Screenshots liegen jetzt im Theme unter `website/setuphelfer-theme/assets/screenshots/` und werden in Snippets als `assets/screenshots/<datei>.png` referenziert (wird wie andere Theme-Assets zu absoluten URLs aufgelöst).
- Legacy-Pfade `/docs/screenshots/...` werden in `setuphelfer_render_snippet()` weiterhin auf Theme-Assets umgebogen (Fallback).
- Sync-Hinweis: `assets/screenshots/README.md`

---

## Befund (historischer Audit-Stand)

- Referenzierte Screenshot-Dateien sind im Repository vorhanden (`frontend/public/docs/screenshots`).
- Auf Theme-Seiten werden sie per **absolutem Pfad** eingebunden: `/docs/screenshots/<datei>.png`.
- Damit ist Anzeige nur korrekt, wenn auf dem Zielsystem ein öffentlich erreichbarer Pfad `/docs/screenshots` existiert.

## Ursachenanalyse nach Fehlerklasse

## 1) Falsche Dateinamen
- Ergebnis: **kein Befund** (alle referenzierten Dateinamen wurden lokal gefunden).

## 2) Falsche Pfade
- Ergebnis: **kritischer Befund**
- Ursache: WordPress-Theme-Assets werden korrekt über `assets/...` gerendert; Screenshots liegen aber außerhalb des Themes und werden absolut referenziert.
- Auswirkung: auf Servern ohne ausgerolltes `/docs` werden Bilder 404 liefern.

## 3) Build-/Export-Probleme
- Ergebnis: **potenzieller Befund**
- Ursache: Screenshot-Quelle ist `frontend/public/docs/screenshots` (Frontend-Build-Kontext), nicht automatisch WordPress-Theme-Kontext.
- Auswirkung: Deployment muss Screenshots explizit mitführen.

## 4) Relative vs. absolute Pfade
- Ergebnis: **kritischer Befund**
- Ursache: absolute Root-Pfade statt theme-relativer oder upload-basierter Pfade.
- Auswirkung: Pfadauflösung hängt vom Server-Root-Layout ab.

## 5) Fehlende Dateien
- Ergebnis: **kein lokaler Fehlbestand**
- Hinweis: Auf Live kann trotzdem „fehlt“ auftreten, falls `/docs` nicht deployt wurde.

## 6) Falsche Import-Strategie
- Ergebnis: **Befund**
- Ursache: harte URL-Strings in Snippets statt zentraler Asset-Funktion (`setuphelfer_asset()` oder WP-Medienpfad).

## 7) Lazy-Loading-/Komponentenfehler
- Ergebnis: **kein Primärfehler**
- `loading="lazy"` wird automatisch ergänzt; Hero-Bild ist ausgenommen (`loading="eager"`).
- Das aktuelle Problem ist Pfadauflösung, nicht Lazy-Loading.

---

## Konkrete defekte/risikobehaftete Einbindungen

Alle nachfolgenden Einbindungen sind **risikobehaftet** (`bedingt`), solange `/docs/screenshots` nicht garantiert öffentlich bereitsteht:

- `/docs/screenshots/screenshot-dashboard.png`
- `/docs/screenshots/screenshot-wizard.png`
- `/docs/screenshots/screenshot-settings.png`
- `/docs/screenshots/screenshot-presets.png`
- `/docs/screenshots/screenshot-security.png`
- `/docs/screenshots/screenshot-users.png`
- `/docs/screenshots/screenshot-backup.png`
- `/docs/screenshots/screenshot-documentation.png`
- `/docs/screenshots/screenshot-control-center.png`
- `/docs/screenshots/screenshot-monitoring.png`
- `/docs/screenshots/screenshot-webserver.png`
- `/docs/screenshots/screenshot-devenv.png`
- `/docs/screenshots/screenshot-nas.png`

---

## Technische Reparaturliste (verbindlich)

1. Entscheidung treffen:
   - **Option A:** `/docs/screenshots` als festen öffentlichen Pfad auf dem Webserver ausrollen.
   - **Option B (robuster):** Screenshots ins Theme-/Upload-System überführen und Pfade dynamisch generieren.
2. Automatisierten Linkcheck in Deploy ergänzen (404-Prüfung auf alle Screenshot-URLs).
3. Snippets auf konsistente Asset-Strategie umstellen (kein harter Root-Pfad ohne Deploymentvertrag).

---

## Neu-Erzeugungsliste (nur falls Quelle fehlt/veraltet)

Wenn Screenshots technisch fehlen, beschädigt sind oder nicht dem aktuellen Build entsprechen, müssen folgende Dateien mit der Tauri-App neu erzeugt werden:

- `screenshot-dashboard.png`
- `screenshot-wizard.png`
- `screenshot-settings.png`
- `screenshot-presets.png`
- `screenshot-security.png`
- `screenshot-users.png`
- `screenshot-backup.png`
- `screenshot-documentation.png`
- `screenshot-control-center.png`
- `screenshot-monitoring.png`
- `screenshot-webserver.png`
- `screenshot-devenv.png`
- `screenshot-nas.png`
