# PI-Installer: Ressourcen-Optimierung auf dem Raspberry Pi

## CPU-Reduktion durch den PI-Installer

Der PI-Installer wurde optimiert, um auf einem Raspberry Pi weniger CPU zu verbrauchen:

### Bereits umgesetzt

1. **Leichtgewichtiges Polling** (`/api/system-info?light=1`)
   - Beim periodischen Aktualisieren des Dashboards wird ein reduzierter Modus genutzt
   - Keine 1-Sekunden-Blockierung mehr für CPU-Messung (stattdessen sofortige Abfrage)
   - Es werden keine schweren Abfragen mehr ausgeführt (kein dmidecode, lspci, Sensoren-Scan, etc.)

2. **Längere Polling-Intervalle auf dem Pi**
   - Dashboard: alle **30 Sekunden** (statt 5) wenn ein Raspberry Pi erkannt wird
   - Monitoring: **kein Live-Polling** auf dem Pi – Auslastungs-Charts nur im Dashboard

3. **Auslastung nur im Dashboard**
   - Die Live-Auslastung (CPU, RAM, Temperatur) wird ausschließlich im Dashboard angezeigt
   - Doppelte Anzeigen in Submenüs (z. B. Monitoring) entfallen auf dem Pi

4. **Tauri-Desktop-App: Leichtgewichtsmodus**
   - Wenn die **Tauri-Oberfläche** (Desktop-App) statt des Browsers genutzt wird, aktiviert sich automatisch ein CPU-sparender Modus:
   - `backdrop-blur` / Glasmorphismus deaktiviert (sehr teuer in WebKitGTK)
   - Hintergrund-Gradient-Animation gestoppt
   - Status-Icon-Puls-Animation deaktiviert
   - Hinweis: Im Browser (Chromium) liegt die CPU-Auslastung typisch bei ~7 %; in Tauri ohne Optimierung bei ~75 %. Der Leichtgewichtsmodus reduziert dies deutlich.

### Raspberry Pi 5: Kein Ton über HDMI?

Wenn am Monitor kein Ton ausgegeben wird und `cat /proc/asound/cards` „no soundcards“ zeigt: In `/boot/firmware/config.txt` die Zeile `dtoverlay=vc4-kms-v3d-pi5` ergänzen (unter `dtparam=audio=on`). Ohne diesen Overlay wird die HDMI-Audio-Hardware des Pi 5 nicht initialisiert. Nach `sudo reboot` sollten die Soundkarten erscheinen. Details: **Dokumentation → Troubleshooting** in der App.

---

### Raspberry Pi Config – warum wird sie nicht angezeigt?

Der Menüpunkt **Raspberry Pi Config** erscheint nur, wenn der PI-Installer erkennt, dass er auf einem Raspberry Pi läuft. Die Erkennung erfolgt über:

- `/proc/device-tree/model` (enthält „Raspberry“)
- `/proc/cpuinfo` (Hardware: BCM2712, BCM2711, …)
- `vcgencmd` (nur auf Pi vorhanden)

Wenn der Pi nicht erkannt wird, erscheint „Linux-System“ statt „Raspberry Pi“ in der Sidebar. Die Erkennung wurde um einen Device-Tree-Fallback ergänzt, damit auch neuere Pi-Modelle zuverlässig erkannt werden.

---

## Raspberry Pi: unnötige System-Services deaktivieren

Wenn der Pi **ohne Bildschirm** (Headless) oder als **Server** läuft, können folgende Services deaktiviert werden, um CPU und RAM zu sparen:

| Service | Beschreibung | Deaktivieren |
|---------|--------------|--------------|
| `bluetooth` | Bluetooth | `sudo systemctl disable bluetooth` |
| `avahi-daemon` | mDNS/Bonjour (Netzwerk-Discovery) | `sudo systemctl disable avahi-daemon` |
| `triggerhappy` | Global-Keyboard-Hotkeys (oft unnötig headless) | `sudo systemctl disable triggerhappy` |
| `wpa_supplicant` | Nur wenn ausschließlich Ethernet genutzt wird | Vorsicht: WLAN fällt weg |
| `ModemManager` | Modem-Verwaltung (meist nicht vorhanden) | `sudo systemctl disable ModemManager` |
| `dphys-swapfile` | Swap-Datei – kann bei ausreichend RAM deaktiviert werden | `sudo systemctl disable dphys-swapfile` |

### Vorsicht

- **Nicht** deaktivieren: `ssh`, `networking`, `systemd-networkd`, `dbus`
- Vor dem Deaktivieren prüfen: `systemctl status <service>`
- Nach Änderungen: `sudo reboot` empfohlen

### Beispiel-Script (optional)

```bash
# Nur ausführen, wenn Sie wissen, was Sie tun
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
sudo systemctl disable triggerhappy
# Optional: sudo systemctl disable dphys-swapfile  # Nur bei ≥4 GB RAM
```

---

## Raspberry Pi 5: Kein Ton über HDMI

Wenn am Monitor kein Ton ausgegeben wird und `cat /proc/asound/cards` „no soundcards“ zeigt, fehlt oft der Overlay **vc4-kms-v3d-pi5** in der config.txt. Ohne diesen wird die HDMI-Audio-Hardware nicht initialisiert.

**Lösung:** In `/boot/firmware/config.txt` hinzufügen: `dtoverlay=vc4-kms-v3d-pi5`. Danach Neustart. Details: Dokumentation → Troubleshooting in der App.

---

## Weitere Tipps

- **Raspberry Pi OS Lite** statt Desktop nutzen, wenn keine grafische Oberfläche benötigt wird
- **GPU-Speicher** reduzieren (Raspberry Pi Config), wenn kein Video/3D genutzt wird
- **Overclock** vermeiden, wenn Stabilität wichtiger ist als Performance
