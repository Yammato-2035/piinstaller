# Freenove 4,3″ TFT – PI-Installer Integration

## Erkennung

Der PI-Installer erkennt das Freenove-Gehäuse automatisch:

- **I2C-Expansion-Board:** Adresse `0x21` (Bus 0 oder 1), Register `0xfd` (REG_BRAND)
- **DSI-Display:** `wlr-randr` oder `/sys/class/drm/card*-DSI-*`
- **Audio:** `/proc/asound/cards` (Lautsprecher über System-Sound wählbar)

Wenn DSI oder Expansion-Board erkannt wird, erscheint im **App Store** der TFT-Bereich sowie der Menüpunkt **TFT Display** in der Sidebar.

## Lautsprecher

Die Gehäuse-Lautsprecher werden über die normalen System-Audio-Einstellungen genutzt:

- **Einstellungen → Sound** oder `pavucontrol`
- **Ausgabegerät** auf die Freenove-Audio-Ausgabe stellen

Für Internetradio, Wecker usw. wird dann automatisch über die Gehäuse-Lautsprecher ausgegeben.

## TFT-Modi

Im PI-Installer unter **TFT Display** stehen Modi bereit:

- **Dashboard:** CPU, RAM, Temperatur
- **Internetradio:** Streams vom Pi (Implementierung folgt)
- **Wecker:** Alarm auf dem Display (Implementierung folgt)
- **Bilderrahmen:** Fotos im Loop (Implementierung folgt)
- **NAS-Auslastung:** Speicher-Übersicht (Implementierung folgt)
- **Hauszentrale:** Smart-Home-Status (Implementierung folgt)
- **Leerlauf:** Uhr und Info (Implementierung folgt)

Für den Kiosk-Modus: PI-Installer oder eine spezielle TFT-Seite auf dem DSI-Display starten (`wlr-randr` zeigt das Display als `DSI-1` bzw. ähnlich).

## Gehäuse wird nicht erkannt

1. **API direkt prüfen:** `curl http://localhost:8000/api/system/freenove-detection` – zeigt `expansion_board`, `dsi_display`, `audio_available`.
2. **I2C:** Benutzer in Gruppe `i2c`: `sudo usermod -aG i2c $USER`, dann abmelden/anmelden. Prüfen: `i2cget -y 1 0x21 0xfd` (sollte einen Hex-Wert ausgeben).
3. **i2c-tools:** Falls fehlend: `sudo apt install i2c-tools`. I2C in `raspi-config` (Interface Options) aktivieren.
4. **DSI:** `/sys/class/drm/card*-DSI-*/status` sollte `connected` enthalten, wenn das DSI-Display verbunden ist.
