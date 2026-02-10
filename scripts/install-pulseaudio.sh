#!/bin/bash
# PI-Installer – PulseAudio installieren
# PulseAudio wird für Audio-Management benötigt (Gehäuse-Lautsprecher, HDMI-Auswahl)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

echo -e "${CYAN}=== PulseAudio Installation ===${NC}"
echo ""

# Prüfe ob bereits installiert
if command -v pulseaudio >/dev/null 2>&1; then
  echo -e "${GREEN}✓${NC} PulseAudio ist bereits installiert: $(which pulseaudio)"
  echo ""
  echo -e "${CYAN}Status prüfen:${NC}"
  systemctl --user status pulseaudio 2>/dev/null | head -3 || echo "  Service nicht aktiv"
  exit 0
fi

echo -e "${CYAN}[1] PulseAudio-Tools installieren${NC}"
apt-get update -qq

# Prüfe ob PipeWire-Pulse läuft (moderne Alternative zu PulseAudio)
if systemctl --user is-active pipewire-pulse >/dev/null 2>&1; then
  echo -e "${GREEN}✓${NC} PipeWire-Pulse läuft bereits"
  # Installiere nur die Tools (pactl, etc.)
  apt-get install -y pulseaudio-utils pavucontrol
else
  # Vollständige PulseAudio-Installation
  apt-get install -y pulseaudio pulseaudio-utils pavucontrol
fi

echo ""
echo -e "${CYAN}[2] PulseAudio für Benutzer aktivieren${NC}"
# Aktueller Benutzer (falls mit sudo ausgeführt)
USER="${SUDO_USER:-$USER}"
if [ "$USER" = "root" ]; then
  USER="$(logname 2>/dev/null || echo "$USER")"
fi

# PulseAudio User-Service aktivieren
if [ -n "$USER" ] && [ "$USER" != "root" ]; then
  systemctl --global enable pulseaudio.service 2>/dev/null || true
  echo -e "${GREEN}✓${NC} PulseAudio für Benutzer $USER aktiviert"
fi

echo ""
echo -e "${CYAN}[3] PulseAudio starten${NC}"
# Als Benutzer starten
if [ -n "$USER" ] && [ "$USER" != "root" ]; then
  sudo -u "$USER" pulseaudio --start 2>/dev/null || echo -e "${YELLOW}⚠${NC} PulseAudio konnte nicht gestartet werden (wird beim nächsten Login automatisch gestartet)"
fi

echo ""
echo -e "${GREEN}=== Installation abgeschlossen ===${NC}"
echo ""
echo -e "${CYAN}Nächste Schritte:${NC}"
echo "  1. Abmelden und wieder anmelden (damit PulseAudio startet)"
echo "  2. Oder manuell starten: pulseaudio --start"
echo "  3. Audio-Gerät wählen: pavucontrol oder Einstellungen → Sound"
echo ""
echo -e "${YELLOW}Hinweis:${NC} Nach dem Neustart sollte PulseAudio automatisch laufen."
echo "Verfügbare Geräte prüfen: pactl list short sinks"
