#!/bin/bash
# PI-Installer: Freenove Computer Case – Audio/Mediaboard automatisch konfigurieren
#
# Findet und konfiguriert das Freenove Mediaboard (Case Adapter Board) für die
# Gehäuselautsprecher. Das Board extrahiert Audio aus HDMI und gibt es über
# 3.5mm und die Gehäuselautsprecher aus.
#
# Ausführung: ./scripts/configure-freenove-audio.sh [--dry-run]
# Mit --dry-run: Zeigt nur an, was gemacht würde, ohne Änderungen vorzunehmen

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=""
[ "${1:-}" = "--dry-run" ] && DRY_RUN="yes"

echo -e "${CYAN}=== Freenove Computer Case – Audio/Mediaboard Konfiguration ===${NC}"
echo ""

# Prüfe ob PulseAudio/PipeWire verfügbar ist
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -z "$PACTL" ]; then
  echo -e "${RED}✗${NC} pactl nicht gefunden (PulseAudio/PipeWire nicht installiert)"
  echo ""
  echo "Installation:"
  echo "  sudo apt update"
  echo "  sudo apt install -y pulseaudio-utils pavucontrol"
  exit 1
fi

echo -e "${GREEN}✓${NC} PulseAudio/PipeWire gefunden: $PACTL"
echo ""

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

# Detaillierte Sink-Informationen sammeln
echo -e "${CYAN}[2] Analysiere Audio-Sinks für Freenove Mediaboard...${NC}"
DETAILED_SINKS=$($PACTL list sinks 2>/dev/null || echo "")

# Kandidaten sammeln
SPEAKER_SINKS=()
HEADPHONE_SINKS=()
ANALOG_SINKS=()
NON_HDMI_SINKS=()
HDMI_SINKS=()

CURRENT_SINK=""
CURRENT_DESC=""

while IFS= read -r line; do
  line_stripped=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  
  if echo "$line_stripped" | grep -qE "^Sink #[0-9]+"; then
    CURRENT_SINK=""
    CURRENT_DESC=""
  elif echo "$line_stripped" | grep -qE "^Name:"; then
    CURRENT_SINK=$(echo "$line_stripped" | sed 's/^Name:[[:space:]]*//')
  elif echo "$line_stripped" | grep -qE "^Description:"; then
    CURRENT_DESC=$(echo "$line_stripped" | sed 's/^Description:[[:space:]]*//')
    
    if [ -n "$CURRENT_SINK" ] && [ -n "$CURRENT_DESC" ]; then
      sink_lower=$(echo "$CURRENT_SINK" | tr '[:upper:]' '[:lower:]')
      desc_lower=$(echo "$CURRENT_DESC" | tr '[:upper:]' '[:lower:]')
      combined="${sink_lower} ${desc_lower}"
      
      # HDMI-Ausgänge identifizieren
      is_hdmi=false
      if echo "$combined" | grep -qiE "(hdmi|107c701400|107c706400|vc4hdmi|digital stereo.*hdmi)"; then
        is_hdmi=true
        HDMI_SINKS+=("$CURRENT_SINK")
      fi
      
      if [ "$is_hdmi" = false ]; then
        NON_HDMI_SINKS+=("$CURRENT_SINK")
        
        # Spezifische Kategorien
        if echo "$combined" | grep -qiE "(speaker|lautsprecher|gehäuse|case)"; then
          SPEAKER_SINKS+=("$CURRENT_SINK")
        fi
        if echo "$combined" | grep -qiE "(headphone|headphones|3\.5|jack|analog.*output)"; then
          HEADPHONE_SINKS+=("$CURRENT_SINK")
        fi
        if echo "$combined" | grep -qiE "(analog.*output|analog.*stereo)"; then
          ANALOG_SINKS+=("$CURRENT_SINK")
        fi
      fi
    fi
  fi
done <<< "$DETAILED_SINKS"

# Priorität: Speaker > Headphone > Analog > Non-HDMI
SELECTED_SINK=""
SELECTED_REASON=""

if [ ${#SPEAKER_SINKS[@]} -gt 0 ]; then
  SELECTED_SINK="${SPEAKER_SINKS[0]}"
  SELECTED_REASON="Speaker/Gehäuselautsprecher gefunden"
elif [ ${#HEADPHONE_SINKS[@]} -gt 0 ]; then
  SELECTED_SINK="${HEADPHONE_SINKS[0]}"
  SELECTED_REASON="Headphone/3.5mm Ausgang gefunden"
elif [ ${#ANALOG_SINKS[@]} -gt 0 ]; then
  SELECTED_SINK="${ANALOG_SINKS[0]}"
  SELECTED_REASON="Analog-Ausgang gefunden"
elif [ ${#NON_HDMI_SINKS[@]} -gt 0 ]; then
  SELECTED_SINK="${NON_HDMI_SINKS[0]}"
  SELECTED_REASON="Non-HDMI Ausgang gefunden (Freenove extrahiert Audio aus HDMI)"
fi

# Fallback: Wenn nur HDMI-Sinks vorhanden sind, nehmen wir den ersten
# (Freenove extrahiert Audio aus HDMI, daher könnte es ein HDMI-Sink sein)
if [ -z "$SELECTED_SINK" ] && [ ${#HDMI_SINKS[@]} -gt 0 ]; then
  SELECTED_SINK="${HDMI_SINKS[0]}"
  SELECTED_REASON="HDMI-Ausgang (Freenove extrahiert Audio aus HDMI)"
fi

# Ergebnis anzeigen
echo -e "  ${BLUE}Gefundene Kategorien:${NC}"
echo "    Speaker/Gehäuselautsprecher: ${#SPEAKER_SINKS[@]}"
echo "    Headphone/3.5mm: ${#HEADPHONE_SINKS[@]}"
echo "    Analog: ${#ANALOG_SINKS[@]}"
echo "    Non-HDMI: ${#NON_HDMI_SINKS[@]}"
echo "    HDMI: ${#HDMI_SINKS[@]}"
echo ""

if [ -z "$SELECTED_SINK" ]; then
  echo -e "  ${RED}✗${NC} Kein passender Audio-Sink gefunden"
  echo ""
  echo "Bitte manuell prüfen:"
  echo "  $PACTL list short sinks"
  echo "  $PACTL list sinks"
  exit 1
fi

echo -e "  ${GREEN}✓${NC} Ausgewählter Sink: ${CYAN}$SELECTED_SINK${NC}"
echo -e "  ${GREEN}✓${NC} Grund: $SELECTED_REASON"
echo ""

# Aktueller Standard-Sink
CURRENT_DEFAULT=$($PACTL get-default-sink 2>/dev/null || echo "")
if [ -n "$CURRENT_DEFAULT" ]; then
  echo -e "${CYAN}[3] Aktueller Standard-Sink:${NC} $CURRENT_DEFAULT"
  if [ "$CURRENT_DEFAULT" = "$SELECTED_SINK" ]; then
    echo -e "  ${GREEN}✓${NC} Bereits korrekt konfiguriert!"
    echo ""
    echo -e "${CYAN}[4] Lautstärke prüfen:${NC}"
    VOLUME=$($PACTL list sinks | grep -A10 "Name: $SELECTED_SINK" | grep "Volume:" | head -1 | awk '{print $5}' | sed 's/%//')
    if [ -n "$VOLUME" ]; then
      echo "  Aktuelle Lautstärke: ${VOLUME}%"
      if [ "$VOLUME" -lt 50 ]; then
        echo -e "  ${YELLOW}⚠${NC} Lautstärke ist niedrig (< 50%)"
      fi
    fi
    echo ""
    echo -e "${GREEN}Fertig.${NC} Audio ist bereits korrekt konfiguriert."
    exit 0
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
fi
echo ""

# Standard-Sink setzen
echo -e "${CYAN}[4] Setze Standard-Sink...${NC}"
if [ -n "$DRY_RUN" ]; then
  echo -e "  ${YELLOW}[DRY-RUN]${NC} Würde ausführen: $PACTL set-default-sink $SELECTED_SINK"
else
  if $PACTL set-default-sink "$SELECTED_SINK" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt: $SELECTED_SINK"
  else
    echo -e "  ${RED}✗${NC} Fehler beim Setzen des Standard-Sinks"
    exit 1
  fi
fi
echo ""

# Lautstärke prüfen und ggf. erhöhen
echo -e "${CYAN}[5] Lautstärke prüfen...${NC}"
VOLUME_INFO=$($PACTL list sinks | grep -A15 "Name: $SELECTED_SINK" | grep -E "Volume:|Mute:" | head -2)
VOLUME=$(echo "$VOLUME_INFO" | grep "Volume:" | head -1 | awk '{print $5}' | sed 's/%//' || echo "")
MUTE=$(echo "$VOLUME_INFO" | grep "Mute:" | head -1 | awk '{print $2}' || echo "")

if [ -n "$MUTE" ] && [ "$MUTE" = "yes" ]; then
  echo -e "  ${YELLOW}⚠${NC} Audio ist stummgeschaltet (Mute)"
  if [ -z "$DRY_RUN" ]; then
    $PACTL set-sink-mute "$SELECTED_SINK" 0 2>/dev/null && echo -e "  ${GREEN}✓${NC} Stummschaltung aufgehoben"
  else
    echo -e "  ${YELLOW}[DRY-RUN]${NC} Würde ausführen: $PACTL set-sink-mute $SELECTED_SINK 0"
  fi
fi

if [ -n "$VOLUME" ]; then
  echo "  Aktuelle Lautstärke: ${VOLUME}%"
  if [ "$VOLUME" -lt 50 ]; then
    echo -e "  ${YELLOW}⚠${NC} Lautstärke ist niedrig (< 50%)"
    if [ -z "$DRY_RUN" ]; then
      $PACTL set-sink-volume "$SELECTED_SINK" 75% 2>/dev/null && echo -e "  ${GREEN}✓${NC} Lautstärke auf 75% gesetzt"
    else
      echo -e "  ${YELLOW}[DRY-RUN]${NC} Würde ausführen: $PACTL set-sink-volume $SELECTED_SINK 75%"
    fi
  else
    echo -e "  ${GREEN}✓${NC} Lautstärke ist ausreichend"
  fi
fi
echo ""

# MUTE-Schalter prüfen (falls am Gehäuse vorhanden)
echo -e "${CYAN}[6] Wichtige Hinweise:${NC}"
echo -e "  ${BLUE}1.${NC} Falls Gehäuse einen MUTE-Schalter hat: prüfen (nicht bei allen vorhanden)"
echo -e "  ${BLUE}2.${NC} Bitte prüfen, ob die Lautsprecher physisch korrekt angeschlossen sind"
echo -e "  ${BLUE}3.${NC} Test mit: paplay /usr/share/sounds/alsa/Front_Left.wav"
echo ""

# Zusammenfassung
echo -e "${CYAN}[7] Zusammenfassung:${NC}"
if [ -z "$DRY_RUN" ]; then
  echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt: $SELECTED_SINK"
  echo -e "  ${GREEN}✓${NC} Konfiguration abgeschlossen"
  echo ""
  echo "Test:"
  echo "  paplay /usr/share/sounds/alsa/Front_Left.wav"
  echo ""
  echo "Falls kein Ton:"
  echo "  1. Falls vorhanden: MUTE-Schalter am Gehäuse prüfen"
  echo "  2. Lautsprecher-Verbindungen prüfen"
  echo "  3. Diagnose ausführen: ./scripts/diagnose-freenove-audio.sh"
else
  echo -e "  ${YELLOW}[DRY-RUN]${NC} Keine Änderungen vorgenommen"
  echo ""
  echo "Zum Ausführen ohne --dry-run:"
  echo "  ./scripts/configure-freenove-audio.sh"
fi
echo ""
