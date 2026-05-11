# Template: Tutorialseite – setuphelfer.de

_Ziel: Einheitliche Struktur für Tutorials. Schritt-für-Schritt-Anleitungen, die Einsteiger sicher durch Aufgaben mit dem PI-Installer führen._

---

## Metadaten

- **Titel (`title`)**  
  Beispiel: `PI-Installer installieren und erste Schritte`

- **Slug (`slug`)**  
  URL-Bestandteil, z. B. `pi-installer-installation-erste-schritte`.

- **Kurzbeschreibung (`short_description`)**  
  1–2 Sätze, was der Nutzer nach Abschluss kann.

- **Schwierigkeit (`difficulty`)**  
  `Anfänger` | `Fortgeschritten` | `Experte`.

- **Geschätzte Dauer (`estimated_time`)**  
  z. B. `15 Minuten`, `30–45 Minuten`.

- **Kategorien (`categories`)**  
  z. B. `Installation`, `Sicherheit & Backup`, `Projekte`, `Diagnose`.

- **Tags (`tags`)**  
  Freie Schlagwörter (z. B. „Backup“, „Docker-Test“, „Mailserver“).

- **Voraussetzungen (`prerequisites`)**  
  Stichpunkte (z. B. „Raspberry Pi ist mit Raspberry Pi OS installiert“, „Zugriff per SSH“).

- **Benötigte Hardware (`required_hardware`)**  
  Liste (z. B. „Raspberry Pi 4“, „32GB SD-Karte“, „Netzwerkkabel“).

---

## Seitenaufbau

### 1. Einleitung

- Kurze Erklärung:
  - Was wird erreicht?
  - Für wen ist das Tutorial geeignet?
  - Hinweis, falls ein Projekt oder anderes Tutorial sinnvoll vorher kommt.

### 2. Übersicht der Schritte

- Liste aller Hauptschritte (nur Überschriften), z. B.:
  1. Raspberry Pi vorbereiten
  2. PI-Installer herunterladen
  3. Installation ausführen
  4. Oberfläche öffnen und prüfen

### 3. Schritt-für-Schritt (Steps)

Für jeden Schritt:

- **Step-Titel**
- **Beschreibung** (in kleiner, verständlicher Sprache).
- **Aktionen** (Aufzählungspunkte).
- **Optional:**
  - Codeblöcke (z. B. SSH-Befehle).
  - Screenshots.
  - Hinweisboxen:
    - Info (z. B. Tipp).
    - Warnung (z. B. „Achtung: Backup vor Änderungen…“).
    - Sicherheit (z. B. Bezug auf Security-Konzept, LAN/VPN-Empfehlung).

### 4. Ergebnis / Abschluss

- Kurze Beschreibung:
  - Woran erkennt der Nutzer, dass alles geklappt hat?
  - Was kann er jetzt tun (z. B. nächstes Tutorial, Projektseite)?

### 5. Weiterführende Links

- Verknüpfte Projekte:
  - Liste mit Projekten, für die dieses Tutorial relevant ist.
- Verknüpfte Doku-Seiten:
  - z. B. „Netzwerkzugriff“, „Backup & Restore“.
- Hinweise auf weitere Tutorials:
  - z. B. „Nächstes Tutorial: Backup einrichten“.

### 6. Community-CTA

- Kurzer Abschnitt:
  - „Fragen oder Probleme?“
  - Link zur Community/Forum:
    - Möglichst direkt in passende Kategorie (z. B. „Installation & Setup“).

---

## Selbstprüfung – Tutorialseite

- **Einsteigerfreundlich?**
  - Schritte sind klar benannt, keine unnötigen Fachbegriffe ohne Erklärung.
- **Klarer Fortschritt?**
  - Nutzer sieht zu Beginn, was auf ihn zukommt (Schrittübersicht).
- **Keine neue Produktlogik erfunden?**
  - Ja, alle Schritte basieren auf bestehenden Installationswegen und Doku; keine imaginären Installer-Funktionen.

