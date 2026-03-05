# PI-Installer Bilderrahmen

Standalone-App zum Anzeigen von Bildern aus dem Picture-Verzeichnis mit Datumsanzeige, themenbezogenem Text und animierten Symbolen (Weihnachten, Ostern, Geburtstag, Valentinstag, Hochzeitstag).

## Funktionen

- **Verzeichnisauswahl:** Hauptordner `~/Pictures` oder beliebiger Unterordner (z. B. `~/Pictures/Urlaub`).
- **Datumsanzeige:** Aktuelles Datum (und optional Uhrzeit) als Overlay.
- **Einstellungsfenster:**  
  - Bilderordner, Thema, eigener Text zum Einblenden  
  - Wechselintervall, Zufallsreihenfolge  
  - Anzeige Datum/Uhr, Symbolgröße
- **Themen:**  
  Weihnachten, Ostern, Geburtstag, Valentinstag, Hochzeitstag, Halloween, Kein Thema.  
  **Rechtefreie Symbol-Icons** werden aus `apps/picture_frame/symbols/<thema>/` geladen (SVG/PNG, z. B. [Lucide Icons](https://lucide.dev), MIT). Schwarze Symbole nur bei Halloween.  
  Weitere Icons (z. B. von [Pixabay](https://pixabay.com/vectors/), [Iconduck](https://iconduck.com)) können in dieselben Ordner oder in `~/.config/pi-installer-picture-frame/symbols/<thema>/` gelegt werden.
- **Musterbilder:** Ordner `~/Pictures/PI-Installer-Samples` kann mit dem Skript `./scripts/setup-picture-frame-samples.sh` angelegt und mit Beispielbildern (z. B. Picsum) gefüllt werden. Eigene freie Bilder (z. B. von [Pixabay](https://pixabay.com)) können dort abgelegt werden.

## Start

- **Desktop-Icon:** `./scripts/desktop-picture-frame-launcher-anlegen.sh` legt ein Starticon auf dem Desktop und im Anwendungsmenü an.
- **Skript:** `./scripts/start-picture-frame.sh`
- **Direkt:** `python3 apps/picture_frame/picture_frame.py` (aus Projektroot, mit installiertem PyQt6)

## Anzeige

- **Format:** Portrait 480×800 (z. B. für DSI-Display).
- **Bilder:** Weißer Rahmen 3–4 px oben, unten, links und rechts um jedes Bild.
- **Hintergrund:** Schwarz, damit der weiße Bildrahmen gut sichtbar ist.

## Konfiguration

- **Verzeichnis:** `~/.config/pi-installer-picture-frame/`  
- **Datei:** `config.json` (Ordner, Thema, Text, Intervall, Optionen)

## Installation (PyQt6)

```bash
cd apps/picture_frame
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Oder System-weit: `pip install PyQt6` (bzw. Paketmanager).

## Musterbilder anlegen

```bash
./scripts/setup-picture-frame-samples.sh
```

Erstellt `~/Pictures/PI-Installer-Samples`, lädt optional Musterbilder (Picsum) und legt eine kurze README im Ordner ab. Weitere Bilder (z. B. von Pixabay) können manuell in diesen Ordner gelegt werden.

## Rechtefreie Symbol-Icons laden

```bash
./scripts/download-picture-frame-symbols.sh
```

Lädt **Lucide Icons** (MIT, rechtefrei) in `apps/picture_frame/symbols/<thema>/` (Weihnachten, Ostern, Geburtstag, Valentinstag, Hochzeitstag, Halloween). Die App nutzt diese SVG-Icons automatisch; ohne Download werden weiterhin Emoji-Symbole angezeigt. Weitere freie Icons (Pixabay, Iconduck, Public Domain Vectors) können als .svg oder .png in dieselben Ordner gelegt werden.

## Weitere Ideen (optional)

- Vollbildmodus (F11)
- Übergangseffekte zwischen Bildern (Blend, Wischen)
- Wetter-Anzeige (API optional)
- Musik-Unterstützung im Hintergrund
- Zeitschaltuhr (Bilderrahmen nur zu bestimmten Tageszeiten)
