# Informationsarchitektur – setuphelfer.de

_Ziel: Klare, anfängerfreundliche Struktur für die Website als Plattform rund um PI-Installer, Linux-Einstieg, Raspberry-Pi-Projekte, Tutorials, Community und Dokumentation._

Top-Level-Navigation:
- Home
- Projekte
- Tutorials
- Community
- Download
- Dokumentation
- Über SetupHelfer

---

## 1. Home

- **Ziel:**
  - Besucher (insbesondere Einsteiger) verstehen in wenigen Sekunden:
    - Was der PI-Installer ist.
    - Für wen er gedacht ist.
    - Was sie damit konkret tun können.
    - Wo sie den Installer sicher herunterladen und wie sie starten.

- **Zielgruppe:**
  - Einsteiger mit wenig Linux-/Raspberry-Pi-Erfahrung.
  - Fortgeschrittene Nutzer, die schnell zum Download und zur Übersicht wollen.

- **Inhalt (Hauptelemente):**
  - Hero-Bereich mit:
    - Kurzem Claim („Dein Setup-Helfer für Raspberry Pi & Linux“).
    - Screenshot oder Illustration des Dashboards.
    - Primärem CTA „Installer herunterladen“.
  - Kurzvorstellung PI-Installer:
    - 3–4 Kernvorteile (Sicherheit, Einsteigerführung, Projekte, Automatisierung).
  - Beispielprojekte:
    - Kleiner Teaser von 3–6 Projekten (Media-Server, Smart Home, NAS, etc.).
  - Erste Schritte:
    - Sehr einfache 3-Schritte-Erklärung „So startest du“.
  - Community-Teaser:
    - Hinweis auf Forum / Community-Bereich.

- **Unterseiten:**
  - Keine technischen Unterseiten, aber der Home-Bereich verlinkt stark auf:
    - „Projekte“, „Tutorials“, „Download“, „Dokumentation“, „Community“.

- **Call-to-Actions (CTAs):**
  - Primär: „Installer herunterladen“ (Link auf Download-Seite).
  - Sekundär:
    - „Projekte entdecken“ (Link auf Projekte-Übersicht).
    - „Erste Schritte lesen“ (Link auf passenden Doku-/Tutorial-Einstieg).
    - „Community beitreten“ (Link auf Community-Seite).

- **Verbindung zum PI-Installer:**
  - Visual: Screenshots, Icons, Farbwelt des Installers.
  - Inhaltlich: Kurzbeschreibung, die den Installer so erklärt, wie im README dokumentiert (kein neues Featureversprechen).

---

## 2. Projekte

- **Ziel:**
  - Zeigen, was man mit dem PI-Installer praktisch machen kann.
  - Projekte als Einstiegspunkte („Ich will einen Media-Server“, „Ich will ein NAS“, …).
  - Brücke schlagen zwischen „Idee“ und „Installer-Realität“ (Projekte/Preset-Konzepte aus der App).

- **Zielgruppe:**
  - Einsteiger, die Inspiration suchen („Was kann ich mit meinem Pi machen?“).
  - Fortgeschrittene, die konkrete Setup-Ideen vergleichen möchten.

- **Inhalt:**
  - Projektübersicht:
    - Kacheln/Karten mit Titel, Kurzbeschreibung, Schwierigkeitsgrad, benötigte Hardware, Kategorie.
  - Projektkategorien:
    - z. B. „Server & Dienste“, „Smart Home“, „Multimedia“, „Lernen & Experimentieren“.
  - Einzelne Projektseiten:
    - Detaillierte Beschreibung (Ziel, Nutzen, Voraussetzungen, Risiko/Sicherheitsaspekte).
    - Optional: Verbindung zu Tutorials und Doku, die das Setup erklären.

- **Unterseiten:**
  - `/projekte/` – Übersicht mit Filtern (Kategorie, Schwierigkeit, Hardware).
  - `/projekte/kategorie/<slug>/` – Kategorieansichten.
  - `/projekte/<projekt-slug>/` – Projektdetailseiten.

- **Call-to-Actions:**
  - Auf Übersicht:
    - „Projekt ansehen“.
    - Filteroptionen (kein technisches Feature, nur UI-Sicht).
  - Auf Projektdetail:
    - „Mit PI-Installer starten“ (führt zur Download-/Erste-Schritte-Seite).
    - „Passende Tutorials anzeigen“.
    - „Fragen im Forum stellen“ (Link zur Community).

- **Verbindung zum PI-Installer:**
  - Klarer Hinweis: Projekte sind mit dem PI-Installer leichter aufsetzbar.
  - Wo die App bereits Presets/Module für den Bereich hat, wird dies erwähnt (ohne neue Module zu erfinden).

---

## 3. Tutorials

- **Ziel:**
  - Schritt-für-Schritt-Anleitungen für typische Aufgaben:
    - Installation des Installers.
    - Basis-Konfiguration.
    - Konkrete Teilaufgaben (Backup einrichten, Diagnose nutzen, etc.).
  - Einsteiger Schritt für Schritt abholen, ohne sie zu überfordern.

- **Zielgruppe:**
  - Einsteiger und leicht Fortgeschrittene.
  - Nutzer, die gezielte Aufgaben lösen wollen.

- **Inhalt:**
  - Tutorial-Übersicht:
    - Liste/Kacheln mit Titel, Kurzbeschreibung, Level (Anfänger/Fortgeschritten/Experte), Dauer, benötigte Hardware.
  - Tutorial-Kategorien:
    - z. B. „Installation & Erste Schritte“, „Sicherheit & Backup“, „Projekte aufsetzen“, „Fehlersuche & Diagnose“.
  - Einzelne Tutorials:
    - Klar strukturierter Ablauf mit Schritten, Screenshots, Hinweisboxen/Warnings.

- **Unterseiten:**
  - `/tutorials/` – Übersicht, filterbar nach Kategorie, Schwierigkeit, Thema.
  - `/tutorials/kategorie/<slug>/`.
  - `/tutorials/<tutorial-slug>/`.

- **Call-to-Actions:**
  - Auf Übersicht:
    - „Tutorial ansehen“.
  - In Tutorials:
    - „Installer installieren“ (falls noch nicht geschehen).
    - „Projektseite anzeigen“ (falls Tutorial zu einem Projekt gehört).
    - „Fragen in der Community stellen“.

- **Verbindung zum PI-Installer:**
  - Tutorials zeigen echte Workflows mit dem Installler (Installationsschritte, Module, Diagnose).
  - Keine neuen Funktionen – nur das, was im Installer bereits vorhanden oder in der Doku dokumentiert ist.

---

## 4. Community

- **Ziel:**
  - Einstieg in die Community rund um PI-Installer und Raspberry-Pi-/Linux-Projekte.
  - Zukünftige Integration von Forum (bbPress) und ggf. später BuddyPress.
  - Ermöglichen von Fragen, Austausch, Teilen von Projekten.

- **Zielgruppe:**
  - Nutzer mit Fragen.
  - Nutzer, die eigene Projekte teilen wollen.
  - Langfristig auch fortgeschrittene Nutzer/Contributors.

- **Inhalt:**
  - Community-Startseite:
    - Erklärung des Community-Zwecks.
    - Hinweise auf Verhaltensregeln, Einstiegspunkte.
  - Forum-Bereiche (konzeptuell):
    - Hilfe & Support (z. B. „Installation“, „Fehlersuche“, „Projekte“).
    - Projektvorstellungen.
    - Ankündigungen (Read-only, vom Projekt).

- **Unterseiten:**
  - `/community/` – Startseite.
  - `/community/forum/` – Einstieg ins Forum (später durch bbPress).
  - Unterforen/Topics werden technisch durch Forum-Software verwaltet; konzeptuell in Doku beschrieben.

- **Call-to-Actions:**
  - „Frage stellen“ (führt in den passenden Forum-Bereich).
  - „Projekt teilen“.
  - „Regeln & Leitfaden lesen“.

- **Verbindung zum PI-Installer:**
  - Community explizit als Anlaufstelle für Nutzerfragen rund um den Installer, seine Projekte und Linux-Einstieg.
  - Kein neues Produktfeature – nur organisatorische Struktur.

---

## 5. Download

- **Ziel:**
  - Zentraler, klarer und sicherer Einstiegspunkt für den Download des PI-Installers.
  - Alle unterstützten Installationswege an einem Ort, aber anfängerfreundlich erklärt.

- **Zielgruppe:**
  - Alle Nutzer, primär Einsteiger.

- **Inhalt:**
  - Installer-Download:
    - Verlinkung auf GitHub-Releases (.deb, Skript).
    - Hinweise zu Hash-Prüfung (SHA256SUMS).
  - Systemanforderungen:
    - Pi-Modell, RAM, Speicher, OS (bereits in README dokumentiert).
  - Screenshots:
    - Ein erster Eindruck der Oberfläche.
  - Erste Schritte nach Installation:
    - Kurze Checkliste, was nach der Installation zu tun ist.

- **Unterseiten:**
  - `/download/` – Einzelne Seite, strukturiert nach „Empfohlen für Einsteiger“ und „Optionen für Fortgeschrittene“.

- **Call-to-Actions:**
  - „Download für Einsteiger“ (führt zum empfohlenen Weg, basierend auf README).
  - „Alle Installationsoptionen anzeigen“ (weiter unten auf derselben Seite).
  - „Installationsanleitung lesen“ (Link zur Doku).

- **Verbindung zum PI-Installer:**
  - Verwendet exakt die in README und Doku beschriebenen Installationswege; nichts Neues erfinden.

---

## 6. Dokumentation

- **Ziel:**
  - Zentrale, strukturierte Anlaufstelle für alle technischen Inhalte.
  - Brücke zwischen bestehenden Markdown-Dokumenten im Repo und einer einsteigerfreundlichen Web-Darstellung.

- **Zielgruppe:**
  - Fortgeschrittene Einsteiger.
  - Power-User und Admins.

- **Inhalt:**
  - Themenbereiche:
    - Installationshilfe.
    - Backup & Restore.
    - Docker.
    - Mailserver.
    - Diagnose & Logs.
    - Netzwerkzugriff.
  - Jede Seite referenziert passende Markdown-Dokumente aus dem Repo (ggf. in vereinfachter Form).

- **Unterseiten (Beispiele, analog zur Vorgabe):**
  - `/dokumentation/installation/`
  - `/dokumentation/backup/`
  - `/dokumentation/docker/`
  - `/dokumentation/mailserver/`
  - `/dokumentation/diagnose/`
  - `/dokumentation/allgemein/`

- **Call-to-Actions:**
  - „Tutorial dazu lesen“ (Verweis auf Tutorials).
  - „Projekt dazu ansehen“ (wenn relevant).
  - „Frage im Forum stellen“.

- **Verbindung zum PI-Installer:**
  - Nutzt und spiegelt vorhandene Doku (keine neuen Features).
  - Betont Best Practices (z. B. Nutzung im LAN, VPN-Empfehlung).

---

## 7. Über SetupHelfer

- **Ziel:**
  - Projekt, Motivation, Philosophie und Roadmap transparent machen.
  - Vertrauen schaffen – insbesondere für Einsteiger, die ein „Sicherheits-Tool“ installieren.

- **Zielgruppe:**
  - Alle Nutzer, insbesondere sicherheitsbewusste Anwender und Entscheidungsträger (z. B. in kleinen Organisationen).

- **Inhalt:**
  - Mission:
    - Einsteigerfreundlicher Einstieg in Linux/Raspberry Pi, ohne Sicherheitsaspekte zu vernachlässigen.
  - Philosophie:
    - Transparenz, Prüfbarkeit (Open Source), Fokus auf Sicherheit und Best Practices.
  - Zielgruppe:
    - Einsteiger, Maker, kleine Unternehmen, Lernumgebungen.
  - Roadmap:
    - Grober Überblick, angelehnt an bestehende `FEATURES.md`/Roadmap-Dokumente.

- **Unterseiten:**
  - `/ueber/` – ggf. mit Ankern für Mission, Philosophie, Roadmap.

- **Call-to-Actions:**
  - „Projekt auf GitHub ansehen“.
  - „Mitmachen / beitragen“ (Verweis auf CONTRIBUTING).
  - „Community besuchen“.

- **Verbindung zum PI-Installer:**
  - Stellt klar, dass SetupHelfer/Website die Plattform rund um den Installer ist.
  - Keine neuen Produktversprechen; stattdessen Verweis auf reale Features.

---

## 8. Selbstprüfung Phase 2 – Informationsarchitektur

- **Ist die Website anfängerfreundlich?**
  - Ja: Klare Einstiegsseiten (Home, Download, Tutorials) mit Fokus auf „Verstehen → Laden → Starten“.
- **Ist die Architektur klar?**
  - Ja: Top-Level-Navigation ist thematisch sauber getrennt (Projekte, Tutorials, Community, Download, Dokumentation, Über).
- **Keine unnötigen Zusatzfunktionen eingebaut?**
  - Ja: Es werden nur Strukturen beschrieben, die auf bestehenden Inhalten und geplanten Assets beruhen; keine neuen Produktfunktionen.

