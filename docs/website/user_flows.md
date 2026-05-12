# Nutzerpfade – setuphelfer.de

_Ziel: Zentrale Nutzerpfade klar beschreiben, insbesondere für Einsteiger. Alle Pfade verbinden Website und PI-Installer ohne neue Funktionen zu erfinden._

---

## 1. Pfad: Anfänger → Startseite → versteht Projekt → lädt Installer

- **Ausgangssituation:**
  - Nutzer hat wenig bis keine Erfahrung mit Linux/Raspberry Pi.
  - Kommt über Suche, Empfehlung oder Link auf `setuphelfer.de`.

- **Schritte:**
  1. **Landing auf Home (`/`)**
     - Sieht Hero mit kurzem Claim („Dein Setup-Helfer für Raspberry Pi & Linux“), einem Screenshot und einem klaren „Download“-Button.
     - Kurze Erklärung in 2–3 Sätzen, was der PI-Installer macht (angelehnt an das README).
  2. **Scrollt zu „Vorteile“ / „Was macht der PI-Installer?“**
     - Liest 3–4 klar formulierte Vorteile (Sicherheit, Einsteigerführung, Projekte, Automatisierung).
  3. **Sieht Abschnitt „Erste Schritte“**
     - Einfache 3-Schritte-Erklärung (z. B. Pi vorbereiten, Installer beziehen, Oberfläche öffnen).
  4. **Klickt auf „Installer herunterladen“**
     - Wird auf `/download/` geleitet.
  5. **Auf `/download/`**
     - Sieht einen hervorgehobenen Abschnitt „Empfohlen für Einsteiger“ mit einem klar beschriebenen Installationsweg (gemäß README, z. B. Weg 1 oder .deb).
     - Sieht darunter weitere Optionen für Fortgeschrittene (Skript, Docker).
  6. **Optionaler Schritt: „Installationsanleitung lesen“**
     - Link von der Download-Seite zu einer Doku-/Tutorial-Seite, z. B. `/tutorials/kategorie/installation/` oder `/dokumentation/installation/`.

- **Zielzustand:**
  - Nutzer versteht:
    - Grundidee des Projekts.
    - Dass es sicherheitssensibel, aber einsteigerfreundlich ist.
  - Nutzer lädt den Installer über einen dokumentierten Weg herunter.

---

## 2. Pfad: Nutzer entdeckt Projekte → Projekt → versteht Nutzen → installiert mit PI-Installer

- **Ausgangssituation:**
  - Nutzer möchte wissen, „was man mit dem PI-Installer machen kann“.
  - Kommt über Home, Menü „Projekte“ oder einen Direktlink.

- **Schritte:**
  1. **Navigiert zu „Projekte“ (`/projekte/`)**
     - Sieht eine Raster-/Listenansicht mit Projektkarten:
       - Titel, kurze Beschreibung, Schwierigkeitsgrad, benötigte Hardware.
  2. **Filtert oder klickt spontan ein Projekt (z. B. „Media-Server“)**
     - Optionale Filter nach Kategorie/Schwierigkeit.
  3. **Auf der Projektdetailseite (`/projekte/<projekt-slug>/`)**
     - Liest:
       - „Was ist dieses Projekt?“ (Ziel/Nutzen).
       - „Was brauche ich?“ (Hardware, Vorwissen).
       - „Wie riskant/komplex ist das?“ (Difficulty-/Risk-Labels, basierend auf dokumentiertem Risikokonzept).
     - Sieht Verweise auf relevante Tutorials/Dokumentation.
  4. **Sieht CTA „Mit PI-Installer starten“**
     - Button-Link zurück auf `/download/`, ggf. mit Anker „Erste Schritte“.
  5. **Auf `/download/`**
     - Nutzer folgt dem bereits beschriebenen Download-Pfad.

- **Zielzustand:**
  - Nutzer versteht den Nutzen des konkreten Projekts.
  - Nutzer wird nicht mit Technik überladen, sondern Schritt für Schritt zum Installer geführt.

---

## 3. Pfad: Nutzer braucht Hilfe → Tutorials / Dokumentation / Community

- **Ausgangssituation:**
  - Nutzer hat den Installer bereits installiert oder ist mitten im Prozess.
  - Er stößt auf Fragen (z. B. Installation, Backup, Fehlermeldung).

- **Schritte:**
  1. **Nutzer kommt auf die Website (oder wechselt von einem in der App verlinkten Hilfeeintrag)**
     - Sieht in der Hauptnavigation „Tutorials“, „Dokumentation“ und „Community“.
  2. **Wählt je nach Problem:**
     - „Tutorials“ (`/tutorials/`) – für Schritt-für-Schritt-Anleitungen.
     - „Dokumentation“ (`/dokumentation/`) – für tiefergehende technische Hintergründe.
  3. **Auf `/tutorials/`**
     - Sucht ein Tutorial nach Kategorie (z. B. Installation, Sicherheit & Backup, Diagnose).
     - Öffnet das passende Tutorial, z. B. „Backup einrichten mit dem PI-Installer“.
  4. **ODER: Auf `/dokumentation/`**
     - Wählt den Themenbereich, z. B. „Backup & Restore“ oder „Diagnose & Logs“.
     - Liest eine sachliche, einsteigerorientierte Erklärung.
  5. **Wenn Fragen offen bleiben**
     - Am Ende jeder Tutorial-/Doku-Seite gibt es einen CTA:
       - „Frage in der Community stellen“.
     - Link führt auf `/community/` bzw. direkt in den passenden Forum-Bereich.

- **Zielzustand:**
  - Nutzer findet ohne Umwege:
    - Eine Anleitung (Tutorial).
    - Eine Hintergrundseite (Doku).
    - Einen Kanal für Fragen (Community).

---

## 4. Pfad: Nutzer will Community → Forum / Projekte / Fragen / Austausch

- **Ausgangssituation:**
  - Nutzer möchte sich austauschen, Erfahrungen teilen oder Fragen stellen.
  - Kommt über Menü „Community“, einen Link aus einer Seite oder direkt.

- **Schritte:**
  1. **Besucht `/community/`**
     - Sieht:
       - Eine kurze Erklärung, wofür die Community da ist.
       - Hinweise auf Verhaltensregeln.
       - Haupt-Einstiegspunkte: „Hilfe & Support“, „Projekte teilen“, „Ankündigungen“.
  2. **Klickt auf „Forum“ / passenden Bereich**
     - Wird auf `/community/forum/` weitergeleitet (später bbPress).
  3. **Im Forum (Konzept, später technisch über bbPress)**
     - Wählt den Bereich:
       - „Hilfe & Support“ – für Fragen zur Installation/Nutzung.
       - „Projekte teilen“ – um eigene Setups/Tutorials zu zeigen.
       - „Ankündigungen“ – nur zum Lesen von offiziellen Infos.
  4. **Stellt eine Frage oder teilt ein Projekt**
     - Nutzung der Forum-Funktionalität (Thema erstellen, antworten).

- **Zielzustand:**
  - Nutzer versteht, wo er Fragen stellen und Projekte teilen kann.
  - Community wird als Erweiterung der Website und des PI-Installers sichtbar, nicht als separates „Produkt“.

---

## 5. Selbstprüfung Phase 2 – Nutzerpfade

- **Ist die Website anfängerfreundlich?**
  - Ja: Alle wichtigen Einstiege (Home, Download, Tutorials, Doku, Community) sind in klaren Pfaden beschrieben, besonders aus Sicht von Einsteigern.
- **Ist die Architektur klar?**
  - Ja: Jeder Pfad nutzt die definierte Navigation ohne Sonderlogik oder versteckte Unterwelten.
- **Keine unnötigen Zusatzfunktionen eingebaut?**
  - Ja: Es werden nur Wege durch bestehende/konzipierte Seiten beschrieben, keine neuen Produktfeatures oder komplexe Systeme.

