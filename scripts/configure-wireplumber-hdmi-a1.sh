#!/bin/bash
# PI-Installer: Konfiguriere WirePlumber, um Card 0 (HDMI-A-1) als Sink zu erkennen
#
# Problem: WirePlumber erstellt keinen Sink für Card 0, weil HDMI-A-1 "disabled" ist.
# Lösung: Erstelle WirePlumber-Regel, die Card 0 explizit erkennt.
#
# Ausführung: sudo ./scripts/configure-wireplumber-hdmi-a1.sh
# Hinweis: Konfiguration wird mit sudo geschrieben. WirePlumber und pactl laufen
# im Benutzerkontext – nach dem Skript bitte ohne sudo ausführen:
#   systemctl --user restart wireplumber
#   ./scripts/activate-hdmi-a1-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Konfiguriere WirePlumber für HDMI-A-1 (vc4hdmi0) ===${NC}"
echo ""

# Prüfe ob HDMI-A-1 (vc4hdmi0) existiert – kann Card 0 oder 1 sein, wenn z.B. USB-Audio Card 0 belegt
if ! grep -q "vc4hdmi0" /proc/asound/cards 2>/dev/null; then
  echo -e "${RED}✗${NC} HDMI-A-1 (vc4hdmi0) ist nicht verfügbar"
  echo "  /proc/asound/cards:"
  cat /proc/asound/cards 2>/dev/null | sed 's/^/    /'
  exit 1
fi

echo -e "${GREEN}✓${NC} HDMI-A-1 (vc4hdmi0) ist verfügbar"
echo ""

# Prüfe WirePlumber-Konfigurationsverzeichnis
WIREPLUMBER_CONF_DIR="/etc/xdg/wireplumber/wireplumber.conf.d"
WIREPLUMBER_USER_CONF_DIR="$HOME/.config/wireplumber/wireplumber.conf.d"

echo -e "${CYAN}[1] Erstelle WirePlumber-Konfiguration:${NC}"

# Versuche zuerst System-weit (benötigt sudo)
if [ -w "/etc" ] || sudo -n true 2>/dev/null; then
  echo "  Erstelle System-weite Konfiguration..."
  sudo mkdir -p "$WIREPLUMBER_CONF_DIR"
  
  CONFIG_FILE="$WIREPLUMBER_CONF_DIR/50-alsa-hdmi-a1.conf"
  
  sudo tee "$CONFIG_FILE" > /dev/null << 'EOF'
# PI-Installer: Erzwinge Sink-Erstellung für Card 0 (HDMI-A-1)
# Auch wenn HDMI-A-1 Display "disabled" ist, soll WirePlumber einen Sink erstellen.
# Zusätzlich: HDMI-A-1 als Standard-Sink (höchste Priorität), HDMI-A-2 niedrigere Priorität,
# damit nach Neustart der Ton an Gehäuselautsprechern/Kopfhörerbuchse ankommt.

alsa_monitor.rules = {
  {
    matches = {
      {
        { "device.name", "matches", "alsa_card.platform-107c701400.hdmi" },
      },
    },
    apply_properties = {
      ["device.disabled"] = false,
      ["api.alsa.use-acp"] = true,
    },
  },
  {
    matches = {
      {
        { "node.name", "matches", "alsa_output.platform-107c701400.hdmi.hdmi-stereo" },
      },
    },
    apply_properties = {
      ["priority.driver"] = 2000,
      ["priority.session"] = 2000,
    },
  },
  {
    matches = {
      {
        { "node.name", "matches", "alsa_output.platform-107c706400.hdmi.hdmi-stereo" },
      },
    },
    apply_properties = {
      ["priority.driver"] = 100,
      ["priority.session"] = 100,
    },
  },
}
EOF
  
  echo -e "  ${GREEN}✓${NC} Konfiguration erstellt: $CONFIG_FILE"
  
else
  # Fallback: Benutzer-Konfiguration
  echo "  Erstelle Benutzer-Konfiguration..."
  mkdir -p "$WIREPLUMBER_USER_CONF_DIR"
  
  CONFIG_FILE="$WIREPLUMBER_USER_CONF_DIR/50-alsa-hdmi-a1.conf"
  
  tee "$CONFIG_FILE" > /dev/null << 'EOF'
# PI-Installer: Erzwinge Device-Erkennung für Card 0 (HDMI-A-1)
# Auch wenn HDMI-A-1 Display "disabled" ist, soll WirePlumber Card 0 erkennen.
# Zusätzlich: HDMI-A-1 als Standard-Sink (höchste Priorität), HDMI-A-2 niedrigere Priorität.

monitor.alsa.rules = [
  {
    matches = [
      {
        { "device.name", "matches", "alsa_card.platform-107c701400.hdmi" },
      },
    ],
    apply_properties = {
      ["device.disabled"] = false,
      ["api.alsa.use-acp"] = true,
    },
  },
  {
    matches = [
      {
        { "node.name", "matches", "alsa_output.platform-107c701400.hdmi.hdmi-stereo" },
      },
    ],
    apply_properties = {
      ["priority.driver"] = 2000,
      ["priority.session"] = 2000,
    },
  },
  {
    matches = [
      {
        { "node.name", "matches", "alsa_output.platform-107c706400.hdmi.hdmi-stereo" },
      },
    ],
    apply_properties = {
      ["priority.driver"] = 100,
      ["priority.session"] = 100,
    },
  },
]
EOF
  
  echo -e "  ${GREEN}✓${NC} Konfiguration erstellt: $CONFIG_FILE"
fi

echo ""
echo -e "${CYAN}[2] Starte WirePlumber neu:${NC}"

# Unter sudo hat systemctl --user den falschen Kontext (root); dann nur Hinweis
if [ "$(id -u)" = "0" ]; then
  echo -e "  ${YELLOW}⚠${NC} Skript läuft mit sudo – WirePlumber bitte als Benutzer neu starten:"
  echo "     systemctl --user restart wireplumber"
  echo "     ./scripts/activate-hdmi-a1-sink.sh"
else
  if systemctl --user is-active --quiet wireplumber.service 2>/dev/null; then
    echo "  Starte WirePlumber neu..."
    systemctl --user restart wireplumber.service
    sleep 2
    echo -e "  ${GREEN}✓${NC} WirePlumber neu gestartet"
  else
    echo -e "  ${YELLOW}⚠${NC} WirePlumber läuft nicht als Systemd-Service"
    echo "  Starte WirePlumber manuell neu oder starte das System neu"
  fi
fi

echo ""
echo -e "${CYAN}[3] Prüfe ob HDMI-A-1 erkannt wurde:${NC}"
sleep 1

# Ganzzahl sicher auswerten (pactl läuft im User-Kontext; bei sudo ggf. 0)
CARD_FOUND=$(pactl list cards 2>/dev/null | grep -c "alsa_card.platform-107c701400.hdmi" || echo "0")
CARD_FOUND=$(( ${CARD_FOUND//[^0-9]/} + 0 ))

if [ "$CARD_FOUND" -gt 0 ]; then
  echo -e "  ${GREEN}✓${NC} HDMI-A-1 wurde erkannt!"
  echo ""
  echo -e "${CYAN}[4] Aktiviere HDMI-Stereo-Profil für HDMI-A-1:${NC}"
  
  # Aktiviere das HDMI-Stereo-Profil
  if pactl set-card-profile alsa_card.platform-107c701400.hdmi output:hdmi-stereo 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Profil aktiviert"
    sleep 1
  else
    echo -e "  ${YELLOW}⚠${NC} Konnte Profil nicht aktivieren (möglicherweise bereits aktiv)"
  fi
  
  echo ""
  echo -e "${CYAN}[5] Prüfe ob Sink erstellt wurde:${NC}"
  sleep 1
  
  SINK_COUNT=$(pactl list short sinks 2>/dev/null | grep -c "alsa_output.platform-107c701400.hdmi" || echo "0")
  SINK_COUNT=$(( ${SINK_COUNT//[^0-9]/} + 0 ))
  
  if [ "$SINK_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Sink für HDMI-A-1 gefunden!"
    echo ""
    echo "  Verfügbare Sinks:"
    pactl list short sinks 2>/dev/null | grep "alsa_output.platform-107c701400.hdmi" || echo "  (keine gefunden)"
    echo ""
    echo -e "${CYAN}[6] Setze HDMI-A-1 als Standard-Sink und aktiviere (wenn SUSPENDED):${NC}"
    SINK_A1="alsa_output.platform-107c701400.hdmi.hdmi-stereo"
    if pactl set-default-sink "$SINK_A1" 2>/dev/null; then
      echo -e "  ${GREEN}✓${NC} Standard-Sink: $SINK_A1"
    fi
    pactl set-sink-mute "$SINK_A1" 0 2>/dev/null || true
    pactl set-sink-volume "$SINK_A1" 70% 2>/dev/null || true
    if pactl list short sinks 2>/dev/null | grep -q "${SINK_A1}.*SUSPENDED"; then
      echo "  Spiele kurzen Testton (aktiviert suspendierten Sink)..."
      paplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null &
      sleep 2
      kill "$!" 2>/dev/null || true
      echo -e "  ${GREEN}✓${NC} Sink sollte jetzt RUNNING sein"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} Kein Sink für HDMI-A-1 gefunden"
    echo ""
    echo "  Versuche Profil manuell zu aktivieren..."
    echo "  pactl set-card-profile alsa_card.platform-107c701400.hdmi output:hdmi-stereo"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 wurde nicht erkannt"
  echo ""
  echo "  Mögliche Gründe:"
  echo "    - WirePlumber muss neu gestartet werden"
  echo "    - System-Neustart erforderlich"
  echo "    - HDMI-A-1 muss aktiviert werden"
fi

echo ""
echo -e "${CYAN}[7] Nächste Schritte:${NC}"
echo ""
echo "  Standard-Sink prüfen: pactl get-default-sink"
echo "  Sollte sein: alsa_output.platform-107c701400.hdmi.hdmi-stereo"
echo ""
echo "  Ton testen: paplay /usr/share/sounds/alsa/Front_Left.wav"
echo ""
echo -e "${GREEN}Fertig.${NC}"
