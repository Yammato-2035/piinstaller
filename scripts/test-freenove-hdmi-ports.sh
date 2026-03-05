#!/bin/bash
# PI-Installer: Freenove HDMI-Ports für Gehäuselautsprecher testen
#
# Testet beide HDMI-Ports, um herauszufinden, welcher zu den Gehäuselautsprechern führt.
# Das Mediaboard extrahiert Audio nur von einem bestimmten HDMI-Port.
#
# Ausführung: ./scripts/test-freenove-hdmi-ports.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove HDMI-Ports für Gehäuselautsprecher testen ===${NC}"
echo ""

# Prüfe ob wpctl verfügbar ist
if ! command -v wpctl >/dev/null 2>&1; then
  echo -e "${RED}✗${NC} wpctl nicht gefunden"
  exit 1
fi

# Prüfe ob pactl verfügbar ist
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -z "$PACTL" ]; then
  echo -e "${RED}✗${NC} pactl nicht gefunden"
  exit 1
fi

# Hole alle HDMI-Sinks (sowohl von wpctl als auch von pactl)
echo "Verfügbare HDMI-Sinks:"

# Versuche wpctl zuerst
HDMI_SINKS_WPCTL=$(wpctl status 2>/dev/null | grep -i "hdmi" | grep -E "^[[:space:]]*[0-9]+\." | awk '{print $1}' | sed 's/\.$//' || echo "")

# Fallback: Hole von pactl (alle HDMI-Sinks, auch suspendierte)
HDMI_SINKS_PACTL=""
if [ -n "$PACTL" ]; then
  # Hole alle HDMI-Sinks (auch die, die nicht in der Short-Liste erscheinen)
  HDMI_SINKS_PACTL=$($PACTL list sinks 2>/dev/null | grep -E "^Name:|alsa\.card" | grep -B1 "107c70" | grep "^Name:" | awk '{print $2}' || echo "")
  # Fallback: Wenn das nicht funktioniert, verwende die Short-Liste
  if [ -z "$HDMI_SINKS_PACTL" ]; then
    HDMI_SINKS_PACTL=$($PACTL list sinks short 2>/dev/null | grep -i "hdmi" | awk '{print $2}' || echo "")
  fi
fi

# Zeige alle HDMI-Sinks mit Details
if [ -n "$HDMI_SINKS_WPCTL" ]; then
  wpctl status 2>/dev/null | grep -i "hdmi" | while IFS= read -r line; do
    echo "  $line"
  done
elif [ -n "$HDMI_SINKS_PACTL" ]; then
  echo "$HDMI_SINKS_PACTL" | while IFS= read -r sink; do
    echo "  $sink"
  done
else
  echo -e "  ${RED}✗${NC} Keine HDMI-Sinks gefunden"
  exit 1
fi
echo ""

# Speichere aktuellen Standard-Sink
CURRENT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
echo -e "${CYAN}Aktueller Standard-Sink:${NC} ${CURRENT_SINK:-keiner}"
echo ""

# Teste jeden HDMI-Sink
echo -e "${CYAN}=== Teste jeden HDMI-Sink ===${NC}"
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Bitte prüfe, ob der Ton aus den ${BLUE}Gehäuselautsprechern${NC} kommt,"
echo "         nicht aus dem HDMI-Monitor!"
echo ""

SINK_COUNT=0
SUCCESSFUL_SINK=""
SUCCESSFUL_ID=""

# Sammle alle HDMI-Sinks (von beiden Quellen)
ALL_HDMI_SINKS=""

# Füge wpctl-Sinks hinzu
if [ -n "$HDMI_SINKS_WPCTL" ]; then
  for sink_id in $HDMI_SINKS_WPCTL; do
    ALL_HDMI_SINKS="$ALL_HDMI_SINKS wpctl:$sink_id"
  done
fi

# Füge pactl-Sinks hinzu (nur wenn noch nicht vorhanden)
if [ -n "$HDMI_SINKS_PACTL" ]; then
  for sink_name in $HDMI_SINKS_PACTL; do
    # Prüfe ob dieser Sink bereits in wpctl-Sinks vorhanden ist
    FOUND=false
    if [ -n "$HDMI_SINKS_WPCTL" ]; then
      for wpctl_id in $HDMI_SINKS_WPCTL; do
        PACTL_NAME=$($PACTL list sinks short 2>/dev/null | grep "^$wpctl_id" | awk '{print $2}' || echo "")
        if [ "$PACTL_NAME" = "$sink_name" ]; then
          FOUND=true
          break
        fi
      done
    fi
    if [ "$FOUND" = false ]; then
      ALL_HDMI_SINKS="$ALL_HDMI_SINKS pactl:$sink_name"
    fi
  done
fi

# Wenn keine Sinks gefunden wurden, versuche beide HDMI-Ports direkt zu testen
if [ -z "$ALL_HDMI_SINKS" ]; then
  echo -e "${YELLOW}⚠${NC} Keine HDMI-Sinks gefunden, versuche beide HDMI-Ports direkt..."
  # Versuche beide bekannten HDMI-Sinks
  ALL_HDMI_SINKS="pactl:alsa_output.platform-107c701400.hdmi.hdmi-stereo pactl:alsa_output.platform-107c706400.hdmi.hdmi-stereo"
fi

if [ -z "$ALL_HDMI_SINKS" ]; then
  echo -e "${RED}✗${NC} Keine HDMI-Sinks zum Testen gefunden"
  exit 1
fi

for sink_item in $ALL_HDMI_SINKS; do
  SINK_COUNT=$((SINK_COUNT + 1))
  
  # Parse sink_item (Format: "wpctl:70" oder "pactl:alsa_output.platform-...")
  if echo "$sink_item" | grep -q "^wpctl:"; then
    sink_id=$(echo "$sink_item" | sed 's/^wpctl://')
    USE_WPCTL=true
    # Hole Sink-Name von wpctl
    SINK_NAME=$(wpctl inspect "$sink_id" 2>/dev/null | grep -E "object.serial|node.name" | head -1 | awk '{print $NF}' | tr -d '"' || echo "")
    # Fallback: Hole Sink-Name von pactl
    if [ -z "$SINK_NAME" ]; then
      SINK_NAME=$($PACTL list sinks short 2>/dev/null | grep "^$sink_id" | awk '{print $2}' || echo "")
    fi
    if [ -z "$SINK_NAME" ]; then
      SINK_NAME="Sink-$sink_id"
    fi
  elif echo "$sink_item" | grep -q "^pactl:"; then
    SINK_NAME=$(echo "$sink_item" | sed 's/^pactl://')
    USE_WPCTL=false
    sink_id=""
    # Versuche wpctl-ID zu finden
    sink_id=$($PACTL list sinks short 2>/dev/null | grep "$SINK_NAME" | awk '{print $1}' || echo "")
  else
    # Fallback: Direkter Sink-Name
    SINK_NAME="$sink_item"
    USE_WPCTL=false
    sink_id=""
  fi
  
  echo -e "${CYAN}[Test $SINK_COUNT]${NC} $SINK_NAME${sink_id:+ (ID: $sink_id)}"
  echo ""
  
  # Setze als Standard-Sink
  echo "  Setze als Standard-Sink..."
  if [ "$USE_WPCTL" = true ] && [ -n "$sink_id" ]; then
    wpctl set-default "$sink_id" 2>/dev/null || {
      echo -e "  ${YELLOW}⚠${NC} Fehler beim Setzen mit wpctl, versuche pactl..."
      if [ -n "$PACTL" ] && [ "$SINK_NAME" != "Sink-$sink_id" ]; then
        $PACTL set-default-sink "$SINK_NAME" 2>/dev/null || {
          echo -e "  ${RED}✗${NC} Fehler beim Setzen des Sinks"
          continue
        }
      else
        continue
      fi
    }
  elif [ -n "$PACTL" ]; then
    $PACTL set-default-sink "$SINK_NAME" 2>/dev/null || {
      echo -e "  ${RED}✗${NC} Fehler beim Setzen des Sinks"
      continue
    }
  else
    echo -e "  ${RED}✗${NC} Weder wpctl noch pactl verfügbar"
    continue
  fi
  
  # Warte kurz
  sleep 1
  
  # Prüfe Lautstärke und stelle sicher, dass nicht stumm geschaltet ist
  echo "  Prüfe Lautstärke..."
  if [ "$USE_WPCTL" = true ] && [ -n "$sink_id" ] && command -v wpctl >/dev/null 2>&1; then
    VOLUME=$(wpctl get-volume "$sink_id" 2>/dev/null | awk '{print $2}' | sed 's/\.//' || echo "0")
    if [ "$VOLUME" -lt 50 ]; then
      echo "  Setze Lautstärke auf 0.70..."
      wpctl set-volume "$sink_id" 0.70 2>/dev/null || true
    fi
  elif [ -n "$PACTL" ]; then
    VOLUME=$($PACTL get-sink-volume "$SINK_NAME" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
    if [ "$VOLUME" -lt 50 ]; then
      echo "  Setze Lautstärke auf 70%..."
      $PACTL set-sink-volume "$SINK_NAME" 70% 2>/dev/null || true
    fi
  fi
  
  # Prüfe ob stumm geschaltet
  if [ -n "$PACTL" ]; then
    MUTED=$($PACTL get-sink-mute "$SINK_NAME" 2>/dev/null | awk '{print $2}' || echo "no")
    if [ "$MUTED" = "yes" ]; then
      echo "  Entstumme..."
      $PACTL set-sink-mute "$SINK_NAME" 0 2>/dev/null || true
    fi
  fi
  
  # Spiele Test-Ton ab
  echo -e "  ${BLUE}→${NC} Spiele Test-Ton ab..."
  
  # Verwende paplay mit einer Test-Datei oder generiere einen Test-Ton
  if command -v paplay >/dev/null 2>&1; then
    # Versuche eine Test-Datei zu finden
    TEST_FILE=""
    for test in /usr/share/sounds/freedesktop/stereo/bell.oga \
                /usr/share/sounds/alsa/Front_Left.wav \
                /usr/share/sounds/alsa/Front_Right.wav \
                /usr/share/sounds/alsa/Noise.wav; do
      if [ -f "$test" ]; then
        TEST_FILE="$test"
        break
      fi
    done
    
    if [ -n "$TEST_FILE" ]; then
      paplay --device="$SINK_NAME" "$TEST_FILE" 2>/dev/null &
      PA_PID=$!
      sleep 2
      kill $PA_PID 2>/dev/null || true
    else
      # Generiere einen Test-Ton mit sox oder speaker-test
      if command -v speaker-test >/dev/null 2>&1; then
        echo "  Verwende speaker-test..."
        timeout 2 speaker-test -c 2 -t sine -f 1000 -s 1 -D "$SINK_NAME" 2>/dev/null || true
      elif command -v sox >/dev/null 2>&1; then
        echo "  Generiere Test-Ton mit sox..."
        sox -n -t pulseaudio "$SINK_NAME" synth 1 sine 1000 2>/dev/null || true
      else
        echo -e "  ${YELLOW}⚠${NC} Kein Test-Ton-Tool gefunden (paplay/speaker-test/sox)"
      fi
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} paplay nicht gefunden"
  fi
  
  echo ""
  echo -e "  ${YELLOW}Kam der Ton aus den Gehäuselautsprechern?${NC}"
  echo -e "  ${CYAN}[j]${NC} Ja, dieser Sink funktioniert!"
  echo -e "  ${CYAN}[n]${NC} Nein, nur HDMI-Monitor"
  echo -e "  ${CYAN}[s]${NC} Überspringen"
  echo ""
  read -p "  Deine Antwort (j/n/s): " answer
  
  case "$answer" in
    [jJ]*)
      echo -e "  ${GREEN}✓${NC} Dieser Sink führt zu den Gehäuselautsprechern!"
      SUCCESSFUL_SINK="$SINK_NAME"
      if [ -n "$sink_id" ]; then
        SUCCESSFUL_ID="$sink_id"
      fi
      break
      ;;
    [nN]*)
      echo -e "  ${RED}✗${NC} Dieser Sink führt nur zum HDMI-Monitor"
      ;;
    [sS]*)
      echo -e "  ${YELLOW}→${NC} Übersprungen"
      ;;
    *)
      echo -e "  ${YELLOW}→${NC} Übersprungen (ungültige Eingabe)"
      ;;
  esac
  
  echo ""
  echo "---"
  echo ""
  
  # Reset für nächste Iteration
  sink_id=""
done

# Wiederherstelle ursprünglichen Standard-Sink oder setze den erfolgreichen
if [ -n "$SUCCESSFUL_SINK" ]; then
  echo -e "${GREEN}=== Erfolgreich! ===${NC}"
  echo ""
  echo "Der richtige Sink für die Gehäuselautsprecher ist:"
  echo -e "  ${GREEN}$SUCCESSFUL_SINK${NC} (ID: $SUCCESSFUL_ID)"
  echo ""
  echo "Setze als Standard-Sink..."
  if [ -n "$SUCCESSFUL_ID" ]; then
    wpctl set-default "$SUCCESSFUL_ID" 2>/dev/null || true
  fi
  if [ -n "$PACTL" ]; then
    $PACTL set-default-sink "$SUCCESSFUL_SINK" 2>/dev/null || true
  fi
  echo ""
  echo "Um diesen Sink dauerhaft zu setzen, füge folgendes zu deiner"
  echo "PipeWire/WirePlumber-Konfiguration hinzu oder verwende:"
  echo ""
  if [ -n "$SUCCESSFUL_ID" ]; then
    echo "  wpctl set-default $SUCCESSFUL_ID"
  fi
  if [ -n "$PACTL" ]; then
    echo "  pactl set-default-sink $SUCCESSFUL_SINK"
  fi
  echo ""
elif [ -n "$CURRENT_SINK" ]; then
  echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
  echo ""
  echo "Stelle ursprünglichen Standard-Sink wieder her:"
  echo "  $CURRENT_SINK"
  if [ -n "$PACTL" ]; then
    $PACTL set-default-sink "$CURRENT_SINK" 2>/dev/null || true
  fi
  echo ""
  echo -e "${YELLOW}Hinweis:${NC} Das Mediaboard könnte:"
  echo "  1. Eine spezielle Konfiguration benötigen"
  echo "  2. Nur funktionieren, wenn kein Monitor angeschlossen ist"
  echo "  3. Über ALSA direkt angesprochen werden müssen"
  echo "  4. Nur von einem bestimmten HDMI-Port (HDMI-A-1 oder HDMI-A-2) extrahieren"
  echo ""
else
  echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
  echo ""
fi

echo -e "${GREEN}Fertig.${NC}"
