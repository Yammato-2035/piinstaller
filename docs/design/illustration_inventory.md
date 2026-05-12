# Grafik-Inventar – Illustrationen, Statusgrafiken, Prozessdiagramme

_Stand: März 2026 – Übersicht aller vorhandenen grafischen Assets außer Icons (Icons siehe `icon_inventory.md`)._

---

## 1. Geprüfte Bereiche

- **Illustrationen** (dekorative/konzeptionelle Grafiken für Onboarding, leere Zustände, Projekte)
- **Statusgrafiken** (größere visuelle Status-Indikatoren, z. B. „System OK“, „Wartung“)
- **Prozessdiagramme** (Setup-Flow, Backup-Flow, Installationsablauf, Netzwerk, Geräteerkennung)
- **Screenshots** (Dokumentation/Website)

---

## 2. Vorhandene Illustrationen

**Ergebnis: Keine.**

- Es existiert **kein** Verzeichnis `frontend/public/assets/illustrations/` mit Dateien.
- Es existieren **keine** SVG- oder Raster-Illustrationen für:
  - Onboarding (Welcome, System Check, Experience Selection, Secure Setup, Backup Setup, Discover Projects)
  - Projekttypen (Media Server, NAS, Smart Home, Musikbox, Fotorahmen, Retro-Gaming, Lernumgebung, System-Monitor)
  - Empty States (keine Projekte, keine Backups, keine Geräte, keine Logs)
  - Community (Community, Projekte teilen, Hilfe)
  - Risiko-System (Safe, Warning, Critical) als eigenständige Illustrationen

**Hinweis:** Status wird aktuell über **Icons** aus `assets/icons/status/` (z. B. `status_ok.svg`, `status_warning.svg`) und ggf. Lucide-Icons dargestellt, nicht über separate „Statusgrafiken“ im Sinne großer Illustrationen.

---

## 3. Vorhandene Statusgrafiken

**Ergebnis: Keine eigenständigen Statusgrafiken.**

- Größere, illustrativ gestaltete Statusgrafiken (z. B. „System OK“ als Bild, „Wartung“, „Check läuft“) sind **nicht** vorhanden.
- Status wird ausschließlich über:
  - **AppIcon** mit Kategorie `status` (ok, warning, error, loading, active, complete, running) und optional `statusColor`
  - **Lucide-Icons** und Text/Badges

umgesetzt.

---

## 4. Vorhandene Prozessdiagramme

**Ergebnis: Keine.**

- Es existieren **keine** Dateien für:
  - Setup-Flow (Ablaufdiagramm)
  - Backup-Flow
  - Installationsprozess (als Diagramm)
  - Netzwerkverbindung (als Diagramm)
  - Geräteerkennung (als Diagramm)
- Abläufe werden im UI durch Texte, Schritte und **Process-Icons** (`process_search`, `process_connect`, `process_prepare` usw.) dargestellt, nicht durch eingebettete Diagramm-SVGs.

---

## 5. Screenshots (Dokumentation)

| Art | Pfad / Referenz | Vorhanden im Repo |
|-----|------------------|--------------------|
| Dokumentations-Screenshots | `frontend/public/docs/screenshots/` bzw. `/docs/screenshots/` | **Nein** – nur `README.md` mit Hinweis; keine PNG-Dateien |
| Referenzierte Dateien | z. B. `screenshot-dashboard.png`, `screenshot-wizard.png`, `screenshot-security.png` … (siehe Documentation.tsx, README.md, docs/user/) | **Nein** – werden in UI und Doku referenziert, Dateien fehlen |

**Referenzierte Screenshot-Dateien (ohne Gewähr auf Vollständigkeit):**

- `screenshot-dashboard.png`
- `screenshot-wizard.png`
- `screenshot-presets.png`
- `screenshot-security.png`
- `screenshot-users.png`
- `screenshot-devenv.png`
- `screenshot-webserver.png`
- `screenshot-mailserver.png`
- `screenshot-nas.png`
- `screenshot-homeautomation.png`
- `screenshot-musicbox.png`
- `screenshot-kino-streaming.png`
- `screenshot-learning.png`
- `screenshot-monitoring.png`
- `screenshot-backup.png`
- `screenshot-settings.png`
- `screenshot-control-center.png`
- `screenshot-periphery-scan.png`
- `screenshot-raspberry-pi-config.png`
- `screenshot-documentation.png`

Diese Liste dient der Vorbereitung einer späteren Screenshot-Produktion bzw. Ablage; es werden **keine** neuen Dateien oder Funktionen angelegt.

---

## 6. Zusammenfassung

| Kategorie | Vorhanden | Anmerkung |
|-----------|-----------|-----------|
| Illustrationen (Onboarding, Projekte, Empty States, Community, Risk) | Nein | Nur Icons und Text im Einsatz |
| Statusgrafiken (große Illustrationen) | Nein | Status nur über Status-Icons |
| Prozessdiagramme (Setup, Backup, Install, Netzwerk, Geräte) | Nein | Abläufe nur über UI-Schritte und Process-Icons |
| Screenshots (Doku/Website) | Referenziert, nicht vorhanden | Ordner + README vorhanden, PNGs fehlen |

---

## 7. Selbstprüfung Phase 2

- **Keine neuen Funktionen entwickelt?** – Ja.
- **Keine UI umgebaut?** – Ja.
- **Nur Dokumentation erstellt?** – Ja.
- **Assetstruktur websitefähig?** – Dokumentation ist für spätere Nutzung (Installer + Doku + setuphelfer.de) nutzbar.
