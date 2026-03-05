#!/bin/bash
# PI-Installer: Raspberry Pi – Alle Audio-Ausgänge finden
#
# Prüft alle möglichen Audio-Ausgänge auf dem Raspberry Pi:
# - HDMI (beide Ports)
# - I2S (für externe Audio-Boards)
# - USB-Audio
# - Bluetooth-Audio
# - ALSA-Karten
#
# Ausführung: ./scripts/diagnose-pi-audio-outputs.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Raspberry Pi – Alle Audio-Ausgänge finden ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${YELLOW}⚠${NC} Nicht auf Raspberry Pi"
  exit 1
fi

PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null | tr -d '\0' || echo "")
echo -e "${CYAN}Gerät:${NC} $PI_MODEL"
echo ""

# 1. ALSA-Karten (alle verfügbaren Audio-Geräte)
echo -e "${CYAN}[1] ALSA-Karten (alle Audio-Hardware):${NC}"
if [ -f /proc/asound/cards ]; then
  cat /proc/asound/cards | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${RED}✗${NC} /proc/asound/cards nicht gefunden"
fi
echo ""

# 2. ALSA-Devices (detailliert)
echo -e "${CYAN}[2] ALSA-Devices (aplay -l):${NC}"
if command -v aplay >/dev/null 2>&1; then
  aplay -l 2>/dev/null | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} aplay nicht gefunden"
fi
echo ""

# 3. PulseAudio/PipeWire Sinks
echo -e "${CYAN}[3] PulseAudio/PipeWire Sinks:${NC}"
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -n "$PACTL" ]; then
  echo -e "  ${GREEN}✓${NC} pactl gefunden: $PACTL"
  echo ""
  echo "  Verfügbare Sinks:"
  SINKS_LIST=$($PACTL list short sinks 2>/dev/null || echo "")
  if [ -n "$SINKS_LIST" ]; then
    echo "$SINKS_LIST" | while IFS= read -r line; do
      echo "    $line"
    done
  else
    echo -e "    ${YELLOW}⚠${NC} Keine Sinks gefunden"
  fi
  echo ""
  echo "  Standard-Sink:"
  DEFAULT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
  if [ -n "$DEFAULT_SINK" ]; then
    echo "    $DEFAULT_SINK"
  else
    echo -e "    ${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
  fi
  echo ""
  echo "  Detaillierte Sink-Informationen (ALSA-Karte, Gerätename, etc.):"
  $PACTL list sinks 2>/dev/null | grep -E "^(Sink|Name:|Description:|State:|alsa\.card|alsa\.device|device\.product\.name|device\.string)" | head -50 | while IFS= read -r line; do
    echo "    $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} pactl nicht gefunden"
fi
echo ""

# 4. I2S-Audio (für externe Audio-Boards)
echo -e "${CYAN}[4] I2S-Audio-Ausgänge prüfen:${NC}"
# Prüfe config.txt auf I2S-Overlays
CONFIG_FILE="/boot/firmware/config.txt"
[ ! -f "$CONFIG_FILE" ] && CONFIG_FILE="/boot/config.txt"

if [ -f "$CONFIG_FILE" ]; then
  I2S_OVERLAYS=$(grep -i "dtoverlay.*i2s\|dtoverlay.*audio" "$CONFIG_FILE" 2>/dev/null || echo "")
  if [ -n "$I2S_OVERLAYS" ]; then
    echo "  I2S-Overlays in config.txt gefunden:"
    echo "$I2S_OVERLAYS" | while IFS= read -r line; do
      echo "    $line"
    done
  else
    echo -e "  ${YELLOW}⚠${NC} Keine I2S-Overlays in config.txt gefunden"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} config.txt nicht gefunden"
fi

# Prüfe ob I2S-Geräte vorhanden sind
if [ -d /proc/asound ]; then
  I2S_CARDS=$(grep -i "i2s\|i2c.*audio" /proc/asound/cards 2>/dev/null || echo "")
  if [ -n "$I2S_CARDS" ]; then
    echo "  I2S-Geräte gefunden:"
    echo "$I2S_CARDS" | while IFS= read -r line; do
      echo "    $line"
    done
  fi
fi
echo ""

# 5. USB-Audio-Geräte
echo -e "${CYAN}[5] USB-Audio-Geräte:${NC}"
USB_AUDIO=$(lsusb 2>/dev/null | grep -i "audio\|sound\|speaker\|headphone" || echo "")
if [ -n "$USB_AUDIO" ]; then
  echo "$USB_AUDIO" | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} Keine USB-Audio-Geräte gefunden"
fi
echo ""

# 6. Bluetooth-Audio
echo -e "${CYAN}[6] Bluetooth-Audio-Geräte:${NC}"
if command -v bluetoothctl >/dev/null 2>&1; then
  BT_DEVICES=$(bluetoothctl devices 2>/dev/null | grep -i "audio\|headphone\|speaker" || echo "")
  if [ -n "$BT_DEVICES" ]; then
    echo "$BT_DEVICES" | while IFS= read -r line; do
      echo "  $line"
    done
  else
    echo -e "  ${YELLOW}⚠${NC} Keine Bluetooth-Audio-Geräte gefunden"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} bluetoothctl nicht gefunden"
fi
echo ""

# 7. ALSA-Control-Devices (für alle Karten)
echo -e "${CYAN}[7] ALSA-Control-Devices (für alle Karten):${NC}"
if command -v amixer >/dev/null 2>&1; then
  for card in 0 1 2 3 4 5; do
    if [ -d "/proc/asound/card$card" ]; then
      echo "  Card $card:"
      amixer -c $card scontrols 2>/dev/null | head -5 | while IFS= read -r line; do
        echo "    $line"
      done
    fi
  done
else
  echo -e "  ${YELLOW}⚠${NC} amixer nicht gefunden"
fi
echo ""

# 8. Device Tree Overlays (Audio-bezogen)
echo -e "${CYAN}[8] Device Tree Overlays (Audio-bezogen):${NC}"
if [ -f "$CONFIG_FILE" ]; then
  AUDIO_OVERLAYS=$(grep -E "dtoverlay.*audio|dtoverlay.*i2s|dtoverlay.*sound|dtparam.*audio" "$CONFIG_FILE" 2>/dev/null || echo "")
  if [ -n "$AUDIO_OVERLAYS" ]; then
    echo "$AUDIO_OVERLAYS" | while IFS= read -r line; do
      echo "  $line"
    done
  else
    echo -e "  ${YELLOW}⚠${NC} Keine Audio-Overlays in config.txt gefunden"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} config.txt nicht gefunden"
fi
echo ""

# 9. PCIe-Audio-Geräte (Freenove Mediaboard könnte über PCIe angeschlossen sein)
echo -e "${CYAN}[9] PCIe-Audio-Geräte prüfen:${NC}"
PCI_AUDIO=$(lspci 2>/dev/null | grep -i "audio\|sound\|multimedia" || echo "")
if [ -n "$PCI_AUDIO" ]; then
  echo "  PCIe-Audio-Geräte gefunden:"
  echo "$PCI_AUDIO" | while IFS= read -r line; do
    echo "    $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} Keine PCIe-Audio-Geräte gefunden"
fi
echo ""

# 10. Sysfs Audio-Geräte
echo -e "${CYAN}[10] Sysfs Audio-Geräte (/sys/class/sound):${NC}"
if [ -d /sys/class/sound ]; then
  echo "  Verfügbare Sound-Geräte:"
  ls -la /sys/class/sound/ 2>/dev/null | grep -v "^total\|^d.*\.$" | while IFS= read -r line; do
    echo "    $line"
  done
  
  # Detaillierte Informationen für jede Sound-Karte
  echo ""
  echo "  Detaillierte Informationen:"
  for card_dir in /sys/class/sound/card*; do
    if [ -d "$card_dir" ]; then
      CARD_NAME=$(basename "$card_dir")
      if [ -f "$card_dir/id" ]; then
        CARD_ID=$(cat "$card_dir/id" 2>/dev/null || echo "?")
        echo "    $CARD_NAME: $CARD_ID"
        # Prüfe ob es PCIe-Gerät ist
        if [ -d "$card_dir/device" ]; then
          PCI_PATH=$(readlink -f "$card_dir/device" 2>/dev/null || echo "")
          if echo "$PCI_PATH" | grep -q "/pci"; then
            echo "      PCIe-Gerät: $PCI_PATH"
          fi
        fi
      fi
    fi
  done
else
  echo -e "  ${YELLOW}⚠${NC} /sys/class/sound nicht gefunden"
fi
echo ""

# 11. Freenove Mediaboard – Spezielle Prüfung
echo -e "${CYAN}[11] Freenove Mediaboard – Spezielle Prüfung:${NC}"
echo "  Das Mediaboard ist über PCIe angeschlossen und extrahiert Audio aus HDMI."
echo "  Prüfe ob es als separates Audio-Gerät erkannt wird..."
echo ""

# Prüfe ob Freenove-Gehäuse erkannt wird
FREENOVE_DETECTED=false
for bus in 1 0 6 7; do
  if i2cget -y $bus 0x21 0xfd 2>/dev/null | grep -q .; then
    FREENOVE_DETECTED=true
    break
  fi
done

if [ "$FREENOVE_DETECTED" = true ]; then
  echo -e "  ${GREEN}✓${NC} Freenove-Gehäuse erkannt (I2C Expansion-Board)"
  echo ""
  echo "  Das Mediaboard sollte Audio aus HDMI extrahieren."
  echo "  Prüfe ob es ein separates Audio-Gerät gibt:"
  
  # Suche nach Audio-Geräten, die nicht HDMI sind
  NON_HDMI_SINKS=()
  if [ -n "$PACTL" ]; then
    SINKS=$($PACTL list short sinks 2>/dev/null || echo "")
    if [ -n "$SINKS" ]; then
      while IFS= read -r line; do
        if echo "$line" | grep -qi "hdmi"; then
          continue
        fi
        SINK_NAME=$(echo "$line" | awk '{print $2}')
        if [ -n "$SINK_NAME" ]; then
          NON_HDMI_SINKS+=("$SINK_NAME")
        fi
      done <<< "$SINKS"
    fi
  fi
  
  if [ ${#NON_HDMI_SINKS[@]} -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Non-HDMI Audio-Sinks gefunden (möglicherweise Mediaboard):"
    for sink in "${NON_HDMI_SINKS[@]}"; do
      echo "    - $sink"
      # Detaillierte Informationen zu diesem Sink
      $PACTL list sinks 2>/dev/null | grep -A20 "Name: $sink" | grep -E "Description:|alsa\.card|alsa\.device|device\." | head -5 | while IFS= read -r detail; do
        echo "      $detail"
      done
    done
    echo ""
    echo -e "  ${BLUE}→${NC} Teste diese Non-HDMI-Sinks für die Gehäuselautsprecher!"
  else
    echo -e "  ${YELLOW}⚠${NC} Keine Non-HDMI Audio-Sinks gefunden"
    echo "  Das Mediaboard könnte:"
    echo "    1. Als HDMI-Gerät erscheinen (extrahiert Audio aus HDMI)"
    echo "    2. Eine spezielle Konfiguration benötigen"
    echo "    3. Über ALSA direkt angesprochen werden müssen"
    echo ""
    echo "  Prüfe alle verfügbaren ALSA-Karten oben und teste jeden einzeln."
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Freenove-Gehäuse nicht erkannt"
fi
echo ""

# 12. Zusammenfassung
echo -e "${CYAN}[12] Zusammenfassung:${NC}"
ALSA_CARDS=$(cat /proc/asound/cards 2>/dev/null | grep -E "^[[:space:]]*[0-9]" | wc -l)
PULSE_SINKS=0
if [ -n "$PACTL" ]; then
  PULSE_SINKS=$($PACTL list short sinks 2>/dev/null | wc -l)
fi

echo "  ALSA-Karten: $ALSA_CARDS"
echo "  PulseAudio/PipeWire Sinks: $PULSE_SINKS"
echo ""
echo "Verfügbare Audio-Ausgänge:"
HDMI_COUNT=0
if [ -n "$PACTL" ]; then
  HDMI_COUNT=$($PACTL list short sinks 2>/dev/null | grep -ci "hdmi" || echo "0")
fi
echo "  - HDMI: $HDMI_COUNT Port(s)"
echo "  - I2S: $(grep -ci "i2s" /proc/asound/cards 2>/dev/null || echo "0")"
echo "  - USB-Audio: $(lsusb 2>/dev/null | grep -ci "audio\|sound" || echo "0")"
echo "  - Bluetooth-Audio: $(bluetoothctl devices 2>/dev/null | grep -ci "audio\|headphone\|speaker" || echo "0")"
echo "  - PCIe-Audio: $(lspci 2>/dev/null | grep -ci "audio\|sound\|multimedia" || echo "0")"
echo ""
echo "WICHTIG für Freenove:"
echo "  Das Mediaboard ist über PCIe angeschlossen und extrahiert Audio aus HDMI."
echo "  Es könnte als separates Audio-Gerät erscheinen oder über HDMI geroutet werden."
echo "  Prüfe alle verfügbaren Sinks oben und teste jeden einzeln."
echo ""

echo -e "${GREEN}Fertig.${NC} Bitte alle Audio-Ausgänge prüfen und den richtigen für die Gehäuselautsprecher finden."
echo ""
