#!/bin/bash
# PI-Installer: Aktiviere HDMI-A-1 Sink (vc4hdmi0 / 107c701400) für Freenove Mediaboard
#
# Sucht die Karte anhand der Plattform-ID 107c701400 (nicht nach ALSA-Kartennummer –
# ALSA Card 0 kann z.B. eine USB-Webcam sein). Aktiviert das output:hdmi-stereo Profil.
#
# Ausführung: ./scripts/activate-hdmi-a1-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== Aktiviere HDMI-A-1 Sink (107c701400 / vc4hdmi0) ===${NC}"
echo ""

# 1. Suche Karte nach Plattform-ID 107c701400 (PipeWire-Objekt-ID, nicht ALSA Card-Nr.)
echo -e "${CYAN}[1] Suche Karte 107c701400 (HDMI-A-1 / vc4hdmi0):${NC}"
CARD_ID=$(pactl list cards short | grep "107c701400" | awk '{print $1}' | head -1)

if [ -z "$CARD_ID" ]; then
  echo -e "  ${RED}✗${NC} Karte 107c701400 nicht in PipeWire/Pulse gefunden"
  echo ""
  if grep -q "vc4hdmi0" /proc/asound/cards 2>/dev/null; then
    echo -e "  ${YELLOW}→${NC} vc4hdmi0 ist in ALSA vorhanden, wird aber von WirePlumber nicht als Karte angeboten."
    echo "    Ohne passende Konfiguration blendet WirePlumber HDMI-A-1 aus („kein Monitor“)."
    echo ""
    echo "  Vorgehen:"
    echo "    1. Konfiguration anlegen:  sudo ./scripts/configure-wireplumber-hdmi-a1.sh"
    echo "    2. WirePlumber neu starten (als Benutzer):  systemctl --user restart wireplumber"
    echo "    3. Dieses Skript erneut ausführen:  ./scripts/activate-hdmi-a1-sink.sh"
    echo ""
    echo "  Siehe: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md → „Freenove Audio von Null einrichten“"
  else
    echo "  ALSA zeigt vc4hdmi0 nicht (cat /proc/asound/cards). Treiber/Neustart prüfen."
    echo "  Prüfe: pactl list cards short"
  fi
  echo ""
  exit 1
fi

echo "  Karte gefunden (PipeWire-ID: $CARD_ID)"
echo ""

SINK=$(pactl list short sinks | grep "107c701400" | awk '{print $2}' | head -1)

# Wenn Sink bereits existiert: Nur Standard setzen, kein Profil neu setzen (vermeidet "Stream error: No such entity")
if [ -n "$SINK" ]; then
  echo -e "${CYAN}[2] Sink existiert bereits – setze nur Standard (Profil nicht neu laden):${NC}"
  echo "  $SINK"
  pactl set-default-sink "$SINK" 2>/dev/null || true
  pactl set-sink-mute "$SINK" 0 2>/dev/null || true
  pactl set-sink-volume "$SINK" 70% 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt, Lautstärke 70 %"
  echo ""
  echo -e "${CYAN}[3] Zusammenfassung:${NC}"
  echo ""
  echo -e "${GREEN}✓${NC} HDMI-A-1 Sink ist Standard: $SINK"
  echo ""
  echo "Hinweis: Profil wurde nicht neu geladen, damit laufende Apps keine „Stream error: No such entity“ bekommen."
  echo ""
  echo -e "${GREEN}Fertig.${NC}"
  exit 0
fi

# 2. Prüfe verfügbare Profile (nur wenn Sink fehlt)
echo -e "${CYAN}[2] Verfügbare Profile:${NC}"
pactl list cards | grep -A 20 "Card #$CARD_ID" | grep -E "Profiles:|output:" | head -5 | sed 's/^/  /'
echo ""

# 3. Aktiviere output:hdmi-stereo Profil (erstellt den Sink)
echo -e "${CYAN}[3] Aktiviere output:hdmi-stereo Profil:${NC}"
if pactl set-card-profile "$CARD_ID" output:hdmi-stereo 2>&1; then
  echo -e "  ${GREEN}✓${NC} Profil aktiviert"
  sleep 2
else
  echo -e "  ${RED}✗${NC} Konnte Profil nicht aktivieren"
  exit 1
fi
echo ""

# 4. Prüfe ob Sink erstellt wurde
echo -e "${CYAN}[4] Prüfe ob Sink erstellt wurde:${NC}"
SINK=$(pactl list short sinks | grep "107c701400" | awk '{print $2}' | head -1)

if [ -n "$SINK" ]; then
  echo -e "  ${GREEN}✓${NC} Sink erstellt: $SINK (HDMI-A-1 / Gehäuselautsprecher)"
  
  # Setze als Standard-Sink
  echo "  Setze als Standard-Sink..."
  pactl set-default-sink "$SINK" 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt"
  
  # Aktiviere Sink (unmute, setze Lautstärke)
  echo "  Aktiviere Sink..."
  pactl set-sink-mute "$SINK" 0 2>/dev/null || true
  pactl set-sink-volume "$SINK" 70% 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} Sink aktiviert"
else
  echo -e "  ${YELLOW}⚠${NC} Kein Sink erstellt"
  echo "  Mögliche Ursachen:"
  echo "    - HDMI-A-1 ist disabled"
  echo "    - WirePlumber erkennt die Karte 107c701400 nicht"
  echo "    - Neustart erforderlich (EDID-Konfiguration)"
fi
echo ""

# 5. Zusammenfassung
echo -e "${CYAN}[5] Zusammenfassung:${NC}"
echo ""
if [ -n "$SINK" ]; then
  echo -e "${GREEN}✓${NC} HDMI-A-1 Sink aktiviert: $SINK"
  echo ""
  echo "Nächste Schritte:"
  echo "  1. Teste Audio – WICHTIG: Terminal/Fenster auf DSI (Gehäuse-Display) legen!"
  echo "     Auf manchen Setups kommt nur dann Ton aus den Gehäuselautsprechern,"
  echo "     wenn das Fenster (Terminal oder App) auf dem DSI-1/Gehäuse-Display läuft."
  echo "     paplay /usr/share/sounds/alsa/Front_Left.wav"
  echo ""
  echo "  2. Falls kein Ton aus Gehäuselautsprechern kommt:"
  echo "     - Fenster auf DSI-1 (Gehäuse-Display) verschieben und erneut testen"
  echo "     - Anderen Sink testen: pactl set-default-sink alsa_output.platform-107c706400.hdmi.hdmi-stereo"
  echo "     - Siehe: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md"
else
  echo -e "${YELLOW}⚠${NC} HDMI-A-1 Sink konnte nicht aktiviert werden"
  echo ""
  echo "Mögliche Lösungen:"
  echo "  1. Prüfe HDMI-A-1 Status:"
  echo "     cat /sys/class/drm/card2-HDMI-A-1/enabled"
  echo ""
  echo "  2. Falls 'disabled':"
  echo "     - EDID-Konfiguration prüfen: sudo ./scripts/fix-freenove-audio-edid.sh"
  echo "     - System neu starten: sudo reboot"
  echo ""
  echo "  3. Siehe: docs/FREENOVE_AUDIO_EDID_SOLUTION.md"
fi
echo ""
echo -e "${GREEN}Fertig.${NC}"
