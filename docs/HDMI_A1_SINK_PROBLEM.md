# Problem: HDMI-A-1 wird nicht als PipeWire-Sink erkannt

## Befund

### Card 0 (HDMI-A-1) Status:
- ✅ Existiert in `/proc/asound/cards` als `vc4hdmi0`
- ✅ Existiert in `aplay -l` als Card 0
- ✅ Läuft im **IEC958-Modus (S/PDIF)**
- ❌ HDMI-A-1 Display ist **"disabled"** (Status=connected, Enabled=disabled)
- ❌ **Kein PipeWire-Sink** wird erstellt

### Card 1 (HDMI-A-2) Status:
- ✅ Existiert in `/proc/asound/cards` als `vc4hdmi1`
- ✅ Existiert in `aplay -l` als Card 1
- ✅ Läuft im **IEC958-Modus (S/PDIF)**
- ✅ HDMI-A-2 Display ist **"enabled"** (Status=connected, Enabled=enabled)
- ✅ **PipeWire-Sink wird erstellt** (`alsa_output.platform-107c706400.hdmi.hdmi-stereo`)

## Ursache

**WirePlumber erstellt nur Sinks für "enabled" HDMI-Ports.**

Obwohl beide Cards im IEC958-Modus laufen, erstellt WirePlumber nur für Card 1 einen Sink, weil HDMI-A-2 "enabled" ist. HDMI-A-1 ist "disabled", daher wird kein Sink erstellt.

## Lösungsansätze

### 1. HDMI-A-1 Display aktivieren

**Problem:** HDMI-A-1 bleibt "disabled", auch nach `video=HDMI-A-1:e` in cmdline.txt und Neustart.

**Lösung:** Konfiguriere HDMI-A-1 in `config.txt`:

```bash
# Bearbeite config.txt:
sudo nano /boot/firmware/config.txt

# Füge hinzu (für HDMI-A-1):
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_drive=2

# Oder für beide HDMI-Ports:
hdmi_force_hotplug=1
hdmi_force_hotplug_1=1
```

**Alternative:** Versuche HDMI-A-1 Display zu aktivieren:

```bash
# Versuche HDMI-A-1 Display zu aktivieren:
./scripts/enable-hdmi-a1-display.sh

# Oder manuell mit xrandr (X11):
xrandr --output HDMI-A-1 --auto

# Oder mit wlr-randr (Wayland):
wlr-randr --output HDMI-A-1 --on
```

### 2. WirePlumber-Konfiguration anpassen (EMPFOHLEN)

Erstelle eine WirePlumber-Regel, die Card 0 explizit erkennt, auch wenn HDMI-A-1 "disabled" ist:

```bash
# Automatische Konfiguration:
./scripts/configure-wireplumber-hdmi-a1.sh
```

**Oder manuell:**

```bash
# Erstelle WirePlumber-Konfiguration:
sudo mkdir -p /etc/xdg/wireplumber/wireplumber.conf.d
sudo nano /etc/xdg/wireplumber/wireplumber.conf.d/50-alsa-hdmi-a1.conf
```

Inhalt:
```lua
alsa_monitor.rules = {
  {
    matches = {
      {
        { "device.name", "matches", "alsa_card.platform-107c701400.hdmi" },
      },
    },
    apply_properties = {
      ["device.disabled"] = false,
      ["api.alsa.use-acp"] = true,
    },
  },
}
```

**Nach der Konfiguration:**
```bash
# WirePlumber neu starten:
systemctl --user restart wireplumber.service

# Oder System neu starten:
sudo reboot
```

### 3. Direkt über ALSA (ohne PipeWire)

Das Mediaboard könnte IEC958-Signale direkt von Card 0 extrahieren, auch ohne PipeWire-Sink:

```bash
# Prüfe Card 0 Format:
aplay -D hw:0,0 --dump-hw-params /dev/zero

# Teste IEC958-Direktausgabe:
./scripts/test-hdmi-a1-iec958-direct.sh
```

## Nächste Schritte

1. **Prüfe warum HDMI-A-1 "disabled" bleibt:**
   - cmdline.txt enthält `video=HDMI-A-1:e`
   - Nach Neustart sollte HDMI-A-1 "enabled" sein
   - Falls nicht: Prüfe Kernel-Logs (`sudo dmesg | grep -i hdmi`)

2. **Teste ob Card 0 direkt funktioniert:**
   - Auch ohne PipeWire-Sink könnte das Mediaboard IEC958-Signale extrahieren
   - Teste mit IEC958-kompatiblen Tools

3. **WirePlumber-Konfiguration anpassen:**
   - Erzwinge Sink-Erstellung für Card 0, auch wenn Display "disabled" ist

## Dokumentation

Siehe auch:
- `docs/FREENOVE_AUDIO_TROUBLESHOOTING.md` – Allgemeine Troubleshooting-Dokumentation
- `scripts/diagnose-hdmi-a1-sink.sh` – Vollständige Diagnose
