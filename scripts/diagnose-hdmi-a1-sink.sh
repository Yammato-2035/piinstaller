#!/bin/bash
# PI-Installer: Diagnose – Warum ist HDMI-A-1 nicht als Sink aktiv?
#
# Diagnostiziert, warum HDMI-A-1 (107c701400) nicht als PipeWire-Sink verfügbar ist,
# obwohl es in cmdline.txt konfiguriert ist.
#
# Ausführung: ./scripts/diagnose-hdmi-a1-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Diagnose: Warum ist HDMI-A-1 nicht als Sink aktiv? ===${NC}"
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

# 1. Prüfe cmdline.txt
echo -e "${CYAN}[1] cmdline.txt prüfen:${NC}"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"

if [ -f "$CMDLINE_FILE" ]; then
  CMDLINE_CONTENT=$(cat "$CMDLINE_FILE")
  if echo "$CMDLINE_CONTENT" | grep -q "video=HDMI-A-1"; then
    echo -e "${GREEN}✓${NC} video=HDMI-A-1 gefunden in cmdline.txt"
    echo "$CMDLINE_CONTENT" | grep -o "video=HDMI-A-1[^ ]*" | while IFS= read -r line; do
      echo "  $line"
    done
  else
    echo -e "${RED}✗${NC} video=HDMI-A-1 NICHT gefunden in cmdline.txt"
    echo "  Lösung: sudo ./scripts/force-hdmi-a1-sink.sh"
  fi
else
  echo -e "${RED}✗${NC} cmdline.txt nicht gefunden: $CMDLINE_FILE"
fi
echo ""

# 2. Prüfe Kernel-Erkennung (DRM)
echo -e "${CYAN}[2] Kernel-Erkennung (DRM) prüfen:${NC}"
if [ -d "/sys/class/drm" ]; then
  HDMI_PORTS=$(ls /sys/class/drm/ 2>/dev/null | grep -E "HDMI-A-" || echo "")
  if [ -n "$HDMI_PORTS" ]; then
    echo "$HDMI_PORTS" | while IFS= read -r port; do
      STATUS=$(cat "/sys/class/drm/$port/status" 2>/dev/null || echo "unknown")
      ENABLED=$(cat "/sys/class/drm/$port/enabled" 2>/dev/null || echo "unknown")
      if echo "$port" | grep -q "HDMI-A-1"; then
        echo -e "  ${GREEN}✓${NC} $port: Status=$STATUS, Enabled=$ENABLED"
      else
        echo "  $port: Status=$STATUS, Enabled=$ENABLED"
      fi
    done
  else
    echo -e "  ${RED}✗${NC} Keine HDMI-Ports gefunden"
  fi
else
  echo -e "  ${RED}✗${NC} /sys/class/drm nicht gefunden"
fi
echo ""

# 3. Prüfe ALSA-Karten
echo -e "${CYAN}[3] ALSA-Karten prüfen:${NC}"
ALSA_CARDS=$(aplay -l 2>/dev/null || echo "")
if [ -n "$ALSA_CARDS" ]; then
  echo "$ALSA_CARDS" | grep "^card" | while IFS= read -r line; do
    if echo "$line" | grep -q "card 0"; then
      echo -e "  ${GREEN}✓${NC} $line (HDMI-A-1 / 107c701400)"
    elif echo "$line" | grep -q "card 1"; then
      echo -e "  ${BLUE}→${NC} $line (HDMI-A-2 / 107c706400)"
    else
      echo "  $line"
    fi
  done
  
  # Prüfe ob Card 0 existiert
  if echo "$ALSA_CARDS" | grep -q "^card 0"; then
    echo -e "${GREEN}✓${NC} Card 0 (HDMI-A-1) ist als ALSA-Karte verfügbar"
  else
    echo -e "${RED}✗${NC} Card 0 (HDMI-A-1) ist NICHT als ALSA-Karte verfügbar"
    echo ""
    echo "  Mögliche Ursachen:"
    echo "    1. Kernel erkennt HDMI-A-1 nicht (trotz cmdline.txt)"
    echo "    2. ALSA-Treiber initialisiert Card 0 nicht"
    echo "    3. HDMI-A-1 ist im Kernel deaktiviert"
    echo ""
    echo "  Prüfe Kernel-Logs:"
    echo "    dmesg | grep -i 'hdmi\|107c701400\|vc4' | tail -20"
  fi
else
  echo -e "${RED}✗${NC} Keine ALSA-Karten gefunden"
fi
echo ""

# 4. Prüfe Kernel-Logs
echo -e "${CYAN}[4] Kernel-Logs (HDMI/VC4):${NC}"
KERNEL_LOGS=$(dmesg | grep -i "hdmi\|107c701400\|vc4.*hdmi" | tail -10 || echo "")
if [ -n "$KERNEL_LOGS" ]; then
  echo "$KERNEL_LOGS" | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo "  (Keine relevanten Kernel-Log-Einträge gefunden)"
fi
echo ""

# 5. Prüfe ALSA-Device-Details für Card 0
echo -e "${CYAN}[5] ALSA-Device-Details für Card 0 (HDMI-A-1):${NC}"
if aplay -l 2>/dev/null | grep -q "^card 0"; then
  echo "  Verfügbare Formate:"
  aplay -D hw:0,0 --dump-hw-params /dev/zero 2>&1 | grep -E "FORMAT|Available formats" | head -5 | while IFS= read -r line; do
    echo "    $line"
  done || echo "    (Fehler beim Abrufen der Formate)"
  
  echo ""
  echo "  Device-Status:"
  if [ -d "/sys/class/drm/card2-HDMI-A-1" ]; then
    STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/status 2>/dev/null || echo "unknown")
    echo "    Status: $STATUS"
  else
    echo "    ⚠ /sys/class/drm/card2-HDMI-A-1 nicht gefunden"
  fi
else
  echo -e "  ${RED}✗${NC} Card 0 nicht verfügbar"
fi
echo ""

# 6. Prüfe PipeWire/PulseAudio Sinks
echo -e "${CYAN}[6] PipeWire/PulseAudio Sinks:${NC}"
ALL_SINKS=$(pactl list sinks short 2>/dev/null || echo "")
if [ -n "$ALL_SINKS" ]; then
  echo "$ALL_SINKS" | while IFS= read -r line; do
    if echo "$line" | grep -q "107c701400"; then
      echo -e "  ${GREEN}✓${NC} $line (HDMI-A-1)"
    elif echo "$line" | grep -q "107c706400"; then
      echo -e "  ${BLUE}→${NC} $line (HDMI-A-2)"
    else
      echo "  $line"
    fi
  done
  
  # Prüfe ob HDMI-A-1 als Sink existiert
  if echo "$ALL_SINKS" | grep -q "107c701400"; then
    echo -e "${GREEN}✓${NC} HDMI-A-1 ist als PipeWire-Sink verfügbar"
  else
    echo -e "${RED}✗${NC} HDMI-A-1 ist NICHT als PipeWire-Sink verfügbar"
  fi
else
  echo -e "${RED}✗${NC} Keine Sinks gefunden"
fi
echo ""

# 7. Prüfe WirePlumber-Status
echo -e "${CYAN}[7] WirePlumber-Status:${NC}"
if systemctl --user is-active wireplumber >/dev/null 2>&1; then
  echo -e "${GREEN}✓${NC} WirePlumber ist aktiv"
  WIREPLUMBER_PID=$(systemctl --user show wireplumber --property MainPID --value 2>/dev/null || echo "")
  if [ -n "$WIREPLUMBER_PID" ]; then
    echo "  PID: $WIREPLUMBER_PID"
  fi
else
  echo -e "${YELLOW}⚠${NC} WirePlumber ist nicht aktiv"
fi
echo ""

# 8. Prüfe WirePlumber-Logs
echo -e "${CYAN}[8] WirePlumber-Logs (letzte 20 Zeilen):${NC}"
if journalctl --user -u wireplumber -n 20 --no-pager 2>/dev/null | grep -i "hdmi\|107c701400\|card.*0" | head -10 | while IFS= read -r line; do
  echo "  $line"
done; then
  echo "  (Keine relevanten Log-Einträge gefunden)"
fi
echo ""

# 9. Prüfe ob Neustart durchgeführt wurde
echo -e "${CYAN}[9] System-Uptime:${NC}"
UPTIME=$(uptime -p 2>/dev/null || echo "unbekannt")
echo "  $UPTIME"

# Prüfe wann cmdline.txt zuletzt geändert wurde
if [ -f "$CMDLINE_FILE" ]; then
  CMDLINE_MTIME=$(stat -c %Y "$CMDLINE_FILE" 2>/dev/null || echo "0")
  CURRENT_TIME=$(date +%s)
  DIFF=$((CURRENT_TIME - CMDLINE_MTIME))
  
  if [ $DIFF -lt 3600 ]; then
    echo -e "  ${YELLOW}⚠${NC} cmdline.txt wurde vor weniger als 1 Stunde geändert"
    echo "  Möglicherweise wurde noch kein Neustart durchgeführt"
  elif [ $DIFF -lt 86400 ]; then
    echo -e "  ${YELLOW}⚠${NC} cmdline.txt wurde vor weniger als 24 Stunden geändert"
    echo "  Neustart könnte erforderlich sein"
  else
    echo -e "  ${GREEN}✓${NC} cmdline.txt wurde vor mehr als 24 Stunden geändert"
  fi
fi
echo ""

# 10. Zusammenfassung und Lösungsvorschläge
echo -e "${CYAN}[10] Zusammenfassung:${NC}"
echo ""

PROBLEM_FOUND=false

# Prüfe alle Bedingungen
if [ -f "$CMDLINE_FILE" ] && ! echo "$CMDLINE_CONTENT" | grep -q "video=HDMI-A-1"; then
  echo -e "${RED}✗${NC} Problem: video=HDMI-A-1 fehlt in cmdline.txt"
  echo "  Lösung: sudo ./scripts/force-hdmi-a1-sink.sh"
  PROBLEM_FOUND=true
fi

if ! aplay -l 2>/dev/null | grep -q "^card 0"; then
  echo -e "${RED}✗${NC} Problem: Card 0 (HDMI-A-1) ist nicht als ALSA-Karte verfügbar"
  echo "  Lösung: Neustart durchführen (sudo reboot)"
  PROBLEM_FOUND=true
fi

if [ -n "$ALL_SINKS" ] && ! echo "$ALL_SINKS" | grep -q "107c701400"; then
  echo -e "${RED}✗${NC} Problem: HDMI-A-1 ist nicht als PipeWire-Sink verfügbar"
  echo ""
  echo "  Mögliche Ursachen:"
  echo "    1. Neustart wurde noch nicht durchgeführt"
  echo "    2. WirePlumber erstellt den Sink nicht automatisch"
  echo "    3. HDMI-A-1 läuft im IEC958-Modus (S/PDIF) und wird nicht als PCM-Sink erkannt"
  echo ""
  echo "  Lösungen:"
  echo "    1. Neustart durchführen: sudo reboot"
  echo "    2. WirePlumber neu starten: systemctl --user restart wireplumber"
  echo "    3. Prüfe WirePlumber-Konfiguration"
  PROBLEM_FOUND=true
fi

# Prüfe ob Card 0 wirklich existiert (auch wenn aplay -l es nicht zeigt)
if grep -q "^ 0 \[vc4hdmi0" /proc/asound/cards 2>/dev/null; then
  echo -e "${GREEN}✓${NC} Card 0 existiert in /proc/asound/cards"
  echo "  Problem: WirePlumber erstellt keinen Sink dafür"
  echo ""
  echo "  Mögliche Ursachen:"
  echo "    1. Card 0 läuft im IEC958-Modus (S/PDIF) - WirePlumber erkennt nur PCM"
  echo "    2. HDMI-A-1 ist 'disabled' - WirePlumber erkennt nur 'enabled' Ports"
  echo "    3. WirePlumber benötigt explizite Konfiguration für Card 0"
  echo ""
  echo "  Lösungen:"
  echo "    1. Prüfe Card 0 Format: aplay -D hw:0,0 --dump-hw-params /dev/zero"
  echo "    2. Aktiviere HDMI-A-1 Display: ./scripts/enable-hdmi-a1-display.sh"
  echo "    3. WirePlumber-Konfiguration anpassen (siehe Dokumentation)"
  PROBLEM_FOUND=true
fi

if [ "$PROBLEM_FOUND" = false ]; then
  echo -e "${GREEN}✓${NC} Alle Prüfungen bestanden"
  echo "  HDMI-A-1 sollte verfügbar sein"
else
  echo ""
  echo -e "${YELLOW}Empfohlene nächste Schritte:${NC}"
  echo "  1. Prüfe Card 0 Format: aplay -D hw:0,0 --dump-hw-params /dev/zero"
  echo "  2. Aktiviere HDMI-A-1 Display: ./scripts/enable-hdmi-a1-display.sh"
  echo "  3. Falls cmdline.txt geändert wurde: sudo reboot"
  echo "  4. Nach Neustart erneut prüfen: ./scripts/diagnose-hdmi-a1-sink.sh"
fi

echo ""
# 11. Prüfe WirePlumber-ALSA-Monitor
echo -e "${CYAN}[11] WirePlumber-ALSA-Monitor prüfen:${NC}"
if [ -f "/usr/share/wireplumber/scripts/monitors/alsa.lua" ]; then
  echo -e "${GREEN}✓${NC} ALSA-Monitor-Skript gefunden"
  echo "  /usr/share/wireplumber/scripts/monitors/alsa.lua"
  echo ""
  echo "  WirePlumber sollte automatisch alle ALSA-Cards erkennen."
  echo "  Falls Card 0 nicht erkannt wird, könnte es sein, dass:"
  echo "    1. Card 0 im IEC958-Modus läuft (S/PDIF)"
  echo "    2. WirePlumber erkennt nur 'enabled' HDMI-Ports"
  echo "    3. Eine explizite Konfiguration erforderlich ist"
else
  echo -e "${YELLOW}⚠${NC} ALSA-Monitor-Skript nicht gefunden"
fi
echo ""

echo -e "${GREEN}Fertig.${NC}"
