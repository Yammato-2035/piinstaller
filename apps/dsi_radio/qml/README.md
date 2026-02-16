# Sabrina Tuner – QML-Prototyp

Die Oberfläche liegt in **QML** (`main.qml`), die Logik (GStreamer, Senderliste) in **Python** (Bridge `radio`).

## Qt / Qt Quick einrichten (wenn „Qt startet nicht“)

**1. Diagnose (genaue Fehlermeldung anzeigen):**

```bash
./apps/dsi_radio/.venv/bin/python ./apps/dsi_radio/check_qml.py
```

Die Ausgabe zeigt, bei welcher Stufe es hakt (PyQt6, Anzeige, QML-Modul).

**2. Systempakete installieren (Debian/Ubuntu, mit sudo):**

```bash
sudo bash ./scripts/install-dsi-radio-qml-setup.sh
```

Installiert u. a.: QML-Module (`libqt6qml6`, `qml6-module-qtquick`, …) und XCB/Anzeige-Pakete (`libxcb-cursor0`, `libxcb-xinerama0`, `libxkbcommon0`, …).

**3. Häufige Ursachen:** Kein Display (nur in grafischer Sitzung starten) · „platform plugin xcb“ → Schritt 2 · „module QtQuick not installed“ → Schritt 2.

## Start

- Aus dem Repo-Root: `./scripts/start-dsi-radio-qml.sh`
- Oder: `apps/dsi_radio/.venv/bin/python apps/dsi_radio/dsi_radio_qml.py`

## Anpassungen

- **Layout, Positionen, Farben, Größen:** in `main.qml` ändern (Qt Quick / Qt 6).
- **Sender, Wiedergabe, Lautstärke:** Python-Bridge in `dsi_radio_qml.py` (RadioBridge).

## Bridge (QML → Python)

Im QML ist `radio` verfügbar:

- `radio.currentStationName` – aktueller Sender (Property)
- `radio.volume` – Lautstärke 0–100 (Property)
- `radio.stationCount` – Anzahl Sender
- `radio.stationName(index)` – Name des Senders an Index
- `radio.setStation(index)` – Sender wählen und abspielen
- `radio.setVolume(value)` – Lautstärke setzen
- `radio.quit()` – App beenden

Neue Properties/Slots in `RadioBridge` anlegen und ggf. in `main.qml` verwenden.
