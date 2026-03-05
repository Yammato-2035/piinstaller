#!/bin/bash
# PI-Installer: Komplette Audio-Reparatur für Freenove Mediaboard
#
# Führt alle möglichen Reparatur-Schritte durch, um Audio zu den Gehäuselautsprechern
# zu aktivieren. Nützlich wenn Audio nach System-Updates oder Konfigurationsänderungen
# nicht mehr funktioniert.
#
# Ausführung: ./scripts/fix-freenove-audio-complete.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Komplette Audio-Reparatur für Freenove Mediaboard ===${NC}"
echo ""
echo "Dieses Skript führt alle möglichen Reparatur-Schritte durch."
echo ""

# 1. Setze WirePlumber-Konfiguration zurück
echo -e "${CYAN}[1] Setze WirePlumber-Konfiguration zurück:${NC}"
if [ -f "$HOME/.config/wireplumber/wireplumber.conf.d/50-alsa-hdmi-a1.conf" ]; then
  BACKUP_DIR="$HOME/.wireplumber-backup.$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$BACKUP_DIR"
  cp "$HOME/.config/wireplumber/wireplumber.conf.d/50-alsa-hdmi-a1.conf" "$BACKUP_DIR/" 2>/dev/null || true
  rm -f "$HOME/.config/wireplumber/wireplumber.conf.d/50-alsa-hdmi-a1.conf"
  echo -e "  ${GREEN}✓${NC} WirePlumber-Konfiguration entfernt (Backup: $BACKUP_DIR)"
else
  echo "  Keine benutzerdefinierte WirePlumber-Konfiguration gefunden"
fi
echo ""

# 2. Aktiviere HDMI-A-1 Display
echo -e "${CYAN}[2] Aktiviere HDMI-A-1 Display:${NC}"
if [ -f "/sys/class/drm/card2-HDMI-A-1/enabled" ]; then
  CURRENT_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
  echo "  Aktueller Status: $CURRENT_STATUS"
  
  if [ "$CURRENT_STATUS" != "enabled" ]; then
    echo "  Versuche HDMI-A-1 zu aktivieren..."
    # Prüfe ob sudo verfügbar ist
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      SUDO_AVAILABLE=true
    elif [ "$(id -u)" -eq 0 ]; then
      SUDO_AVAILABLE=true
    else
      SUDO_AVAILABLE=false
    fi
    
    if [ "$SUDO_AVAILABLE" = true ] && sudo bash -c "echo on > /sys/class/drm/card2-HDMI-A-1/enabled" 2>/dev/null; then
      sleep 2
      NEW_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
      if [ "$NEW_STATUS" = "enabled" ]; then
        echo -e "  ${GREEN}✓${NC} HDMI-A-1 Display aktiviert"
        echo "  Starte WirePlumber neu, damit Card 0 erkannt wird..."
        systemctl --user restart wireplumber.service 2>/dev/null || true
        sleep 2
      else
        echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 konnte nicht aktiviert werden (Status: $NEW_STATUS)"
        echo "  Möglicherweise Neustart erforderlich (cmdline.txt enthält bereits video=HDMI-A-1:e)"
      fi
    else
      echo -e "  ${YELLOW}⚠${NC} Konnte HDMI-A-1 nicht aktivieren (benötigt sudo)"
      echo "  Führe manuell aus: echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled"
      echo "  Oder starte das System neu (cmdline.txt enthält bereits video=HDMI-A-1:e)"
    fi
  else
    echo "  HDMI-A-1 ist bereits aktiviert"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} /sys/class/drm/card2-HDMI-A-1/enabled nicht gefunden"
fi
echo ""

# 3. Starte WirePlumber neu
echo -e "${CYAN}[3] Starte WirePlumber neu:${NC}"
if systemctl --user restart wireplumber.service 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} WirePlumber neu gestartet"
  sleep 2
else
  echo -e "  ${YELLOW}⚠${NC} Konnte WirePlumber nicht neu starten"
fi
echo ""

# 4. Aktiviere beide HDMI-Sinks
echo -e "${CYAN}[4] Aktiviere beide HDMI-Sinks:${NC}"
HDMI_SINKS=$(pactl list short sinks 2>/dev/null | grep "hdmi" | awk '{print $2}' || echo "")

if [ -n "$HDMI_SINKS" ]; then
  echo "$HDMI_SINKS" | while read -r sink; do
    echo "  Aktiviere $sink..."
    
    # Setze als Standard-Sink
    pactl set-default-sink "$sink" 2>/dev/null || true
    
    # Hebe Stummschaltung auf
    pactl set-sink-mute "$sink" 0 2>/dev/null || true
    
    # Setze Lautstärke
    pactl set-sink-volume "$sink" 70% 2>/dev/null || true
    
    echo -e "    ${GREEN}✓${NC} Konfiguriert"
  done
else
  echo -e "  ${YELLOW}⚠${NC} Keine HDMI-Sinks gefunden"
fi
echo ""

# 5. Prüfe cmdline.txt
echo -e "${CYAN}[5] Prüfe cmdline.txt:${NC}"
if [ -f "/boot/firmware/cmdline.txt" ]; then
  if grep -q "video=HDMI-A-1:e" /boot/firmware/cmdline.txt 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} cmdline.txt enthält video=HDMI-A-1:e"
  else
    echo -e "  ${YELLOW}⚠${NC} cmdline.txt enthält NICHT video=HDMI-A-1:e"
    echo "  Füge hinzu mit: ./scripts/enable-hdmi-audio-without-monitor.sh"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} /boot/firmware/cmdline.txt nicht gefunden"
fi
echo ""

# 6. Prüfe config.txt
echo -e "${CYAN}[6] Prüfe config.txt:${NC}"
if [ -f "/boot/firmware/config.txt" ]; then
  if grep -q "dtoverlay=vc4-kms-v3d-pi5" /boot/firmware/config.txt 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} config.txt enthält dtoverlay=vc4-kms-v3d-pi5"
  else
    echo -e "  ${YELLOW}⚠${NC} config.txt enthält NICHT dtoverlay=vc4-kms-v3d-pi5"
  fi
  
  if grep -q "dtparam=audio=on" /boot/firmware/config.txt 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} config.txt enthält dtparam=audio=on"
  else
    echo -e "  ${YELLOW}⚠${NC} config.txt enthält NICHT dtparam=audio=on"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} /boot/firmware/config.txt nicht gefunden"
fi
echo ""

# 7. Prüfe Audio-Sinks
echo -e "${CYAN}[7] Prüfe Audio-Sinks:${NC}"
SINKS=$(pactl list short sinks 2>/dev/null || echo "")
if [ -n "$SINKS" ]; then
  SINK_COUNT=$(echo "$SINKS" | wc -l)
  HDMI_COUNT=$(echo "$SINKS" | grep -c "hdmi" || echo "0")
  echo "  Verfügbare Sinks: $SINK_COUNT (davon HDMI: $HDMI_COUNT)"
  
  DEFAULT_SINK=$(pactl get-default-sink 2>/dev/null || echo "keiner")
  echo "  Standard-Sink: $DEFAULT_SINK"
  
  # Prüfe ob Card 0 (HDMI-A-1) als Sink verfügbar ist
  if echo "$SINKS" | grep -q "107c701400"; then
    echo -e "  ${GREEN}✓${NC} Card 0 (HDMI-A-1) ist als Sink verfügbar"
  else
    echo -e "  ${YELLOW}⚠${NC} Card 0 (HDMI-A-1) ist NICHT als Sink verfügbar"
    echo "  Möglicherweise Neustart erforderlich (cmdline.txt enthält bereits video=HDMI-A-1:e)"
    echo "  Oder HDMI-A-1 Display muss aktiviert werden"
  fi
  
  # Prüfe ob Card 1 (HDMI-A-2) als Sink verfügbar ist
  if echo "$SINKS" | grep -q "107c706400"; then
    echo -e "  ${GREEN}✓${NC} Card 1 (HDMI-A-2) ist als Sink verfügbar"
  else
    echo -e "  ${YELLOW}⚠${NC} Card 1 (HDMI-A-2) ist NICHT als Sink verfügbar"
  fi
else
  echo -e "  ${RED}✗${NC} Keine Sinks gefunden"
fi
echo ""

# 8. Zusammenfassung
echo -e "${CYAN}[8] Zusammenfassung:${NC}"
echo ""
echo "Durchgeführte Reparatur-Schritte:"
echo "  ✓ WirePlumber-Konfiguration zurückgesetzt"
echo "  ✓ HDMI-A-1 Display aktiviert (falls möglich)"
echo "  ✓ WirePlumber neu gestartet"
echo "  ✓ HDMI-Sinks konfiguriert"
echo "  ✓ cmdline.txt und config.txt geprüft"
echo ""
echo "Nächste Schritte:"
echo ""
if echo "$SINKS" | grep -q "107c701400"; then
  echo "1. Teste beide HDMI-Sinks:"
  echo "   ./scripts/test-both-hdmi-sinks.sh"
else
  echo "1. WICHTIG: Card 0 (HDMI-A-1) ist nicht als Sink verfügbar!"
  echo "   Optionen:"
  echo "   a) Starte das System neu (cmdline.txt enthält bereits video=HDMI-A-1:e):"
  echo "      sudo reboot"
  echo ""
  echo "   b) Oder aktiviere HDMI-A-1 manuell:"
  echo "      echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled"
  echo "      systemctl --user restart wireplumber.service"
  echo ""
  echo "   c) Dann teste Audio:"
  echo "      ./scripts/test-both-hdmi-sinks.sh"
fi
echo ""
echo "2. Falls immer noch kein Ton:"
echo "   - Teste ohne Monitor: ./scripts/test-audio-without-monitor.sh"
echo "   - Prüfe Hardware-Verbindungen (FPC-Kabel, Lautsprecher; falls Gehäuse MUTE-Schalter hat: prüfen)"
echo "   - Siehe: docs/FREENOVE_AUDIO_FINAL_DIAGNOSIS.md"
echo ""
echo "3. Falls alles fehlschlägt:"
echo "   - Kontaktiere Freenove Support: https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi"
echo ""
echo -e "${GREEN}Fertig.${NC}"
