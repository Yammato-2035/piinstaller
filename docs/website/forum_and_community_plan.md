# Forum- und Community-Plan – setuphelfer.de

_Ziel: Klare, anfängerfreundliche Community-Struktur rund um PI-Installer, ohne eine überdimensionierte Social-Plattform zu bauen. Fokus auf Hilfe, Austausch und Projektinspiration._

---

## 1. Rolle der Community

- **Funktionen:**
  - Fragen stellen und Hilfe bekommen (Installation, Nutzung, Probleme).
  - Eigene Projekte teilen und andere inspirieren.
  - Offizielle Ankündigungen des Projekts lesen.
- **Abgrenzung:**
  - Community ergänzt Website und Doku – sie ersetzt keine offizielle Dokumentation.
  - Kein allgemeines „Linux-Forum“, sondern klar PI-Installer-zentriert.

---

## 2. Technische Basis

- **Forum:** bbPress.
- **Optionale Erweiterung:** BuddyPress (später, falls nötig), z. B. für Profile, Gruppen, Activity Streams.
- **Integration:**
  - WordPress verwaltet Seiten, CPTs und Menüs.
  - bbPress stellt Foren/Topics/Replies bereit.

---

## 3. Forenstruktur (Startversion)

### 3.1 Hauptbereiche

1. **Hilfe & Support**
   - Zweck:
     - Fragen zu Installation, Konfiguration und Nutzung des PI-Installers.
   - Unterforen (optional):
     - Installation & erste Schritte.
     - Projekte & Presets.
     - Fehler & Diagnose.

2. **Projekte teilen**
   - Zweck:
     - Nutzer posten ihre Setups und Erfahrungen mit Projekten.
   - Inhalt:
     - Kurze Beschreibungen, Screenshots, ggf. Links zu Tutorials oder externen Repos.

3. **Ankündigungen**
   - Zweck:
     - Nur für offizielle Projektmeldungen (Releases, wichtige Hinweise).
   - Besonderheit:
     - Schreibrechte nur für Projektteam (Admins/Moderatoren).

### 3.2 Zusätzliche Bereiche (optional, später)

- „Ideen & Vorschläge“ – Feature-Ideen, die diskutiert werden können.
- „Off-Topic“ – nur falls eine klare Nachfrage besteht, ansonsten vermeiden.

---

## 4. Einstiegspunkte von der Website

- **Community-Startseite (`/community/`):**
  - Erklärt kurz:
    - Wofür die Community da ist.
    - Wie man eine gute Frage stellt.
    - Wo man Projekte teilt.
  - Enthält Karten/Links zu:
    - Hilfe & Support.
    - Projekte teilen.
    - Ankündigungen.

- **Von Projekten/Tutorials/Doku aus:**
  - Am Ende jeder Seite:
    - CTA „Frage stellen“:
      - Link zu passendem Forum-Bereich (z. B. „Installation & erste Schritte“).
    - CTA „Erfahrungen teilen“:
      - Link zu „Projekte teilen“.

---

## 5. Rollen & Moderation (Community-spezifisch)

- **Rollen (bbPress/BuddyPress):**
  - Keymaster/Administrator:
    - Vollzugriff, Struktur und Rechteverwaltung.
  - Moderator:
    - Beiträge moderieren, Themen verschieben/schließen.
  - Teilnehmer (Standardnutzer):
    - Themen erstellen, antworten.

- **Moderationsprinzipien:**
  - Klare, einfache Regeln:
    - Freundlicher Umgangston.
    - Keine sicherheitsgefährdenden Anleitungen (z. B. „öffentlicher Zugriff ohne Schutz“).
    - Keine Werbung/Spam.
  - Moderation eher erklärend als strafend.

---

## 6. Verbindung zu Dokumentation und GitHub

- **Doku ↔ Forum:**
  - Doku-Seiten verlinken auf zugehörige Forenbereiche („Fragen dazu? Hier entlang…“).
  - Forum-Threads können bei Bedarf auf relevante Doku-Artikel/Tutorials verweisen.

- **GitHub ↔ Forum:**
  - Für Bugreports und Feature-Requests:
    - Empfehlung, GitHub-Issues zu nutzen (Link in Community-Bereich).
  - Forum dient eher Nutzerfragen und Erfahrungsaustausch, nicht als Issue-Tracker-Ersatz.

---

## 7. Wachstumsplan (Community)

- **Phase 1 – Minimalbetrieb:**
  - Nur drei Hauptbereiche:
    - Hilfe & Support.
    - Projekte teilen.
    - Ankündigungen.

- **Phase 2 – Feintuning:**
  - Falls viele Themen in bestimmten Bereichen entstehen:
    - Unterforen nach Kategorien (z. B. Projekte nach Typ).

- **Phase 3 – Erweiterung (optional):**
  - Einsatz von BuddyPress, wenn:
    - Bedarf an Nutzerprofilen/Projektprofilen besteht.
    - Mehr Community-Funktionen sinnvoll sind.

---

## 8. Selbstprüfung Phase 5 – Forum/Community

- **WordPress-Struktur realistisch?**
  - Ja: bbPress als Forum, WordPress-Pages als Einstieg, BuddyPress nur optional.
- **Nicht überladen?**
  - Ja: Start mit wenigen, klaren Bereichen, optionaler Ausbau bei Bedarf.
- **Community sinnvoll eingeordnet?**
  - Ja: Unterstützung von Projekten, Tutorials und Doku; keine konkurrierende Parallelwelt.

