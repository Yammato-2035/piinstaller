# Template: Projektseite – setuphelfer.de

_Ziel: Einheitliche Struktur für Projektdetailseiten. WordPress-tauglich (CPT „Projekt“), klar für Einsteiger, verknüpft mit Tutorials, Doku und Community._

---

## Metadaten

- **Titel (`title`)**  
  Beispiel: `Media-Server mit Raspberry Pi`

- **Kurzbeschreibung (`short_description`)**  
  1–2 Sätze, was das Projekt macht und für wen es gedacht ist.

- **Slug (`slug`)**  
  URL-Bestandteil, z. B. `media-server`.

- **Schwierigkeit (`difficulty`)**  
  Eine von: `Anfänger` | `Fortgeschritten` | `Experte`.

- **Risiko (`risk_level`)**  
  Eine von: `niedrig` | `mittel` | `hoch` (angelehnt an dokumentiertes Risk-System).

- **Kategorien (`categories`)**  
  z. B. `Server & Dienste`, `Smart Home`, `Multimedia`, `Lernen & Experimente`.

- **Hardware-Anforderungen (`hardware_requirements`)**  
- **Software-Anforderungen (`software_requirements`, optional)**  
- **Geschätzte Dauer (`estimated_time`, optional)**  

---

## Seitenaufbau

### 1. Einleitung

- **Abschnitt: „Was ist dieses Projekt?“**
  - Kurzbeschreibung aus Nutzerperspektive:
    - Welches Problem löst das Projekt?
    - Welchen Nutzen hat der Nutzer?

### 2. Voraussetzungen

- **Abschnitt: „Was brauchst du dafür?“**
  - Hardwareliste in einfacher Sprache.
  - ggf. Hinweis auf notwendiges Vorwissen (z. B. „Grundkenntnisse im Umgang mit dem Pi“).
  - Difficulty- und Risk-Badges visuell hervorgehoben.

### 3. Wie hilft der PI-Installer?

- **Abschnitt: „Was übernimmt der PI-Installer für dich?“**
  - Hochlevel-Beschreibung, welche Teile des Setups der Installer vereinfacht:
    - z. B. „Basis-Konfiguration“, „Sicherheitssetup“, „Installation bestimmter Dienste“.
  - Keine neuen Funktionen erfinden – nur das beschreiben, was in README/Doku vorgesehen ist.

### 4. Ablauf-Überblick

- **Abschnitt: „So läuft das Setup ab“**
  - 3–7 Schritte in Stichpunkten (hochlevelig, kein Tutorial-Ersatz).
  - Verweis auf ein oder mehrere konkrete Tutorials für die Details.

### 5. Screenshots / Illustrationen

- **Abschnitt: „So sieht es aus“**
  - 1–3 Screenshots oder Illustrationen:
    - z. B. Dashboard-Ansicht, relevante Module, Ergebnisansicht.
  - Verweis auf gemeinsame Asset-Ordner (Icons/Illustrationen/Screenshots).

### 6. Verknüpfte Inhalte

- **Abschnitt: „Weiterführende Hilfe“**
  - Liste verknüpfter Tutorials:
    - Titel + kurzer Satz, was im Tutorial passiert.
  - Liste verknüpfter Doku-Seiten:
    - z. B. „Backup & Restore“, „Diagnose & Logs“.

### 7. Community-CTA

- **Abschnitt: „Fragen? Erfahrungen teilen?“**
  - Kurzer Text, der auf die Community verweist.
  - Button/Link zu passendem Forum-Bereich (Hilfe oder Projekte teilen).

---

## Selbstprüfung – Projektseite

- **Einsteigerfreundlich?**
  - Nutzen und Voraussetzungen sind in einfacher Sprache erklärt.
- **Verknüpfung mit PI-Installer klar?**
  - Ja, der Installer wird als Werkzeug erklärt, nicht als Blackbox.
- **Keine neue Produktlogik erfunden?**
  - Ja, nur beschriebene/naheliegende Funktionen genutzt, angelehnt an vorhandene Doku.

