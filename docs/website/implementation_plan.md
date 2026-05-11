# Umsetzungsplan – setuphelfer.de

_Ziel: Realistischen, in Etappen gegliederten Plan für die Umsetzung der Website auf Basis der bestehenden Konzepte und der WordPress‑Architektur definieren._

---

## Etappe 1 – Struktur und Dokumentation

- **Ziel**
  - Vollständige konzeptionelle Grundlage schaffen: Informationsarchitektur, Seitenbaum, Content‑Modelle, visuelles System, WordPress‑Architektur, Community‑Plan.
- **Abhängigkeiten**
  - Keine technischen Voraussetzungen – basiert rein auf vorhandener Projekt‑Doku und Designunterlagen.
- **Risiken**
  - Gering: rein dokumentarische Arbeiten.
- **Ergebnis**
  - Alle Dateien unter `docs/website/` und `website/content/` liegen vor und können als Referenz für weitere Schritte genutzt werden.

---

## Etappe 2 – WordPress‑Grundsystem

- **Ziel**
  - Saubere Grundinstallation von WordPress für `setuphelfer.de`, inkl. SSL, Basis‑Security und Backups.
- **Abhängigkeiten**
  - Serverzugang (Plesk/SSH).
  - Bestehendes Zertifikat und funktionierende Domain.
- **Risiken**
  - Falsch konfigurierte Plugins oder Themes können Performance und Sicherheit beeinträchtigen.
- **Ergebnis**
  - Aktuelles WordPress mit minimalem, stabilen Theme (oder Child‑Theme), wenigen Kern‑Plugins (ACF, bbPress, Basis‑Security, Cache).

---

## Etappe 3 – Theme / Designbasis

- **Ziel**
  - Visuelle Basis analog zum PI‑Installer schaffen: Farbwelt, Typografie, Karten‑ und Buttonstile, Header/Footer‑Layout.
- **Abhängigkeiten**
  - Fertige Konzepte aus `visual_system.md`, `component_patterns.md`, `branding_usage.md`.
  - WordPress‑Grundsystem aus Etappe 2.
- **Risiken**
  - Zu starke Abhängigkeit von komplexen Pagebuildern; Gefahr eines schwer wartbaren Themes.
- **Ergebnis**
  - Eigenes (Child‑)Theme oder angepasstes Basistheme, das:
    - das Hauptmenü gemäß `navigation_structure.md` abbildet,
    - Grundkomponenten wie Hero‑Bereich, Karten, Badges und Hinweisboxen bereitstellt.

---

## Etappe 4 – Kernseiten

- **Ziel**
  - Zentrale statische Seiten aufsetzen:
    - Home.
    - Download.
    - Community‑Start.
    - Dokumentation‑Übersicht.
    - Über SetupHelfer.
- **Abhängigkeiten**
  - Theme/Designbasis (Etappe 3).
  - Inhalte aus `website/content/*.md`.
- **Risiken**
  - Inkonsistente Übernahme der Texte, falls Änderungen im Repo nicht nachgezogen werden.
- **Ergebnis**
  - Kernseiten sind in WordPress als Pages angelegt, strukturiert nach den Wireframes (`wireframe_*.md`) und mit den vorbereiteten Inhalten befüllt.

---

## Etappe 5 – Projektbibliothek

- **Ziel**
  - Custom Post Type „Projekt“ und zugehörige Taxonomien/Felder umsetzen.
- **Abhängigkeiten**
  - ACF (oder vergleichbares Feld‑Plugin).
  - Definitionen aus `content_model.md`, `project_template.md`, `wordpress_architecture.md`.
- **Risiken**
  - Zu komplexe Feldstrukturen können die Redaktion erschweren.
- **Ergebnis**
  - CPT „Projekt“ existiert.
  - Archivseite `/projekte/` und Projektdetailseiten folgen den Wireframes.
  - Erste exemplarische Projekte können angelegt und getestet werden.

---

## Etappe 6 – Tutorials

- **Ziel**
  - Custom Post Type „Tutorial“ inkl. Schrittstruktur umsetzen.
- **Abhängigkeiten**
  - Umsetzung von Etappe 5 (gemeinsame Taxonomien).
  - Definitionen aus `content_model.md`, `tutorial_template.md`.
- **Risiken**
  - Unübersichtliche Schrittverwaltung, wenn das Feldsetup nicht sauber gestaltet ist.
- **Ergebnis**
  - CPT „Tutorial“ existiert.
  - Archivseite `/tutorials/` und Tutorialdetailseiten orientieren sich an den vereinbarten Wireframes.
  - Verknüpfungen zwischen Projekten, Tutorials und Doku sind möglich.

---

## Etappe 7 – Dokumentation

- **Ziel**
  - Doku‑Einträge in WordPress strukturiert abbilden und mit bestehenden Markdown‑Dokumenten verknüpfen.
- **Abhängigkeiten**
  - CPT „Dokumentationseintrag“ aus `content_model.md` / `wordpress_architecture.md`.
  - Bestehende Doku im Repo.
- **Risiken**
  - Doppelpflege, wenn Textpassagen unkoordiniert sowohl im Repo als auch in WordPress geändert werden.
- **Ergebnis**
  - Themenbasierte Doku‑Seiten (Installation, Backup, Docker, Mailserver, Diagnose, Allgemeines).
  - Klare Links auf die zugrundeliegenden Markdown‑Dokumente, ohne diese zu duplizieren.

---

## Etappe 8 – Community / Forum

- **Ziel**
  - bbPress‑Forum entsprechend des Community‑Plans einrichten.
- **Abhängigkeiten**
  - WordPress‑Grundsystem, Community‑Seite aus Etappe 4.
  - `forum_and_community_plan.md`.
- **Risiken**
  - Zu viele Forenbereiche von Anfang an, dadurch Unübersichtlichkeit.
- **Ergebnis**
  - Forenbereiche:
    - Hilfe & Support.
    - Projekte teilen.
    - Ankündigungen (read‑only).
  - Community‑Seite verlinkt gezielt auf diese Bereiche; CTAs aus Projekten/Tutorials führen in passende Foren.

---

## Etappe 9 – Feinschliff, Inhalte, SEO

- **Ziel**
  - Bestehende Inhalte glätten, Lücken schließen und Auffindbarkeit verbessern.
- **Abhängigkeiten**
  - Alle vorherigen Etappen sollten weitgehend stehen.
- **Risiken**
  - Überoptimierung und Plugin‑Zuwachs.
- **Ergebnis**
  - Überarbeitete Texte und Screenshots auf Basis realer Nutzerfragen.
  - Leichtgewichtiges SEO‑Setup (Titel/Beschreibungen, Sitemap).
  - Ggf. strukturierte Daten für Projekte/Tutorials, sofern sinnvoll.

---

## Selbstprüfung – Umsetzungsplan

- **Plan realistisch?**
  - Ja: Die Etappen bauen schrittweise aufeinander auf und trennen Konzept, Basis, Inhalte und Community klar.
- **Keine unnötigen Großbaustellen?**
  - Ja: Jede Etappe ist in sich überschaubar, mit klaren Abhängigkeiten.
- **Nach Nutzen priorisiert?**
  - Ja: Zuerst Struktur/Doku, dann Basis‑Website und Kernseiten, anschließend dynamische Inhalte, Community und Feinschliff.

