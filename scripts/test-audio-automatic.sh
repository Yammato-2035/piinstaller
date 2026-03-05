#!/bin/bash
# PI-Installer: Automatischer Audio-Test (ohne Monitor)
#
# Testet Audio automatisch ohne Benutzerinteraktion.
# Läuft im Hintergrund und gibt Ergebnisse in eine Log-Datei aus.
#
# Ausführung: ./scripts/test-audio-automatic.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_FILE="$HOME/audio-test-$(date +%Y%m%d_%H%M%S).log"

echo -e "${CYAN}=== Automatischer Audio-Test ===${NC}" | tee "$LOG_FILE"
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

# Teste beide HDMI-Sinks
HDMI_SINK_1="alsa_output.platform-107c701400.hdmi.hdmi-stereo"  # HDMI-A-1
HDMI_SINK_2="alsa_output.platform-107c706400.hdmi.hdmi-stereo"  # HDMI-A-2

echo -e "${CYAN}[1] Verfügbare Sinks:${NC}" | tee -a "$LOG_FILE"
pactl list sinks short 2>/dev/null | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo -e "${CYAN}[2] Teste HDMI-A-1 ($HDMI_SINK_1):${NC}" | tee -a "$LOG_FILE"
if pactl list sinks short 2>/dev/null | grep -q "$HDMI_SINK_1"; then
  echo "  Sink gefunden" | tee -a "$LOG_FILE"
  pactl set-default-sink "$HDMI_SINK_1" 2>/dev/null || true
  pactl set-sink-volume "$HDMI_SINK_1" 70% 2>/dev/null || true
  pactl set-sink-mute "$HDMI_SINK_1" 0 2>/dev/null || true
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
      paplay --device="$HDMI_SINK_1" "$TEST_FILE" 2>&1 | tee -a "$LOG_FILE" &
      PA_PID=$!
      sleep 2
      kill $PA_PID 2>/dev/null || true
      echo "  Test-Ton abgespielt" | tee -a "$LOG_FILE"
    fi
  fi
  echo "  → Prüfe Gehäuselautsprecher!" | tee -a "$LOG_FILE"
else
  echo "  ⚠ Sink nicht gefunden" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

echo -e "${CYAN}[3] Teste HDMI-A-2 ($HDMI_SINK_2):${NC}" | tee -a "$LOG_FILE"
if pactl list sinks short 2>/dev/null | grep -q "$HDMI_SINK_2"; then
  echo "  Sink gefunden" | tee -a "$LOG_FILE"
  pactl set-default-sink "$HDMI_SINK_2" 2>/dev/null || true
  pactl set-sink-volume "$HDMI_SINK_2" 70% 2>/dev/null || true
  pactl set-sink-mute "$HDMI_SINK_2" 0 2>/dev/null || true
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
      paplay --device="$HDMI_SINK_2" "$TEST_FILE" 2>&1 | tee -a "$LOG_FILE" &
      PA_PID=$!
      sleep 2
      kill $PA_PID 2>/dev/null || true
      echo "  Test-Ton abgespielt" | tee -a "$LOG_FILE"
    fi
  fi
  echo "  → Prüfe Gehäuselautsprecher!" | tee -a "$LOG_FILE"
else
  echo "  ⚠ Sink nicht gefunden" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

echo -e "${CYAN}[4] ALSA-Karten:${NC}" | tee -a "$LOG_FILE"
aplay -l 2>/dev/null | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo -e "${CYAN}[5] cmdline.txt:${NC}" | tee -a "$LOG_FILE"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"
if [ -f "$CMDLINE_FILE" ]; then
  grep "video=HDMI" "$CMDLINE_FILE" | tee -a "$LOG_FILE" || echo "  Keine video=HDMI-Einträge" | tee -a "$LOG_FILE"
else
  echo "  cmdline.txt nicht gefunden" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

echo -e "${GREEN}Fertig.${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Log-Datei: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "WICHTIG: HDMI-A-1 ist nicht als Sink verfügbar!" | tee -a "$LOG_FILE"
echo "Ein Neustart ist erforderlich, damit HDMI-A-1 aktiv wird." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Nach dem Neustart prüfen mit:" | tee -a "$LOG_FILE"
echo "  ./scripts/audio-test-after-reboot.sh" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Prüfe die Log-Datei:" | tee -a "$LOG_FILE"
echo "  cat $LOG_FILE" | tee -a "$LOG_FILE"
