#!/bin/bash
# PI-Installer: Audio-Test nach Neustart
#
# Wird nach einem Neustart ausgeführt, um zu prüfen, ob HDMI-A-1 als Sink verfügbar ist.
# Kann auch manuell ausgeführt werden.
#
# Ausführung: ./scripts/audio-test-after-reboot.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_FILE="$HOME/audio-test-after-reboot-$(date +%Y%m%d_%H%M%S).log"

echo -e "${CYAN}=== Audio-Test nach Neustart ===${NC}" | tee "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Prüfe ob pactl verfügbar ist
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -z "$PACTL" ]; then
  echo -e "${RED}✗${NC} pactl nicht gefunden" | tee -a "$LOG_FILE"
  exit 1
fi

echo "Log-Datei: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Prüfe cmdline.txt
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"

echo -e "${CYAN}[1] cmdline.txt prüfen:${NC}" | tee -a "$LOG_FILE"
if [ -f "$CMDLINE_FILE" ]; then
  if grep -q "video=HDMI-A-1" "$CMDLINE_FILE"; then
    echo -e "${GREEN}✓${NC} video=HDMI-A-1 gefunden" | tee -a "$LOG_FILE"
    grep "video=HDMI-A-1" "$CMDLINE_FILE" | tee -a "$LOG_FILE"
  else
    echo -e "${YELLOW}⚠${NC} video=HDMI-A-1 nicht gefunden" | tee -a "$LOG_FILE"
  fi
else
  echo -e "${RED}✗${NC} cmdline.txt nicht gefunden" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Prüfe ALSA-Karten
echo -e "${CYAN}[2] ALSA-Karten:${NC}" | tee -a "$LOG_FILE"
aplay -l 2>/dev/null | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Prüfe verfügbare Sinks
echo -e "${CYAN}[3] Verfügbare PipeWire/PulseAudio Sinks:${NC}" | tee -a "$LOG_FILE"
ALL_SINKS=$(pactl list sinks short 2>/dev/null || echo "")
if [ -n "$ALL_SINKS" ]; then
  echo "$ALL_SINKS" | tee -a "$LOG_FILE"
  
  # Prüfe ob HDMI-A-1 verfügbar ist
  if echo "$ALL_SINKS" | grep -q "107c701400"; then
    echo "" | tee -a "$LOG_FILE"
    echo -e "${GREEN}✓${NC} HDMI-A-1 ist als Sink verfügbar!" | tee -a "$LOG_FILE"
    HDMI_A1_SINK=$(echo "$ALL_SINKS" | grep "107c701400" | awk '{print $2}')
    echo "  Sink: $HDMI_A1_SINK" | tee -a "$LOG_FILE"
    
    # Teste HDMI-A-1
    echo "" | tee -a "$LOG_FILE"
    echo -e "${CYAN}[4] Teste HDMI-A-1:${NC}" | tee -a "$LOG_FILE"
    pactl set-default-sink "$HDMI_A1_SINK" 2>/dev/null || true
    pactl set-sink-volume "$HDMI_A1_SINK" 70% 2>/dev/null || true
    pactl set-sink-mute "$HDMI_A1_SINK" 0 2>/dev/null || true
    sleep 1
    
    echo "  Spiele Test-Ton..." | tee -a "$LOG_FILE"
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
        paplay --device="$HDMI_A1_SINK" "$TEST_FILE" 2>&1 | tee -a "$LOG_FILE" &
        PA_PID=$!
        sleep 2
        kill $PA_PID 2>/dev/null || true
        echo "  Test-Ton abgespielt" | tee -a "$LOG_FILE"
        echo "" | tee -a "$LOG_FILE"
        echo -e "${YELLOW}→${NC} Prüfe Gehäuselautsprecher!" | tee -a "$LOG_FILE"
      fi
    fi
  else
    echo "" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist nicht als Sink verfügbar" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Mögliche Ursachen:" | tee -a "$LOG_FILE"
    echo "  1. Neustart wurde noch nicht durchgeführt" | tee -a "$LOG_FILE"
    echo "  2. WirePlumber erstellt den Sink nicht automatisch" | tee -a "$LOG_FILE"
    echo "  3. HDMI-A-1 läuft im IEC958-Modus (S/PDIF) und wird nicht als PCM-Sink erkannt" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Lösungen:" | tee -a "$LOG_FILE"
    echo "  1. Neustart durchführen: sudo reboot" | tee -a "$LOG_FILE"
    echo "  2. WirePlumber neu starten: systemctl --user restart wireplumber" | tee -a "$LOG_FILE"
    echo "  3. Prüfe ALSA direkt: aplay -D hw:0,0 --dump-hw-params /dev/zero" | tee -a "$LOG_FILE"
  fi
else
  echo -e "${RED}✗${NC} Keine Sinks gefunden" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo -e "${GREEN}Fertig.${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Log-Datei: $LOG_FILE" | tee -a "$LOG_FILE"
