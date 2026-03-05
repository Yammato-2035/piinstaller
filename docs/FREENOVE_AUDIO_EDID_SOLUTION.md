# Lösung: EDID für HDMI-A-1 erzwingen (Freenove Mediaboard Audio)

## Problem

**Pi 5 erkennt HDMI-Audio nur, wenn das HDMI-Endgerät EDID präsentiert.**

- Das Freenove Mediaboard extrahiert Audio aus HDMI
- Aber das Mediaboard präsentiert möglicherweise kein EDID
- Daher wird HDMI-A-1 nicht als Audio-Gerät erkannt
- Audio geht nur zum HDMI-Monitor (HDMI-A-2), nicht zu den Gehäuselautsprechern

## Lösung: EDID erzwingen

**Quelle:** Raspberry Pi Forums - "No HDMI audio via extractor without display"
- Link: https://forums.raspberrypi.com/viewtopic.php?t=147115
- Lösung: EDID dumpen und in config.txt erzwingen

### Schritt 1: EDID von HDMI-A-2 dumpen

```bash
# Dump EDID von HDMI-A-2 (wo Monitor angeschlossen ist):
sudo cp /sys/class/drm/card2-HDMI-A-2/edid /boot/firmware/edid-hdmi-a2.dat

# Prüfe EDID:
edid-decode /boot/firmware/edid-hdmi-a2.dat
```

### Schritt 2: Automatisches Skript verwenden

```bash
# Erzwinge EDID für HDMI-A-1:
sudo ./scripts/fix-freenove-audio-edid.sh
```

Dieses Skript:
- Dumped EDID von HDMI-A-2
- Kopiert es nach `/boot/firmware/edid.dat`
- Konfiguriert `config.txt` mit:
  - `hdmi_force_hotplug=1` (für HDMI-A-1)
  - `hdmi_edid_file=1` (verwendet /boot/firmware/edid.dat)
  - `hdmi_drive=2` (erzwingt HDMI-Audio)

### Schritt 3: System neu starten

```bash
sudo reboot
```

Nach dem Neustart sollte HDMI-A-1 als Audio-Gerät erkannt werden.

### Schritt 4: Aktiviere HDMI-A-1 Sink

**WICHTIG:** Auch wenn Card 0 existiert, erstellt WirePlumber möglicherweise keinen Sink automatisch.

```bash
# Aktiviere HDMI-A-1 Sink:
./scripts/activate-hdmi-a1-sink.sh
```

Dieses Skript:
- Aktiviert das `output:hdmi-stereo` Profil für Card 0
- Erstellt den Sink `alsa_output.platform-107c701400.hdmi.hdmi-stereo`
- Setzt ihn als Standard-Sink

### Schritt 5: Prüfe und teste

```bash
# Prüfe HDMI-A-1 Status:
cat /sys/class/drm/card2-HDMI-A-1/enabled

# Prüfe ob Card 0 verfügbar ist:
pactl list short sinks | grep 107c701400

# Teste Audio:
./scripts/test-freenove-speakers-simple.sh
```

## Warum funktioniert das?

**EDID (Extended Display Identification Data)** enthält Informationen über das HDMI-Gerät:
- Unterstützte Auflösungen
- Audio-Fähigkeiten
- Hersteller-Informationen

Der Pi 5 verwendet EDID, um zu bestimmen, ob ein HDMI-Gerät Audio unterstützt. Wenn kein EDID vorhanden ist, wird HDMI-Audio deaktiviert.

**Durch das Erzwingen von EDID:**
- Der Pi 5 denkt, dass ein Monitor mit Audio-Fähigkeiten angeschlossen ist
- HDMI-Audio wird aktiviert
- Das Mediaboard kann Audio extrahieren

## Alternative: EDID-Emulator

Falls das nicht funktioniert, könnte ein **HDMI-EDID-Emulator** zwischen Pi 5 und Mediaboard helfen:
- Emuliert EDID eines Monitors mit Audio
- Ermöglicht HDMI-Audio auch ohne Monitor
- Hardware-Lösung (kostet ~10-20€)

## Dokumentation

Siehe auch:
- `docs/FREENOVE_AUDIO_FINAL_DIAGNOSIS.md` – Finale Diagnose
- `docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md` – Problem-Analyse
- Raspberry Pi Forums: https://forums.raspberrypi.com/viewtopic.php?t=147115
