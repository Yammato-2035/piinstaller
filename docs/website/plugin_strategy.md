# Plugin-Strategie – setuphelfer.de

_Ziel: Schlanke, kontrollierte Nutzung von Plugins für setuphelfer.de. Fokus auf Stabilität, Sicherheit und Wartbarkeit – keine Plugin-Flut._

---

## 1. Grundsätze

- So wenig Plugins wie möglich, so viele wie nötig.
- Keine Funktionsduplikate (z. B. mehrere Pagebuilder).
- Schwerpunkt auf:
  - Inhaltsmodellierung (CPTs, Felder, Taxonomien).
  - Community/Forum.
  - Sicherheit/Performance in vernünftigem Rahmen.

---

## 2. Kern-Plugins (empfohlen)

### 2.1 Custom Post Types & Felder

- **Advanced Custom Fields (ACF) oder vergleichbar**
  - Zweck:
    - Strukturierte Felder für Projekte, Tutorials, Doku-Einträge.
  - Einsatz:
    - Feldgruppen pro CPT (siehe `content_model.md`).

- **CPT-Registrierung**
  - Option A: CPTs im Theme/Child-Theme per Code registrieren (empfohlen).
  - Option B: Schlankes CPT-Plugin nur für Registrierung (falls Code im Theme nicht gewünscht).

### 2.2 Forum/Community

- **bbPress**
  - Zweck:
    - Forum-Struktur für Hilfe & Support, Projekte teilen, Ankündigungen.
  - Integration:
    - Community-Seite verlinkt auf Foren und Kategorien.

- **BuddyPress (optional, später)**
  - Nur einsetzen, wenn tatsächlich erweiterte Community-Funktionen (Profile, Gruppen, Stream) benötigt werden.

---

## 3. Unterstützende Plugins

### 3.1 Sicherheit

- Leichtgewichtiges Security-Plugin (z. B. Limit Login Attempts, grundlegende Hardening-Einstellungen).
- Keine tief eingreifenden Security-Suiten, die schwer durchschaubar sind, sofern nicht nötig.

### 3.2 Caching/Performance

- Einfaches Cache-Plugin (z. B. ein gängiger Page Cache).
- Konfiguration im Rahmen halten; zuerst saubere Umsetzung von Theme/Struktur, Performance dann feinjustieren.

### 3.3 SEO/Breadcrumbs (optional)

- Schlankes SEO-Plugin für:
  - Meta-Titel/-Beschreibungen.
  - Sitemap.
- Optionales Breadcrumb-Plugin, falls nicht im Theme integriert.

---

## 4. Was bewusst vermieden wird

- Kein visueller Mega-Pagebuilder als Hauptbasis (Elementor/Divi & Co.), um:
  - Performance und Wartbarkeit nicht zu gefährden.
  - Die Struktur (Hero, Karten, etc.) eher als saubere Templates im Theme abzubilden.
- Keine Mehrfach-Plugins für dieselbe Aufgabe (z. B. mehrere Cache- oder SEO-Plugins).
- Keine exotischen Plugins mit unklarer Wartungslage für zentrale Funktionen.

---

## 5. Theme-Strategie (kurz)

- Basis:
  - Eigenes schlankes Theme oder Child-Theme auf Basis eines stabilen Standardthemes.
- Umsetzung:
  - Visuelle Komponenten (Hero, Karten, Badges etc.) im Theme implementieren.
  - ACF-Felder im Template ausgeben, statt komplexe Pagebuilder-Konstrukte zu verwenden.

---

## 6. Migration / Updates

- Regelmäßige Updates:
  - WordPress-Core, Plugins und Theme aktualisieren – aber:
    - Vorher Backups.
    - Keine unnötigen, experimentellen Plugins hinzufügen.
- Dokumentation:
  - Jede Plugin-Installation und -Konfiguration kurz dokumentieren (separat, z. B. in einem Admin-Log oder internem Doc).

---

## 7. Selbstprüfung Phase 5 – Plugin-Strategie

- **WordPress-Struktur realistisch?**
  - Ja: Fokus auf ACF, bbPress und wenige, klar definierte Zusatzplugins.
- **Nicht überladen?**
  - Ja: Kein Pagebuilder-Zoo, keine Mehrfach-Plugins für gleiche Aufgaben.
- **Community sinnvoll eingeordnet?**
  - Ja: bbPress als Kern, BuddyPress nur als optionale spätere Erweiterung.

