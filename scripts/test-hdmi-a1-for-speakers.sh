#!/bin/bash
# PI-Installer: HDMI-A-1 für Freenove Gehäuselautsprecher aktivieren und testen
#
# Aktiviert HDMI-A-1 (107c701400) als Audio-Sink, auch wenn dort kein Monitor angeschlossen ist.
# Das Mediaboard könnte Audio von diesem Port extrahieren müssen.
#
# Ausführung: ./scripts/test-hdmi-a1-for-speakers.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== HDMI-A-1 für Freenove Gehäuselautsprecher aktivieren ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${RED}✗${NC} Nicht auf Raspberry Pi"
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

HDMI_A1_SINK="alsa_output.platform-107c701400.hdmi.hdmi-stereo"
HDMI_A2_SINK="alsa_output.platform-107c706400.hdmi.hdmi-stereo"

echo -e "${CYAN}Problem:${NC}"
echo "  Monitor ist auf HDMI-A-2 ($HDMI_A2_SINK)"
echo "  Mediaboard könnte Audio von HDMI-A-1 ($HDMI_A1_SINK) extrahieren müssen"
echo "  HDMI-A-1 wird nicht als Sink angezeigt, weil dort kein Monitor angeschlossen ist"
echo ""

# Prüfe verfügbare Sinks
echo -e "${CYAN}Verfügbare HDMI-Sinks:${NC}"
ALL_SINKS=$($PACTL list sinks short 2>/dev/null || echo "")
echo "$ALL_SINKS" | while IFS= read -r line; do
  echo "  $line"
done
echo ""

# Prüfe ob HDMI-A-1 als Sink existiert
HDMI_A1_EXISTS=false
if echo "$ALL_SINKS" | grep -q "$HDMI_A1_SINK"; then
  HDMI_A1_EXISTS=true
  echo -e "${GREEN}✓${NC} HDMI-A-1 ist als Sink verfügbar: $HDMI_A1_SINK"
else
  echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist nicht als Sink verfügbar"
  echo ""
  echo "HDMI-A-1 muss aktiviert werden, auch wenn dort kein Monitor angeschlossen ist."
  echo ""
  echo "Lösung: In /boot/firmware/cmdline.txt ergänzen:"
  echo "  video=HDMI-A-1:e"
  echo ""
  echo "Oder mit fixer Auflösung:"
  echo "  video=HDMI-A-1:1920x1080@60D"
  echo ""
  echo -e "${BLUE}→${NC} Möchtest du das jetzt konfigurieren? (erfordert Neustart)"
  read -p "  [j] Ja, konfigurieren / [n] Nein, später: " answer
  
  if [[ "$answer" =~ ^[jJ] ]]; then
    if [ "$EUID" -ne 0 ]; then
      echo -e "${RED}✗${NC} Bitte als root ausführen (sudo)"
      exit 1
    fi
    
    CMDLINE_FILE="/boot/firmware/cmdline.txt"
    [ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"
    
    if [ ! -f "$CMDLINE_FILE" ]; then
      echo -e "${RED}✗${NC} cmdline.txt nicht gefunden: $CMDLINE_FILE"
      exit 1
    fi
    
    # Backup erstellen
    BACKUP_FILE="${CMDLINE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CMDLINE_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓${NC} Backup erstellt: $BACKUP_FILE"
    
    # Prüfe ob bereits konfiguriert
    CURRENT_CMDLINE=$(cat "$CMDLINE_FILE")
    if echo "$CURRENT_CMDLINE" | grep -q "video=HDMI-A-1"; then
      echo -e "${GREEN}✓${NC} HDMI-A-1 ist bereits in cmdline.txt konfiguriert"
    else
      # Entferne alte video=HDMI-Einträge (falls vorhanden)
      NEW_CMDLINE=$(echo "$CURRENT_CMDLINE" | sed 's/video=HDMI[^ ]*//g' | sed 's/  */ /g')
      
      # Füge video=HDMI-A-1:e hinzu
      VIDEO_PARAM="video=HDMI-A-1:e"
      if [ "$(tail -c 1 "$CMDLINE_FILE")" != "" ]; then
        NEW_CMDLINE="$NEW_CMDLINE $VIDEO_PARAM"
      else
        NEW_CMDLINE="$NEW_CMDLINE $VIDEO_PARAM"
      fi
      
      echo "$NEW_CMDLINE" > "$CMDLINE_FILE"
      echo -e "${GREEN}✓${NC} cmdline.txt aktualisiert: $VIDEO_PARAM"
      echo ""
      echo -e "${YELLOW}⚠${NC} Neustart erforderlich!"
      echo ""
      echo "Nach dem Neustart sollte HDMI-A-1 als Sink verfügbar sein."
      echo "Dann kannst du diesen Sink testen:"
      echo "  ./scripts/test-both-hdmi-sinks.sh"
      exit 0
    fi
  else
    echo ""
    echo "Du kannst später konfigurieren mit:"
    echo "  sudo ./scripts/enable-hdmi-audio-without-monitor.sh HDMI-A-1"
    exit 0
  fi
fi

# Wenn HDMI-A-1 verfügbar ist, teste es
if [ "$HDMI_A1_EXISTS" = true ]; then
  echo ""
  echo -e "${CYAN}Teste HDMI-A-1:${NC}"
  echo ""
  
  # Speichere aktuellen Standard-Sink
  CURRENT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
  echo "Aktueller Standard-Sink: ${CURRENT_SINK:-keiner}"
  echo ""
  
  # Setze HDMI-A-1 als Standard-Sink
  echo "Setze HDMI-A-1 als Standard-Sink..."
  $PACTL set-default-sink "$HDMI_A1_SINK" 2>/dev/null || {
    echo -e "${RED}✗${NC} Fehler beim Setzen des Sinks"
    exit 1
  }
  
  # Warte kurz
  sleep 1
  
  # Prüfe Lautstärke
  VOLUME=$($PACTL get-sink-volume "$HDMI_A1_SINK" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
  if [ "$VOLUME" -lt 50 ]; then
    echo "Setze Lautstärke auf 70%..."
    $PACTL set-sink-volume "$HDMI_A1_SINK" 70% 2>/dev/null || true
  fi
  
  # Prüfe ob stumm geschaltet
  MUTED=$($PACTL get-sink-mute "$HDMI_A1_SINK" 2>/dev/null | awk '{print $2}' || echo "no")
  if [ "$MUTED" = "yes" ]; then
    echo "Entstumme..."
    $PACTL set-sink-mute "$HDMI_A1_SINK" 0 2>/dev/null || true
  fi
  
  # Spiele Test-Ton ab
  echo -e "${BLUE}→${NC} Spiele Test-Ton ab..."
  
  if command -v paplay >/dev/null 2>&1; then
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
      paplay --device="$HDMI_A1_SINK" "$TEST_FILE" 2>/dev/null &
      PA_PID=$!
      sleep 2
      kill $PA_PID 2>/dev/null || true
    else
      echo -e "${YELLOW}⚠${NC} Keine Test-Datei gefunden"
    fi
  else
    echo -e "${YELLOW}⚠${NC} paplay nicht gefunden"
  fi
  
  echo ""
  echo -e "${YELLOW}Kam der Ton aus den Gehäuselautsprechern?${NC}"
  echo -e "${CYAN}[j]${NC} Ja, HDMI-A-1 funktioniert!"
  echo -e "${CYAN}[n]${NC} Nein, immer noch kein Ton"
  echo ""
  read -p "Deine Antwort (j/n): " answer
  
  case "$answer" in
    [jJ]*)
      echo -e "${GREEN}✓${NC} HDMI-A-1 führt zu den Gehäuselautsprechern!"
      echo ""
      echo "HDMI-A-1 ist jetzt als Standard-Sink gesetzt."
      echo "Der Ton sollte jetzt aus den Gehäuselautsprechern kommen."
      ;;
    [nN]*)
      echo -e "${RED}✗${NC} HDMI-A-1 funktioniert auch nicht"
      echo ""
      if [ -n "$CURRENT_SINK" ]; then
        echo "Stelle ursprünglichen Standard-Sink wieder her: $CURRENT_SINK"
        $PACTL set-default-sink "$CURRENT_SINK" 2>/dev/null || true
      fi
      echo ""
      echo "Mögliche Ursachen:"
      echo "  1. Hardware-Problem (Lautsprecher-Verbindungen, Mediaboard)"
      echo "  2. Mediaboard funktioniert nur ohne angeschlossenen Monitor"
      echo "  3. Defektes Mediaboard"
      echo ""
      echo "Siehe: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md"
      ;;
    *)
      echo -e "${YELLOW}→${NC} Ungültige Eingabe"
      if [ -n "$CURRENT_SINK" ]; then
        $PACTL set-default-sink "$CURRENT_SINK" 2>/dev/null || true
      fi
      ;;
  esac
fi

echo ""
echo -e "${GREEN}Fertig.${NC}"
