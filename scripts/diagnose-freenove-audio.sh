#!/bin/bash
# PI-Installer: Freenove Computer Case – Audio/Mediaboard Diagnose
#
# Analysiert alle Audio-Geräte auf dem Raspberry Pi und sucht nach dem
# Freenove Mediaboard (Case Adapter Board) für die Gehäuselautsprecher.
#
# Das Freenove Computer Case Kit Pro (FNK0107) hat ein Audio-Video-Board,
# das Audio aus HDMI-Signalen extrahiert und über 3.5mm und die
# Gehäuselautsprecher ausgibt.
#
# Ausführung: ./scripts/diagnose-freenove-audio.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove Computer Case – Audio/Mediaboard Diagnose ===${NC}"
echo ""

# 1. ALSA-Karten auflisten
echo -e "${CYAN}[1] ALSA-Karten (aplay -l)${NC}"
if command -v aplay >/dev/null 2>&1; then
  aplay -l 2>/dev/null | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${RED}✗${NC} aplay nicht gefunden"
fi
echo ""

# 2. ALSA-Karten-Details (/proc/asound/cards)
echo -e "${CYAN}[2] ALSA-Karten-Details (/proc/asound/cards)${NC}"
if [ -f /proc/asound/cards ]; then
  cat /proc/asound/cards | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${RED}✗${NC} /proc/asound/cards nicht gefunden"
fi
echo ""

# 3. ALSA-Control-Devices
echo -e "${CYAN}[3] ALSA-Control-Devices (amixer)${NC}"
if command -v amixer >/dev/null 2>&1; then
  amixer -c 0 scontrols 2>/dev/null | head -10 | while IFS= read -r line; do
    echo "  Card 0: $line"
  done
  if [ -n "$(amixer -c 1 scontrols 2>/dev/null | head -1)" ]; then
    echo "  ---"
    amixer -c 1 scontrols 2>/dev/null | head -10 | while IFS= read -r line; do
      echo "  Card 1: $line"
    done
  fi
else
  echo -e "  ${YELLOW}⚠${NC} amixer nicht gefunden"
fi
echo ""

# 4. PulseAudio/PipeWire Sinks
echo -e "${CYAN}[4] PulseAudio/PipeWire Sinks${NC}"
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -n "$PACTL" ]; then
  echo -e "  ${GREEN}✓${NC} pactl gefunden: $PACTL"
  echo ""
  echo -e "  ${BLUE}Verfügbare Sinks:${NC}"
  $PACTL list short sinks 2>/dev/null | while IFS= read -r line; do
    echo "    $line"
  done
  echo ""
  echo -e "  ${BLUE}Standard-Sink:${NC}"
  DEFAULT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
  if [ -n "$DEFAULT_SINK" ]; then
    echo "    $DEFAULT_SINK"
  else
    echo -e "    ${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
  fi
  echo ""
  echo -e "  ${BLUE}Detaillierte Sink-Informationen:${NC}"
  $PACTL list sinks 2>/dev/null | grep -E "^(Sink|Name:|Description:|State:|Volume:|alsa\.)" | head -30 | while IFS= read -r line; do
    echo "    $line"
  done
else
  echo -e "  ${RED}✗${NC} pactl nicht gefunden (PulseAudio/PipeWire nicht installiert?)"
fi
echo ""

# 5. ALSA-Mixer-Werte für alle Karten
echo -e "${CYAN}[5] ALSA-Mixer-Werte (Lautstärke)${NC}"
for card in 0 1 2 3; do
  if [ -d "/proc/asound/card$card" ]; then
    echo -e "  ${BLUE}Card $card:${NC}"
    if command -v amixer >/dev/null 2>&1; then
      amixer -c $card get Master 2>/dev/null | grep -E "Simple mixer|Mono:|Front Left:|Front Right:" | head -5 | while IFS= read -r line; do
        echo "    $line"
      done
      amixer -c $card get PCM 2>/dev/null | grep -E "Simple mixer|Mono:|Front Left:|Front Right:" | head -5 | while IFS= read -r line; do
        echo "    $line"
      done
    fi
  fi
done
echo ""

# 6. Suche nach Freenove-spezifischen Gerätenamen
echo -e "${CYAN}[6] Suche nach Freenove-spezifischen Gerätenamen${NC}"
FREENOVE_FOUND=""

# In ALSA-Karten
if [ -f /proc/asound/cards ]; then
  while IFS= read -r line; do
    if echo "$line" | grep -qiE "(freenove|case|adapter|media|board|3\.5|analog|headphone|speaker)"; then
      echo -e "  ${GREEN}✓${NC} Gefunden in ALSA: $line"
      FREENOVE_FOUND="yes"
    fi
  done < /proc/asound/cards
fi

# In PulseAudio/PipeWire Sinks
if [ -n "$PACTL" ]; then
  $PACTL list sinks 2>/dev/null | grep -iE "(freenove|case|adapter|media|board|3\.5|analog|headphone|speaker|gehäuse)" | while IFS= read -r line; do
    echo -e "  ${GREEN}✓${NC} Gefunden in PulseAudio/PipeWire: $line"
    FREENOVE_FOUND="yes"
  done
fi

if [ -z "$FREENOVE_FOUND" ]; then
  echo -e "  ${YELLOW}⚠${NC} Keine expliziten Freenove-Gerätenamen gefunden"
  echo -e "  ${YELLOW}  →${NC} Das Mediaboard könnte als generisches HDMI-Audio-Gerät erscheinen"
fi
echo ""

# 7. HDMI-Audio-Geräte (Freenove extrahiert Audio aus HDMI)
echo -e "${CYAN}[7] HDMI-Audio-Geräte (Freenove extrahiert Audio aus HDMI)${NC}"
if [ -n "$PACTL" ]; then
  $PACTL list sinks 2>/dev/null | grep -B5 -A10 -i "hdmi" | grep -E "^(Sink|Name:|Description:|State:|alsa\.card|alsa\.device)" | head -20 | while IFS= read -r line; do
    echo "    $line"
  done
fi
echo ""

# 8. Test: Audio-Ausgabe testen
echo -e "${CYAN}[8] Audio-Test${NC}"
echo -e "  ${BLUE}Verfügbare Test-Befehle:${NC}"
echo "    # Test mit aplay (ALSA):"
echo "    speaker-test -c 2 -t wav -l 1"
echo ""
echo "    # Test mit PulseAudio/PipeWire:"
if [ -n "$PACTL" ]; then
  DEFAULT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
  if [ -n "$DEFAULT_SINK" ]; then
    echo "    pactl set-default-sink $DEFAULT_SINK"
    echo "    paplay /usr/share/sounds/alsa/Front_Left.wav"
  fi
fi
echo ""

# 9. MUTE-Schalter prüfen (Freenove hat einen MUTE-Button)
echo -e "${CYAN}[9] MUTE/Stummschaltung:${NC}"
echo -e "  ${YELLOW}⚠${NC} Nicht bei allen Freenove-Gehäusen vorhanden. Falls vorhanden: Ist er aus?"
echo "    - Sind die Lautsprecher physisch korrekt angeschlossen?"
echo ""

# 10. Konfigurationsvorschläge
echo -e "${CYAN}[10] Konfigurationsvorschläge${NC}"
echo ""
echo -e "  ${BLUE}Option A: Standard-Sink setzen (PulseAudio/PipeWire)${NC}"
if [ -n "$PACTL" ]; then
  echo "    # Alle verfügbaren Sinks anzeigen:"
  echo "    pactl list short sinks"
  echo ""
  echo "    # Standard-Sink setzen (z.B. analog oder 3.5mm):"
  echo "    pactl set-default-sink <SINK-NAME>"
  echo ""
  echo "    # Oder mit pavucontrol (GUI):"
  echo "    pavucontrol"
fi
echo ""
echo -e "  ${BLUE}Option B: ALSA direkt verwenden${NC}"
echo "    # ALSA-Karte für Ausgabe wählen:"
echo "    aplay -D plughw:0,0 /usr/share/sounds/alsa/Front_Left.wav"
echo "    # (0 = Card-Nummer, 0 = Device-Nummer)"
echo ""
echo -e "  ${BLUE}Option C: config.txt prüfen (Raspberry Pi)${NC}"
echo "    # In /boot/firmware/config.txt (oder /boot/config.txt):"
echo "    # dtparam=audio=on  # sollte aktiviert sein"
echo "    # dtoverlay=vc4-kms-v3d  # für HDMI-Audio"
echo ""

# 11. Zusammenfassung
echo -e "${CYAN}[11] Zusammenfassung${NC}"
echo ""
ALSA_CARDS=$(cat /proc/asound/cards 2>/dev/null | grep -E "^[[:space:]]*[0-9]" | wc -l)
PULSE_SINKS=0
if [ -n "$PACTL" ]; then
  PULSE_SINKS=$($PACTL list short sinks 2>/dev/null | wc -l)
fi

echo "  ALSA-Karten gefunden: $ALSA_CARDS"
echo "  PulseAudio/PipeWire Sinks: $PULSE_SINKS"
echo ""
if [ "$ALSA_CARDS" -eq 0 ]; then
  echo -e "  ${RED}✗${NC} Keine ALSA-Karten gefunden – Audio-Hardware möglicherweise nicht erkannt"
elif [ "$PULSE_SINKS" -eq 0 ] && [ -n "$PACTL" ]; then
  echo -e "  ${YELLOW}⚠${NC} ALSA-Karten vorhanden, aber keine PulseAudio/PipeWire Sinks"
  echo -e "  ${YELLOW}  →${NC} PulseAudio/PipeWire möglicherweise nicht gestartet"
else
  echo -e "  ${GREEN}✓${NC} Audio-System scheint grundsätzlich zu funktionieren"
fi
echo ""
echo -e "${GREEN}Fertig.${NC} Bitte die Ausgabe oben prüfen und ggf. die Konfigurationsvorschläge befolgen."
echo ""
