# FAQ Source Notes – Panda & Branding

## Was macht der Panda?

- Der Panda ist eine ergänzende Helferfigur zum SetupHelfer-Logo.
- Zielgruppe:
  - Einsteiger: visuelle Orientierung, Hinweise auf sichere Standardpfade.
  - Fortgeschrittene: dezenter Hinweis auf Einsteiger-Hilfen.
  - Experten: Panda wird im UI ausgeblendet.
- Technische Umsetzung:
  - Assets: `frontend/public/assets/mascot/*.svg` (basieren alle auf `panda_base.svg`).
  - UI-Komponente: `frontend/src/components/PandaHelper.tsx`.
  - Texte laufen über i18n (`dashboard.panda.*`, `panda.*`).

## Kann ich den Panda deaktivieren?

- Aktuell:
  - Der Panda verschwindet automatisch, wenn das Erfahrungslevel auf „Entwickler“ gestellt wird.
  - Erfahrungslevel kann über die Einstellungen bzw. den First-Run-Wizard angepasst werden.
- Geplante Erweiterung:
  - Optionaler Schalter „Panda-Helfer ausblenden“ in den UI-Einstellungen, der zusätzlich zu den Erfahrungslevels greift.

## Backup / Restore – Verifikation verschlüsselter Backups

- Thema: Was bedeutet „Backup verifizieren“ bei verschlüsselten Archiven?
- Problem:
  - Bisher wurde bei verschlüsselten Backups nur geprüft, ob die Datei existiert und größer als 0 Bytes ist.
  - Nutzer könnten dies als vollständige Integritätsprüfung missverstehen.
- Ursache:
  - Technisch war nur eine Oberflächenprüfung implementiert.
- Lösung:
  - Einführung zweier Modi:
    - Basisprüfung (ohne Schlüssel): Existenz, Größe, Pfad-Validierung; klarer Hinweis, dass der Inhalt nicht entschlüsselt wurde.
    - Tiefenprüfung (mit Schlüssel): temporäres Entschlüsseln in ein sicheres Verzeichnis, anschließende Integritätsprüfung (z. B. `tar -tzf`), konsequentes Aufräumen.
  - API und UI benennen den verwendeten Prüfmodus explizit.
- FAQ-Kandidat: ja
- Tutorial-Kandidat: ja (Erklärung „Wie prüfe ich, ob mein verschlüsseltes Backup wirklich lesbar ist?“)

## Backup / Restore – Warum ist Root-Restore gesperrt?

- Thema: Produktiver Restore auf `/`
- Problem:
  - Früher wurde ein Restore direkt via `tar -xzf ... -C /` ausgeführt, mit Risiko für das Root-Dateisystem.
- Ursache:
  - Vereinfachte erste Implementierung ohne Whitelist und Preview-Modus.
- Lösung:
  - Einführung eines sicheren Preview-Modus, der nur in ein separates Verzeichnis unter `/mnt/setuphelfer-restore-preview/` entpackt.
  - In Phase 1 bleibt der Root-Restore explizit gesperrt, bis Whitelist- und Sicherheitslogik vollständig getestet sind.
- FAQ-Kandidat: ja
- Tutorial-Kandidat: ja (Leitfaden: „So testest du ein Backup, ohne dein System zu überschreiben“)

## Backup / Restore – UI-Verhalten für Test-Restore & Verifikation

- Thema: Warum zeigt die UI „Analyse / Test-Restore“ und nicht direkt „Wiederherstellen“?
- Problem:
  - Frühere UI-Texte suggerierten einen direkten Restore auf das laufende System.
  - Nach der Härtung arbeitet das Backend standardmäßig im Preview-Modus.
- Ursache:
  - Historische 1-Schritt-Restore-UX ohne Preview-Phase.
- Lösung:
  - Restore-Tab verwendet nun standardmäßig eine Analyse-/Test-Restore-Aktion.
  - Die UI kennzeichnet, dass der Test-Restore nur in ein Vorschau-Verzeichnis schreibt und das System nicht überschreibt.
  - Root-Restore wird in Phase 1 nicht als aktive Option angeboten.
- FAQ-Kandidat: ja
- Tutorial-Kandidat: ja (Schritt-für-Schritt-Anleitung „Backup analysieren und Test-Restore prüfen“)

## Backup / Restore – Analyse-Box für Test-Restore

- Thema: Wie lese ich die Analyse-Box nach einem Test-Restore?
- Verhalten:
  - Nach einem erfolgreichen Preview-Restore zeigt der Restore-Tab eine Analyse-Box an.
  - Die Box enthält:
    - Pfad zur Backup-Datei.
    - Pfad zum Vorschau-Verzeichnis (unter `/mnt/setuphelfer-restore-preview/...`).
    - Gesamtzahl der Einträge im Archiv.
    - Aufteilung in Dateien, Verzeichnisse und sonstige Einträge.
  - Ein Hinweis-Text macht explizit klar, dass das laufende System bei diesem Schritt nicht überschrieben wurde.
- FAQ-Kandidat: ja
- Tutorial-Kandidat: ja (Beispiel-Screenshot der Analyse-Box).

## Backup / Restore – Problematische Archiv-Einträge

- Thema: Was bedeutet die rote Warnbox „Problematische Archiv-Einträge erkannt“?
- Hintergrund:
  - Das Backend analysiert das Archiv vor dem Entpacken und erkennt u. a.:
    - Pfad-Traversal (`../`), absolute Pfade, symbolische Links, Hardlinks, Geräte-Dateien.
  - Solche Einträge werden als `blocked_entries` zurückgemeldet.
- Darstellung in der UI:
  - Rote Warnbox innerhalb der Analyse-Box mit klarer Überschrift und Erklärung.
  - Liste der ersten problematischen Einträge zur Orientierung.
- Empfehlung:
  - Solche Backups nicht produktiv einspielen.
  - Stattdessen ein neues Backup mit aktueller Version von SetupHelfer erzeugen.

## Backup / Restore – Systemnahe Pfade

- Thema: Was bedeuten die „systemnahen Pfade“ in der Analyse?
- Hintergrund:
  - Das Backend markiert Einträge, die in typischen System- oder Benutzerpfaden liegen (z. B. `/etc`, `/home`, `/usr`), als `system_like_entries`.
  - Diese sind nicht automatisch gesperrt, können aber bei einem produktiven Restore sensible Bereiche betreffen.
- Darstellung in der UI:
  - Separate Box innerhalb der Analyse mit blauer Hervorhebung.
  - Hinweistext, dass diese Pfade systemrelevant sein können und besonders sorgfältig geprüft werden sollten.
- Empfehlung:
  - Inhalt und Herkunft des Backups prüfen, bevor ein zukünftiger Root-Restore überhaupt in Betracht gezogen wird.

## Backup / Restore – Was wurde in Phase 1 real getestet?

- Thema: Welche Teile des gehärteten Backup / Restore wurden in Phase 1 lokal geprüft?
- Technisch geprüfte Punkte:
  - Backend-Erreichbarkeit:
    - `/health` liefert `{"status":"ok"}` → Grundfunktion und Serverlauf geprüft.
  - Negativfall für Verify:
    - Aufruf von `/api/backup/verify` mit einem ungültigen Pfad (`/nonexistent/file.tar.gz`, `mode="basic"`).
    - Ergebnis: Saubere Fehlermeldung „Backup-Datei liegt außerhalb erlaubter Pfade“; zeigt, dass Pfadvalidierung aktiv ist.
- Nicht geprüfte Punkte (Stand Phase 1):
  - Erfolgreicher Preview-Restore mit realem Archiv und Anzeige der Analyse-Box (inkl. systemnaher und geblockter Einträge).
  - Erfolgreiche Basis- und Tiefenprüfung echter Backups (einschließlich verschlüsselter Archive mit gültigem Schlüssel).
  - Gezielte Tests mit beschädigten Archiven und absichtlich vorbereiteten problematischen Pfaden.
  - Vollständige UI-Interaktion im Browser (Restore-Tab, Auswahl, Modale) mit echtem Datenmaterial.
- Fazit für FAQ:
  - Abschnitt 1 definiert das fachliche und technische Verhalten (inkl. Analyse-UI und Deep-Verify).
  - Ein vollständiger Reality-Check mit produktionsnahen Backups bleibt ausdrücklich als nächster Schritt offen.

## Einsteigerführung & Begleiter (ab 1.3.9.0)

- **Zentrale Logik:** `frontend/src/beginner/moduleModel.ts` (ModuleId, ExperienceLevel, MODULE_DEFINITIONS, App-Store-Meta).
- **UI-Marker:** `frontend/src/beginner/BeginnerGuidanceMarker.tsx` – konsistente Badges in Navigation, Dashboard, Listen.
- **Panda-Bilder (Kontext):** `frontend/src/assets/pandas/*.png` (z. B. backup, cloud, install) – ergänzen zu `PandaCompanion` / Strips.
- **Nutzerdoku:** `docs/user/GUIDED_UX_AND_COMPANION.md`; in-App **Dokumentation** → Dashboard + FAQ (Erfahrungslevel, Begleiter, Einsteigerpfad).


