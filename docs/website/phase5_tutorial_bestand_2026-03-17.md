# Phase 5 – Tutorial-Bestand erfasst und integriert (setuphelfer.de)

Datum: 2026-03-17
Ziel: Bereits vorhandene Tutorials/Anleitungen vollstaendig erfassen und sinnvoll in die Website einbinden.

## 1) Identifizierte Tutorial- und Anleitungsquellen

### A) Bereits in Snippets vorhanden

- Kern-Tutorials:
  - `tutorial-pi-os-install.html`
  - `tutorial-wlan-setup.html`
  - `tutorial-ssh-enable.html`
  - `tutorial-backup-create.html`
  - `tutorial-updates-run.html`
  - `tutorial-docker-basics.html`
  - `tutorial-nvme-setup.html`

- Zusaetzlich vorhandene Vertiefungen:
  - `tutorial-network-basics.html`
  - `tutorial-backup-basics.html`
  - `tutorial-linux-basics.html`
  - `tutorial-first-setup.html`

### B) Strukturierte Hilfetexte / Doku-Bestand

- `doc-installation.html`
- `doc-backup.html`
- `doc-diagnostics.html`
- weitere `doc-*`-Eintraege fuer Spezialthemen

### C) Content- und Doku-Referenzen im Projekt

- `website/content/tutorials_overview.md`
- `docs/website/tutorial_template.md`
- `docs/website/wireframe_tutorials.md`
- `docs/VIDEO_TUTORIALS.md`

## 2) Dubletten-/Ueberlappungsanalyse

- Inhaltliche Ueberlappung festgestellt:
  - `tutorial-first-setup.html` vs. `tutorial-pi-os-install.html`
- Entscheidung:
  - `tutorial-pi-os-install.html` bleibt Hauptpfad fuer den Einstieg.
  - `tutorial-first-setup.html` wird **nicht** erneut als aktiver Hauptkartenpunkt ausgebaut, um Doppelpfade zu vermeiden.

## 3) Integration in die Website-Struktur

### 3.1 Tutorial-Archiv erweitert

Datei: `website/setuphelfer-theme/snippets/tutorials.html`

- Neuer Abschnitt:
  - "Weitere vorhandene Tutorials aus dem Projekt"
- Eingebundene Vertiefungen:
  - Netzwerk-Grundlagen
  - Backup-Grundlagen
  - Linux-Grundlagen ohne Umwege
- Zusaetzlicher Verweis auf strukturierte Doku:
  - Installation / Backup / Diagnose

### 3.2 CPT-Datenbasis erweitert

Datei: `website/setuphelfer-theme/inc/setuphelfer-data.php`

- `setuphelfer_tutorials()` um vorhandene Vertiefungs-Tutorials erweitert:
  - `netzwerk-grundlagen-vertiefung` -> `tutorial-network-basics`
  - `backup-grundlagen-vertiefung` -> `tutorial-backup-basics`
  - `linux-grundlagen-vertiefung` -> `tutorial-linux-basics`

Damit werden diese Inhalte beim Seeding als reguläre Tutorial-Posts verfuegbar.

## 4) Unvollstaendige Entwuerfe

- Keine neuen unvollstaendigen Tutorial-Snippets eingefuehrt.
- Vorhandene Alt-Snippets bleiben erhalten; nicht genutzte Inhalte werden transparent als Ueberlappung behandelt statt geloescht.

## 5) Ergebnis Phase 5

- Vorhandener Tutorial-Bestand wurde nicht nur teilweise, sondern erweitert eingebunden.
- Dubletten wurden erkannt und gesteuert.
- Verlinkung zu vorhandenen strukturierten Hilfetexten wurde verbessert.
- Website bildet den realen Projektbestand besser ab als zuvor.

## 6) Selbstpruefung Phase 5

- Alle relevanten Tutorial-Quellen gesucht: Ja.
- Dubletten erkannt: Ja.
- Brauchbare Inhalte integriert: Ja.
- Keine Fantasie-Tutorials erzeugt: Ja.
- Interne Verlinkung verbessert: Ja.

