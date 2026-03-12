# Fehlende Grafiken – PI-Installer

_Stand: März 2026 – Liste der fehlenden Illustrationen und Grafiken für Installer, Dokumentation und Website (setuphelfer.de). Es werden **keine** neuen Assets erzeugt; nur Bedarf dokumentiert._

---

## 1. Onboarding

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **welcome** | Begrüßungsbild für ersten Start / First-Run-Wizard |
| **system check** | Illustration „System wird geprüft“ |
| **experience selection** | Auswahl der Nutzererfahrung / Ziel (Einsteiger, Fortgeschritten, Experte) |
| **secure setup** | Sichere Einrichtung (Sicherheit, Firewall, Benutzer) |
| **backup setup** | Backup einrichten / Erstes Backup |
| **discover projects** | Projekte entdecken (Presets, Module, App-Store) |

---

## 2. Projects (Projekttypen)

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **media server** | Medienserver (Plex, Jellyfin, …) |
| **NAS** | NAS / Speicher / Freigaben |
| **smart home** | Smart Home / Hausautomatisierung (Home Assistant, openHAB, FHEM) |
| **music box** | Musikbox (Mopidy, Volumio, Plex Music) |
| **photo frame** | Fotorahmen / Diashow |
| **retro gaming** | Retro-Gaming / Emulation |
| **learning environment** | Lernumgebung / Lerncomputer |
| **system monitor** | System-Monitoring / Dashboards |

---

## 3. Setup-Diagramme

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **setup flow** | Gesamtablauf Setup-Assistent (Schritte, Entscheidungen) |
| **backup flow** | Ablauf Backup (Quelle → Ziel, Optionen) |
| **install process** | Installationsprozess (Schreiben, Prüfen, Neustart) |
| **network connection** | Netzwerkverbindung (Pi ↔ Rechner, Remote) |
| **device detection** | Geräteerkennung (USB, SD, NVMe, Peripherie-Scan) |

---

## 4. Statusgrafiken

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **system ok** | Großes Statusbild „Alles in Ordnung“ (kann von status_ok.svg abweichen, z. B. Hero) |
| **system warning** | Status „Warnung / Aktion empfohlen“ |
| **system problem** | Status „Problem / Fehler“ |
| **maintenance** | Wartung / Update läuft |
| **check running** | Prüfung läuft (z. B. Systemcheck, Scan) |

---

## 5. Empty States

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **no projects** | Keine Projekte / Presets ausgewählt |
| **no backups** | Keine Backups vorhanden / konfiguriert |
| **no devices** | Keine Geräte erkannt |
| **no logs** | Keine Log-Einträge |

---

## 6. Community-Grafiken

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **community** | Community / Nutzer vernetzen |
| **share projects** | Projekte teilen / Presets teilen |
| **help** | Hilfe / Support / Dokumentation |

---

## 7. Risk-System

| Grafik | Beschreibung / Kontext |
|--------|------------------------|
| **safe** | Stufe „Sicher“ (grün / niedriges Risiko) |
| **warning** | Stufe „Warnung“ (gelb / mittleres Risiko) |
| **critical** | Stufe „Kritisch“ (rot / hohes Risiko) |

_Anmerkung: Im Code existieren bereits `RiskLevelBadge` und `RiskWarningCard`; fehlend sind einheitliche **Illustrationen** für die drei Stufen (z. B. für Doku oder Website)._

---

## 8. Übersicht nach Priorität (Empfehlung)

- **Hohe Priorität (Onboarding + Empty States):** welcome, system check, experience selection, secure setup, backup setup, discover projects; no projects, no backups, no devices, no logs.
- **Mittlere Priorität (Projekte + Status):** Projekt-Illustrationen (media server, NAS, smart home, …); system ok, system warning, system problem, maintenance, check running.
- **Mittlere Priorität (Setup + Risiko):** setup flow, backup flow, install process; safe, warning, critical.
- **Unterstützend (Doku/Website):** network connection, device detection; community, share projects, help.

---

## 9. Selbstprüfung Phase 3

- **Keine neuen Funktionen entwickelt?** – Ja.
- **Keine UI umgebaut?** – Ja.
- **Nur Dokumentation erstellt?** – Ja (Liste fehlender Grafiken).
- **Assetstruktur websitefähig?** – Liste ist für Installer, Doku und setuphelfer.de nutzbar.
