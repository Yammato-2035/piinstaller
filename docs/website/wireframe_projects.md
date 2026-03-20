# Wireframe – Projekte (Übersichtsseite)

_Ziel: Besuchern zeigen, welche Anwendungsszenarien mit dem PI-Installer möglich sind, und sie zu passenden Projektdetailseiten führen._

---

## Seitenziel

- Projekte als Inspiration und Einstiegspunkte präsentieren.
- Klar machen:
  - Welche Arten von Projekten es gibt.
  - Welche Anforderungen und Schwierigkeitsgrade sie haben.
- Brücke zur Installation:
  - Von Projekten zur Download-/Erste-Schritte-Seite führen.

---

## Sektionen (Reihenfolge)

1. Einleitung / Hero light
2. Filter- und Kategorieleiste
3. Projektliste (Kartenraster)
4. Hinweise zu Schwierigkeit & Risiko
5. CTA zu Download und Tutorials

---

## 1. Einleitung / Hero light

- **Inhalt:**
  - Titel: „Projekte mit dem PI-Installer“.
  - Kurzer Einleitungstext:
    - „Hier findest du Beispiele, was du mit dem PI-Installer auf deinem Raspberry Pi umsetzen kannst.“

- **Komponenten:**
  - Überschrift.
  - Kurzer Text.

---

## 2. Filter- und Kategorieleiste

- **Inhalt (UI-Ebene):**
  - Dropdowns/Chips für:
    - Kategorie (Server & Dienste, Smart Home, Multimedia, Lernen & Experimente, …).
    - Schwierigkeit (Anfänger, Fortgeschritten, Experte).
    - Hardware (Pi 4, Pi 5, NVMe, etc.).
- **Hinweis für Einsteiger:**
  - Kleiner Text z. B.: „Wenn du neu bist, starte mit Projekten auf Anfänger-Niveau.“

- **Komponenten:**
  - Filter-Leiste (UI-Konzept).
  - Difficulty-/Risk-Badges als Legende.

---

## 3. Projektliste (Kartenraster)

- **Inhalt:**
  - Raster mit Projektkarten.
  - Jede Projektkarte zeigt:
    - Titel.
    - Kurzbeschreibung.
    - Difficulty-Badge.
    - Risk-Badge (falls sinnvoll).
    - Kategorie(n) / Hardwarekurzinfo.
  - Optional kleines Icon/Illustration je Projekt.

- **Interaktion:**
  - Klick auf Karte → Projektdetailseite (`/projekte/<slug>/`).

- **Komponenten:**
  - Projektkarten.
  - Difficulty-/Risk-Badges.

---

## 4. Hinweise zu Schwierigkeit & Risiko

- **Inhalt:**
  - Kurze Erklärung:
    - Was bedeuten „Anfänger“, „Fortgeschritten“, „Experte“?
    - Was bedeuten Risiko-Stufen (niedrig/mittel/hoch) im Kontext PI-Installer?
  - Optional mit kleinen Status-/Risk-Icons.

- **Nutzen:**
  - Einsteiger verstehen, welche Projekte für sie geeignet sind.

- **Komponenten:**
  - Hinweisboxen.
  - Status-/Difficulty-Badges als Beispiel.

---

## 5. CTA zu Download und Tutorials

- **Inhalt:**
  - Text:
    - „Du hast ein Projekt gefunden, das dir gefällt?“
  - CTAs:
    - „Installer herunterladen“ (→ `/download/`).
    - „Erste Schritte mit dem Installer“ (→ Einsteiger-Tutorial).

- **Komponenten:**
  - Download-Box (klein, eingebettet).
  - Buttons.

---

## CTA pro Sektion (Übersicht)

- Einleitung: keine starke CTA, nur Orientierung.
- Filterleiste: indirekter CTA („Projekte nach deinen Bedürfnissen filtern“).
- Projektliste: „Projekt ansehen“ (Klick auf Karte).
- Hinweisbereich: ggf. Link „Mehr zu Sicherheit & Risiko“ (→ Doku).
- Abschluss: „Installer herunterladen“, „Erste Schritte lesen“.

---

## Selbstprüfung – Projekte-Übersicht

- **Seite verständlich?**
  - Ja: erklärt Ziel der Seite und Bedeutung von Difficulty/Risk.
- **Einsteigerführung sichtbar?**
  - Ja: Hinweise für Einsteiger, klare Legende, CTAs zu Download/Erste Schritte.
- **Projekte ausreichend präsent?**
  - Ja: Projektkarten als zentraler Inhalt, Filter erleichtern Orientierung.

