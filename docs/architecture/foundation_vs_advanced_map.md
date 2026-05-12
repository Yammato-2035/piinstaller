# Vorbereitung Grundlagen / Erweitert

_Phase 4 – Strukturelle Systemvereinfachung. Noch keine UI-Änderung._

## 1. Ziel

Fachlich saubere Vorstruktur für spätere UI-Trennung. Keine Menüs umbauen, keine Funktionen verstecken.

---

## 2. Kandidaten aus System Audit (U-001 bis U-005)

| ID | Bereich | Typ | Begründung | Spätere UI-Folge |
|----|---------|-----|------------|------------------|
| U-001 | ControlCenter.tsx | gemischt | WLAN, SSH, VNC, Sprache, Tastatur, Standard-Display = Grundlagen; Performance, ASUS-ROG, Corsair/RGB, Telemetrie = Erweitert | Trennung in zwei Tabs oder Collapse |
| U-002 | RaspberryPiConfig.tsx | gemischt | Anzeige, Audio, Peripherie = Grundlagen; Overclocking, EDID, Overlays, UART/GPIO/Kamera = Erweitert | Experten-Bereich ausklappbar |
| U-003 | BackupRestore.tsx | gemischt | Lokales Sichern/Wiederherstellen = Grundlagen; Cloud, Verschlüsselung, Zeitpläne, USB-Formatierung = Erweitert | Erweitert-Bereich reduzieren/ausblenden |
| U-004 | App.tsx / Hauptnavigation | gemischt | Installer / Standardverwaltung = Grundlagen; Remote, Radio, TFT, Spezialfunktionen = Erweitert | Spätere Informationsarchitektur |
| U-005 | Documentation.tsx | gemischt | Erste Schritte, Standard-Setups = Grundlagen; Freenove, DSI, Remote, Spezialhardware = Erweitert | Doku-Quelle klären (TSX vs. Markdown) |

---

## 3. Bereits logisch vorstrukturierte Bereiche

- **backend/debug/:** Eigenständiges Modul, klare Grenzen
- **backend/core/:** Eventbus, Registry, Auth, Permissions – unterstützend
- **backend/services/:** Remote-Companion-Module (pi_installer, sabrina_tuner)
- **api/routes/:** Remote-Companion-Routen getrennt von app.py-Endpunkten

---

## 4. Noch vermischt

- **backend/app.py:** Viele Domänen in einem Monolithen; Aufteilung nur nach fachlicher Source-of-Truth
- **Setup-Seiten:** Sudo-, Fetch-, Konfig-Logik wiederholt; gemeinsame Bausteine fehlen
- **Documentation.tsx:** Doku lebt in TSX und docs/*.md parallel

---

## 5. Nächste Schritte (Phase 5/6)

- UI-Trennung Grundlagen / Erweitert (Phase 5)
- UX-Optimierung für Einsteiger (Phase 6)
