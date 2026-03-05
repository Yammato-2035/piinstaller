#!/bin/bash
# PI-Installer: Freenove Computer Case – Audio-Ausgabe beheben
#
# Behebt das Problem, dass kein Ton aus den Gehäuselautsprechern kommt.
# Das Freenove Mediaboard extrahiert Audio aus HDMI – dieses Skript findet
# den richtigen HDMI-Port und konfiguriert die Audio-Ausgabe.
#
# Ausführung: ./scripts/fix-freenove-audio-output.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove Computer Case – Audio-Ausgabe beheben ===${NC}"
echo ""

# Prüfe PulseAudio/PipeWire
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -z "$PACTL" ]; then
  echo -e "${RED}✗${NC} pactl nicht gefunden"
  echo "Installation: sudo apt install -y pulseaudio-utils"
  exit 1
fi

# Alle verfügbaren Sinks auflisten
echo -e "${CYAN}[1] Verfügbare Audio-Sinks:${NC}"
SINKS=$($PACTL list short sinks 2>/dev/null || echo "")
if [ -z "$SINKS" ]; then
  echo -e "  ${RED}✗${NC} Keine Audio-Sinks gefunden"
  exit 1
fi

echo "$SINKS" | while IFS= read -r line; do
  echo "  $line"
done
echo ""

# Aktueller Standard-Sink
CURRENT_DEFAULT=$($PACTL get-default-sink 2>/dev/null || echo "")
echo -e "${CYAN}[2] Aktueller Standard-Sink:${NC}"
if [ -n "$CURRENT_DEFAULT" ]; then
  echo "  $CURRENT_DEFAULT"
else
  echo -e "  ${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
fi
echo ""

# Freenove: Audio wird aus HDMI extrahiert
# Es gibt 2 HDMI-Ports (HDMI0 und HDMI1)
# Das Mediaboard ist typischerweise an HDMI0 angeschlossen
# Aber wir testen beide, um sicherzugehen

HDMI_SINKS=()
while IFS= read -r line; do
  if echo "$line" | grep -qi "hdmi"; then
    SINK_NAME=$(echo "$line" | awk '{print $2}')
    HDMI_SINKS+=("$SINK_NAME")
  fi
done <<< "$SINKS"

echo -e "${CYAN}[3] Gefundene HDMI-Sinks:${NC}"
for i in "${!HDMI_SINKS[@]}"; do
  echo "  [$i] ${HDMI_SINKS[$i]}"
done
echo ""

# Freenove: HDMI0 (107c701400) ist typischerweise der primäre Port
# HDMI1 (107c706400) ist der sekundäre Port
# Das Mediaboard könnte an beiden angeschlossen sein, aber meistens HDMI0

SELECTED_SINK=""
SELECTED_REASON=""

# Priorität 1: HDMI0 (107c701400) - primärer HDMI-Port
for sink in "${HDMI_SINKS[@]}"; do
  if echo "$sink" | grep -q "107c701400"; then
    SELECTED_SINK="$sink"
    SELECTED_REASON="HDMI0 (107c701400) - primärer HDMI-Port (typisch für Freenove Mediaboard)"
    break
  fi
done

# Priorität 2: HDMI1 (107c706400) - sekundärer HDMI-Port
if [ -z "$SELECTED_SINK" ]; then
  for sink in "${HDMI_SINKS[@]}"; do
    if echo "$sink" | grep -q "107c706400"; then
      SELECTED_SINK="$sink"
      SELECTED_REASON="HDMI1 (107c706400) - sekundärer HDMI-Port"
      break
    fi
  done
fi

# Fallback: Erster HDMI-Sink
if [ -z "$SELECTED_SINK" ] && [ ${#HDMI_SINKS[@]} -gt 0 ]; then
  SELECTED_SINK="${HDMI_SINKS[0]}"
  SELECTED_REASON="Erster verfügbarer HDMI-Sink"
fi

if [ -z "$SELECTED_SINK" ]; then
  echo -e "${RED}✗${NC} Kein HDMI-Sink gefunden"
  exit 1
fi

echo -e "${CYAN}[4] Ausgewählter Sink für Freenove Mediaboard:${NC}"
echo -e "  ${GREEN}✓${NC} $SELECTED_SINK"
echo -e "  ${GREEN}✓${NC} Grund: $SELECTED_REASON"
echo ""

# Prüfe ob bereits korrekt gesetzt
if [ "$CURRENT_DEFAULT" = "$SELECTED_SINK" ]; then
  echo -e "${CYAN}[5] Standard-Sink ist bereits korrekt gesetzt${NC}"
else
  echo -e "${CYAN}[5] Setze Standard-Sink...${NC}"
  if $PACTL set-default-sink "$SELECTED_SINK" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt: $SELECTED_SINK"
  else
    echo -e "  ${RED}✗${NC} Fehler beim Setzen des Standard-Sinks"
    exit 1
  fi
fi
echo ""

# Lautstärke prüfen und erhöhen
echo -e "${CYAN}[6] Lautstärke prüfen und konfigurieren...${NC}"
VOLUME_INFO=$($PACTL list sinks | grep -A15 "Name: $SELECTED_SINK" | grep -E "Volume:|Mute:" | head -2)
VOLUME=$(echo "$VOLUME_INFO" | grep "Volume:" | head -1 | awk '{print $5}' | sed 's/%//' || echo "")
MUTE=$(echo "$VOLUME_INFO" | grep "Mute:" | head -1 | awk '{print $2}' || echo "")

if [ -n "$MUTE" ] && [ "$MUTE" = "yes" ]; then
  echo -e "  ${YELLOW}⚠${NC} Audio ist stummgeschaltet (Mute)"
  $PACTL set-sink-mute "$SELECTED_SINK" 0 2>/dev/null && echo -e "  ${GREEN}✓${NC} Stummschaltung aufgehoben"
fi

if [ -n "$VOLUME" ]; then
  echo "  Aktuelle Lautstärke: ${VOLUME}%"
  if [ "$VOLUME" -lt 75 ]; then
    echo -e "  ${YELLOW}⚠${NC} Lautstärke ist niedrig (< 75%)"
    $PACTL set-sink-volume "$SELECTED_SINK" 85% 2>/dev/null && echo -e "  ${GREEN}✓${NC} Lautstärke auf 85% gesetzt"
  else
    echo -e "  ${GREEN}✓${NC} Lautstärke ist ausreichend"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Lautstärke konnte nicht ermittelt werden"
  echo -e "  ${BLUE}→${NC} Setze Lautstärke auf 85%"
  $PACTL set-sink-volume "$SELECTED_SINK" 85% 2>/dev/null || true
fi
echo ""

# ALSA-Lautstärke auch prüfen (für direkte ALSA-Nutzung)
echo -e "${CYAN}[7] ALSA-Lautstärke prüfen...${NC}"
if command -v amixer >/dev/null 2>&1; then
  # Prüfe beide HDMI-Karten
  for card in 0 1; do
    if [ -d "/proc/asound/card$card" ]; then
      MASTER_VOL=$(amixer -c $card get Master 2>/dev/null | grep -oE "[0-9]+%" | head -1 || echo "")
      PCM_VOL=$(amixer -c $card get PCM 2>/dev/null | grep -oE "[0-9]+%" | head -1 || echo "")
      if [ -n "$MASTER_VOL" ] || [ -n "$PCM_VOL" ]; then
        echo "  Card $card:"
        [ -n "$MASTER_VOL" ] && echo "    Master: $MASTER_VOL"
        [ -n "$PCM_VOL" ] && echo "    PCM: $PCM_VOL"
        # Setze Lautstärke auf 85% falls niedrig
        if [ -n "$MASTER_VOL" ]; then
          VOL_NUM=$(echo "$MASTER_VOL" | sed 's/%//')
          if [ "$VOL_NUM" -lt 75 ]; then
            amixer -c $card set Master 85% unmute 2>/dev/null && echo -e "    ${GREEN}✓${NC} Master auf 85% gesetzt"
          fi
        fi
        if [ -n "$PCM_VOL" ]; then
          VOL_NUM=$(echo "$PCM_VOL" | sed 's/%//')
          if [ "$VOL_NUM" -lt 75 ]; then
            amixer -c $card set PCM 85% unmute 2>/dev/null && echo -e "    ${GREEN}✓${NC} PCM auf 85% gesetzt"
          fi
        fi
      fi
    fi
  done
else
  echo -e "  ${YELLOW}⚠${NC} amixer nicht gefunden"
fi
echo ""

# Test-Audio abspielen
echo -e "${CYAN}[8] Test-Audio abspielen...${NC}"
TEST_FILE="/usr/share/sounds/alsa/Front_Left.wav"
if [ ! -f "$TEST_FILE" ]; then
  TEST_FILE="/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"
fi

if [ -f "$TEST_FILE" ]; then
  echo "  Spiele Test-Audio ab: $TEST_FILE"
  if command -v paplay >/dev/null 2>&1; then
    paplay "$TEST_FILE" 2>&1 && echo -e "  ${GREEN}✓${NC} Test-Audio abgespielt"
  elif command -v aplay >/dev/null 2>&1; then
    aplay "$TEST_FILE" 2>&1 && echo -e "  ${GREEN}✓${NC} Test-Audio abgespielt"
  else
    echo -e "  ${YELLOW}⚠${NC} Kein Audio-Player gefunden (paplay/aplay)"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Test-Audio-Datei nicht gefunden"
  echo "  Manueller Test: paplay /usr/share/sounds/alsa/Front_Left.wav"
fi
echo ""

# Wichtige Hinweise
echo -e "${CYAN}[9] Wichtige Hinweise:${NC}"
echo -e "  ${BLUE}1.${NC} Falls Gehäuse einen MUTE-Schalter hat: prüfen (nicht bei allen vorhanden)"
echo -e "  ${BLUE}2.${NC} Bitte prüfen, ob die Lautsprecher physisch korrekt angeschlossen sind"
echo -e "  ${BLUE}3.${NC} Falls kein Ton: Versuche den anderen HDMI-Sink:"
echo ""
for i in "${!HDMI_SINKS[@]}"; do
  if [ "${HDMI_SINKS[$i]}" != "$SELECTED_SINK" ]; then
    echo "    $PACTL set-default-sink ${HDMI_SINKS[$i]}"
  fi
done
echo ""
echo -e "  ${BLUE}4.${NC} Das Freenove Mediaboard extrahiert Audio aus HDMI"
echo -e "     → Der richtige HDMI-Port muss ausgewählt sein"
echo ""

# Zusammenfassung
echo -e "${CYAN}[10] Zusammenfassung:${NC}"
echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt: $SELECTED_SINK"
echo -e "  ${GREEN}✓${NC} Lautstärke konfiguriert"
echo -e "  ${GREEN}✓${NC} Stummschaltung aufgehoben"
echo ""
echo "Falls weiterhin kein Ton:"
echo "  1. Falls vorhanden: MUTE-Schalter am Gehäuse prüfen"
echo "  2. Anderen HDMI-Sink probieren (siehe oben)"
echo "  3. Diagnose erneut ausführen: ./scripts/diagnose-freenove-audio.sh"
echo ""
