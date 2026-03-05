#!/bin/bash
# PI-Installer: Freenove Computer Case – Gehäuselautsprecher konfigurieren
#
# Problem: Sound geht nur über HDMI-Monitor, nicht über Gehäuselautsprecher
# Lösung: Das Freenove Mediaboard extrahiert Audio aus HDMI, muss aber über
# den richtigen HDMI-Port angesprochen werden. Dieses Skript findet den
# richtigen Port und konfiguriert das Audio-Routing.
#
# Ausführung: ./scripts/fix-freenove-case-speakers.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove Computer Case – Gehäuselautsprecher konfigurieren ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -qi "raspberry" /proc/device-tree/model 2>/dev/null; then
  echo -e "${YELLOW}⚠${NC} Dieses Skript ist für Raspberry Pi gedacht"
  exit 1
fi

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

echo -e "${CYAN}[1] Raspberry Pi 5 Audio-Ausgabe${NC}"
echo "  Der Raspberry Pi 5 hat keinen 3.5mm-Audio-Ausgang mehr."
echo "  Audio wird standardmäßig über HDMI ausgegeben."
echo "  Das Freenove Mediaboard extrahiert Audio aus HDMI und gibt es"
echo "  über die Gehäuselautsprecher aus."
echo ""

# Verfügbare HDMI-Sinks
echo -e "${CYAN}[2] Verfügbare HDMI-Audio-Sinks:${NC}"
SINKS=$($PACTL list short sinks 2>/dev/null || echo "")
if [ -z "$SINKS" ]; then
  echo -e "  ${RED}✗${NC} Keine Audio-Sinks gefunden"
  exit 1
fi

HDMI_SINKS=()
while IFS= read -r line; do
  if echo "$line" | grep -qi "hdmi"; then
    SINK_NAME=$(echo "$line" | awk '{print $2}')
    HDMI_SINKS+=("$SINK_NAME")
    echo "  - $SINK_NAME"
  fi
done <<< "$SINKS"

if [ ${#HDMI_SINKS[@]} -eq 0 ]; then
  echo -e "  ${RED}✗${NC} Keine HDMI-Sinks gefunden"
  exit 1
fi
echo ""

# Aktueller Standard-Sink
CURRENT_DEFAULT=$($PACTL get-default-sink 2>/dev/null || echo "")
echo -e "${CYAN}[3] Aktueller Standard-Sink:${NC}"
if [ -n "$CURRENT_DEFAULT" ]; then
  echo "  $CURRENT_DEFAULT"
else
  echo -e "  ${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
fi
echo ""

# Freenove: Das Mediaboard ist typischerweise an HDMI0 (107c701400) angeschlossen
# Aber: Es könnte auch HDMI1 (107c706400) sein, je nach Konfiguration
# WICHTIG: Der HDMI-Port, der NICHT an einen Monitor angeschlossen ist, ist meistens
# der richtige für das Mediaboard

echo -e "${CYAN}[4] Freenove Mediaboard – Audio-Routing${NC}"
echo "  Das Mediaboard extrahiert Audio aus HDMI und gibt es über die"
echo "  Gehäuselautsprecher aus."
echo ""
echo "  WICHTIG: Der HDMI-Port, der für das Mediaboard verwendet wird,"
echo "  sollte NICHT an einen Monitor angeschlossen sein (oder der Monitor"
echo "  sollte kein Audio unterstützen)."
echo ""

# Prüfe welche HDMI-Ausgänge aktiv sind
echo -e "${CYAN}[5] Aktive HDMI-Ausgänge prüfen:${NC}"
HDMI_DISPLAYS=$(xrandr 2>/dev/null | grep -i "hdmi.*connected" || echo "")
if [ -n "$HDMI_DISPLAYS" ]; then
  echo "$HDMI_DISPLAYS" | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} xrandr nicht verfügbar oder keine HDMI-Displays erkannt"
  echo "  (Das ist OK, wenn kein Monitor angeschlossen ist)"
fi
echo ""

# Strategie: Bei Freenove sollte der Standard-Sink verwendet werden
# Aber: Wenn der Standard-Sink auf einen HDMI-Monitor zeigt, müssen wir
# den anderen HDMI-Port verwenden

SELECTED_SINK=""
SELECTED_REASON=""

# Wenn nur ein HDMI-Sink vorhanden ist, diesen verwenden
if [ ${#HDMI_SINKS[@]} -eq 1 ]; then
  SELECTED_SINK="${HDMI_SINKS[0]}"
  SELECTED_REASON="Nur ein HDMI-Sink verfügbar"
elif [ ${#HDMI_SINKS[@]} -eq 2 ]; then
  # Zwei HDMI-Sinks: Prüfe welcher der Standard ist
  if [ -n "$CURRENT_DEFAULT" ] && echo "$CURRENT_DEFAULT" | grep -qi "hdmi"; then
    # Standard-Sink ist bereits ein HDMI-Sink
    # Bei Freenove: Standard-Sink beibehalten (wie in Version 1.2.x.x)
    SELECTED_SINK="$CURRENT_DEFAULT"
    SELECTED_REASON="Standard-Sink beibehalten (wie Version 1.2.x.x)"
  else
    # Standard-Sink ist nicht HDMI oder nicht gesetzt
    # Priorität: HDMI0 (107c701400) - primärer HDMI-Port
    for sink in "${HDMI_SINKS[@]}"; do
      if echo "$sink" | grep -q "107c701400"; then
        SELECTED_SINK="$sink"
        SELECTED_REASON="HDMI0 (107c701400) - primärer HDMI-Port"
        break
      fi
    done
    # Fallback: Erster HDMI-Sink
    if [ -z "$SELECTED_SINK" ]; then
      SELECTED_SINK="${HDMI_SINKS[0]}"
      SELECTED_REASON="Erster verfügbarer HDMI-Sink"
    fi
  fi
else
  # Mehr als 2 HDMI-Sinks: HDMI0 bevorzugen
  for sink in "${HDMI_SINKS[@]}"; do
    if echo "$sink" | grep -q "107c701400"; then
      SELECTED_SINK="$sink"
      SELECTED_REASON="HDMI0 (107c701400) - primärer HDMI-Port"
      break
    fi
  done
  if [ -z "$SELECTED_SINK" ]; then
    SELECTED_SINK="${HDMI_SINKS[0]}"
    SELECTED_REASON="Erster verfügbarer HDMI-Sink"
  fi
fi

if [ -z "$SELECTED_SINK" ]; then
  echo -e "${RED}✗${NC} Kein HDMI-Sink gefunden"
  exit 1
fi

echo -e "${CYAN}[6] Ausgewählter Sink für Gehäuselautsprecher:${NC}"
echo -e "  ${GREEN}✓${NC} $SELECTED_SINK"
echo -e "  ${GREEN}✓${NC} Grund: $SELECTED_REASON"
echo ""

# Setze Standard-Sink
if [ "$CURRENT_DEFAULT" != "$SELECTED_SINK" ]; then
  echo -e "${CYAN}[7] Setze Standard-Sink...${NC}"
  if $PACTL set-default-sink "$SELECTED_SINK" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt: $SELECTED_SINK"
  else
    echo -e "  ${RED}✗${NC} Fehler beim Setzen des Standard-Sinks"
    exit 1
  fi
else
  echo -e "${CYAN}[7] Standard-Sink ist bereits korrekt gesetzt${NC}"
  echo -e "  ${GREEN}✓${NC} $SELECTED_SINK"
fi
echo ""

# Lautstärke prüfen und erhöhen
echo -e "${CYAN}[8] Lautstärke prüfen...${NC}"
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
fi
echo ""

# Test-Audio abspielen
echo -e "${CYAN}[9] Test-Audio abspielen...${NC}"
TEST_FILE="/usr/share/sounds/alsa/Front_Left.wav"
if [ ! -f "$TEST_FILE" ]; then
  TEST_FILE="/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"
fi

if [ -f "$TEST_FILE" ]; then
  echo "  Spiele Test-Audio ab: $TEST_FILE"
  if command -v paplay >/dev/null 2>&1; then
    paplay "$TEST_FILE" 2>&1 && echo -e "  ${GREEN}✓${NC} Test-Audio abgespielt"
    echo ""
    echo -e "  ${BLUE}→${NC} Bitte prüfen, ob der Ton aus den Gehäuselautsprechern kommt"
    echo -e "  ${BLUE}→${NC} Falls nicht, probiere den anderen HDMI-Port:"
    for sink in "${HDMI_SINKS[@]}"; do
      if [ "$sink" != "$SELECTED_SINK" ]; then
        echo "    $PACTL set-default-sink $sink"
      fi
    done
  else
    echo -e "  ${YELLOW}⚠${NC} paplay nicht gefunden"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Test-Audio-Datei nicht gefunden"
  echo "  Manueller Test: paplay /usr/share/sounds/alsa/Front_Left.wav"
fi
echo ""

# Wichtige Hinweise
echo -e "${CYAN}[10] Wichtige Hinweise:${NC}"
echo -e "  ${BLUE}1.${NC} Das Freenove Mediaboard extrahiert Audio aus HDMI"
echo -e "  ${BLUE}2.${NC} Der richtige HDMI-Port muss verwendet werden"
echo -e "  ${BLUE}3.${NC} Falls kein Ton: Probiere den anderen HDMI-Port"
echo -e "  ${BLUE}4.${NC} Falls weiterhin kein Ton: Prüfe physische Verbindungen"
echo ""

# Zusammenfassung
echo -e "${CYAN}[11] Zusammenfassung:${NC}"
echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt: $SELECTED_SINK"
echo -e "  ${GREEN}✓${NC} Lautstärke konfiguriert"
echo ""
echo "Falls weiterhin kein Ton aus den Gehäuselautsprechern:"
echo "  1. Probiere den anderen HDMI-Port (siehe oben)"
echo "  2. Prüfe physische Verbindungen am Mediaboard"
echo "  3. Diagnose ausführen: ./scripts/diagnose-freenove-audio.sh"
echo ""
