#!/bin/bash
# PI-Installer – Dual Display Setup für X11 mit früher Konfiguration
# Verwendet LightDM display-setup-script und session-setup-script für frühe,
# einmalige Bildschirmkonfiguration ohne mehrfache Umschaltungen.
#
# Mit sudo ausführen: sudo ./fix-gabriel-dual-display-x11-early.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

USER="gabrielglienke"
HOME_DIR="/home/$USER"

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

if [ ! -d "$HOME_DIR" ]; then
  echo -e "${RED}Benutzer $USER nicht gefunden ($HOME_DIR)${NC}"
  exit 1
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Dual Display Setup für X11 (frühe Konfiguration)${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Prüfe ob wir unter X11 sind
if [ "$XDG_SESSION_TYPE" != "x11" ] && [ -z "$DISPLAY" ]; then
  echo -e "${YELLOW}Warnung: Scheint nicht unter X11 zu laufen.${NC}"
  echo -e "${YELLOW}XDG_SESSION_TYPE: ${XDG_SESSION_TYPE:-nicht gesetzt}${NC}"
  echo -e "${YELLOW}DISPLAY: ${DISPLAY:-nicht gesetzt}${NC}"
  echo ""
fi

# Verfügbare Outputs ermitteln (falls xrandr verfügbar)
HDMI_MAIN="HDMI-1-2"
DSI_OUTPUT="DSI-1"
HDMI_SECONDARY="HDMI-1-1"
HDMI_WIDTH=3440  # Standard-Wert

if command -v xrandr >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
  if xrandr | grep -q "HDMI-1-2"; then
    HDMI_MAIN="HDMI-1-2"
  elif xrandr | grep -q "HDMI-1"; then
    HDMI_MAIN="HDMI-1"
  fi
  
  if xrandr | grep -q "DSI-1"; then
    DSI_OUTPUT="DSI-1"
  fi
  
  if xrandr | grep -q "HDMI-1-1"; then
    HDMI_SECONDARY="HDMI-1-1"
  fi
  
  # HDMI-Breite ermitteln
  CURRENT_MODE=$(xrandr | grep "$HDMI_MAIN" | grep -oP '\d+x\d+' | head -1)
  if [ -n "$CURRENT_MODE" ]; then
    HDMI_WIDTH=$(echo "$CURRENT_MODE" | cut -dx -f1)
  fi
fi

DSI_WIDTH=480
DSI_HEIGHT=800
HDMI_HEIGHT=1440
FB_WIDTH=$((DSI_WIDTH + HDMI_WIDTH))
FB_HEIGHT=$((HDMI_HEIGHT + DSI_HEIGHT))

echo -e "${CYAN}Konfiguration:${NC}"
echo -e "  HDMI-Hauptbildschirm: $HDMI_MAIN (${HDMI_WIDTH}x${HDMI_HEIGHT})"
echo -e "  DSI: $DSI_OUTPUT (${DSI_WIDTH}x${DSI_HEIGHT}, Portrait)"
echo -e "  Framebuffer: ${FB_WIDTH}x${FB_HEIGHT}"
echo ""

# --- 1. LightDM display-setup-script (übersprungen - verwende nur session-setup) ---
# display-setup-script wird übersprungen, da es zu früh läuft und Konflikte verursachen kann
# Stattdessen verwenden wir nur session-setup-script, das nach Login läuft
echo -e "${CYAN}[1] LightDM display-setup-script (übersprungen)${NC}"
echo -e "    ${YELLOW}Verwende nur session-setup-script für bessere Kompatibilität${NC}"
echo ""

# --- 2. LightDM session-setup-script (läuft als User nach Login, vor Desktop) ---
echo -e "${CYAN}[2] LightDM session-setup-script erstellen${NC}"

SESSION_SETUP_SCRIPT="/usr/local/bin/pi-installer-session-setup.sh"
cat > "$SESSION_SETUP_SCRIPT" << 'SESSIONSETUP'
#!/bin/bash
# PI-Installer: Display-Konfiguration nach Login, vor Desktop-Start
# Läuft als angemeldeter Benutzer nach Login, aber vor Desktop-Start
# DISPLAY und XAUTHORITY sind bereits gesetzt

# Kurze Verzögerung, damit X-Session vollständig initialisiert ist
sleep 1

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME}/.Xauthority}"

# Verfügbare Outputs dynamisch ermitteln
HDMI_MAIN=""
DSI_OUTPUT=""
HDMI_SECONDARY=""

if command -v xrandr >/dev/null 2>&1; then
  # HDMI-1-2 als Hauptbildschirm
  if xrandr 2>/dev/null | grep -q "HDMI-1-2.*connected"; then
    HDMI_MAIN="HDMI-1-2"
  elif xrandr 2>/dev/null | grep -q "HDMI-1.*connected"; then
    HDMI_MAIN="HDMI-1"
  fi
  
  # DSI-1 finden
  if xrandr 2>/dev/null | grep -q "DSI-1.*connected"; then
    DSI_OUTPUT="DSI-1"
  fi
  
  # HDMI-1-1 als sekundärer HDMI
  if xrandr 2>/dev/null | grep -q "HDMI-1-1.*connected"; then
    HDMI_SECONDARY="HDMI-1-1"
  fi
  
  # HDMI-Breite ermitteln
  HDMI_WIDTH=3440
  if [ -n "$HDMI_MAIN" ]; then
    CURRENT_MODE=$(xrandr 2>/dev/null | grep "$HDMI_MAIN" | grep -oP '\d+x\d+' | head -1)
    if [ -n "$CURRENT_MODE" ]; then
      HDMI_WIDTH=$(echo "$CURRENT_MODE" | cut -dx -f1)
    fi
  fi
  
  DSI_WIDTH=480
  DSI_HEIGHT=800
  HDMI_HEIGHT=1440
  FB_WIDTH=$((DSI_WIDTH + HDMI_WIDTH))
  FB_HEIGHT=$((HDMI_HEIGHT + DSI_HEIGHT))
  
  # Konfiguration anwenden (atomarer Befehl)
  # WICHTIG: DSI zuerst setzen, dann HDMI (verhindert Position-Überschreibung)
  if [ -n "$HDMI_MAIN" ] && [ -n "$DSI_OUTPUT" ]; then
    # Erst Framebuffer setzen, dann beide Outputs in einem Befehl
    # DSI links unten (0x1440), HDMI rechts oben (480x0)
    xrandr --fb ${FB_WIDTH}x${FB_HEIGHT} \
           --output "$DSI_OUTPUT" --mode 800x480 --rotate left --pos 0x1440 \
           --output "$HDMI_MAIN" --auto --primary --pos 480x0 \
           2>/dev/null || true
    
    # HDMI-1-1 ausschalten (falls vorhanden)
    if [ -n "$HDMI_SECONDARY" ]; then
      xrandr --output "$HDMI_SECONDARY" --off 2>/dev/null || true
    fi
    
    # PCManFM-Desktop auf Primary Display neu starten
    if command -v pcmanfm >/dev/null 2>&1; then
      sleep 0.5
      killall pcmanfm 2>/dev/null || true
      sleep 0.5
      for profile in LXDE-pi default; do
        [ -d "${XDG_CONFIG_HOME:-$HOME/.config}/pcmanfm/$profile" ] && break
        profile="default"
      done
      pcmanfm --desktop --profile "$profile" &
    fi
  fi
fi
SESSIONSETUP

chmod +x "$SESSION_SETUP_SCRIPT"
echo -e "    ${GREEN}✓ Script erstellt: $SESSION_SETUP_SCRIPT${NC}"

# LightDM-Konfiguration aktualisieren
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
LIGHTDM_D="/etc/lightdm/lightdm.conf.d"
LIGHTDM_DROPIN="$LIGHTDM_D/99-pi-installer-display-setup.conf"

mkdir -p "$LIGHTDM_D"

# Entferne alte session-setup-script Einträge aus der Haupt-Config
if [ -f "$LIGHTDM_CONF" ]; then
  sed -i '/^session-setup-script=/d' "$LIGHTDM_CONF"
fi

# Erstelle/aktualisiere Drop-in für session-setup-script
cat > "$LIGHTDM_DROPIN" << LIGHTDMDROPIN
# PI-Installer: Display-Konfiguration nach Login
[Seat:*]
session-setup-script=$SESSION_SETUP_SCRIPT
LIGHTDMDROPIN

echo -e "    ${GREEN}✓ LightDM Drop-in aktualisiert${NC}"
echo ""

# --- 3. Systemd User Service (zusätzliche Sicherheitsschicht) ---
echo -e "${CYAN}[3] Systemd User Service erstellen${NC}"

SYSTEMD_USER_DIR="$HOME_DIR/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

SERVICE_FILE="$SYSTEMD_USER_DIR/pi-installer-display-config.service"
cat > "$SERVICE_FILE" << 'SERVICEFILE'
[Unit]
Description=PI-Installer Display Configuration (X11)
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/pi-installer-session-setup.sh
Environment="DISPLAY=:0"
Environment="XAUTHORITY=%h/.Xauthority"

[Install]
WantedBy=graphical-session.target
SERVICEFILE

chown -R "$USER:$(stat -c '%G' "$HOME_DIR")" "$SYSTEMD_USER_DIR"
echo -e "    ${GREEN}✓ Service erstellt: $SERVICE_FILE${NC}"
echo -e "    ${YELLOW}Hinweis: Service wird beim nächsten Login aktiviert${NC}"
echo ""

# --- 4. Alte verzögerte Autostart-Skripte deaktivieren ---
echo -e "${CYAN}[4] Alte verzögerte Autostart-Skripte deaktivieren${NC}"

# Entferne verzögertes Autostart-Script
AUTOSTART_DESKTOP="$HOME_DIR/.config/autostart/pi-installer-dual-display-x11-delayed.desktop"
if [ -f "$AUTOSTART_DESKTOP" ]; then
  mv "$AUTOSTART_DESKTOP" "${AUTOSTART_DESKTOP}.disabled" 2>/dev/null || rm -f "$AUTOSTART_DESKTOP"
  echo -e "    ${GREEN}✓ Deaktiviert: $(basename "$AUTOSTART_DESKTOP")${NC}"
fi

# Deaktiviere altes enable-hdmi.sh Script (überschreibt Position mit --right-of)
ENABLE_HDMI_SCRIPT="/usr/local/bin/pi-installer-enable-hdmi.sh"
ENABLE_HDMI_DESKTOP_SYSTEM="/etc/xdg/autostart/pi-installer-enable-hdmi.desktop"
ENABLE_HDMI_DESKTOP_USER="$HOME_DIR/.config/autostart/pi-installer-enable-hdmi.desktop"

if [ -f "$ENABLE_HDMI_DESKTOP_SYSTEM" ]; then
  mv "$ENABLE_HDMI_DESKTOP_SYSTEM" "${ENABLE_HDMI_DESKTOP_SYSTEM}.disabled" 2>/dev/null || rm -f "$ENABLE_HDMI_DESKTOP_SYSTEM"
  echo -e "    ${GREEN}✓ Deaktiviert: $(basename "$ENABLE_HDMI_DESKTOP_SYSTEM")${NC}"
fi

if [ -f "$ENABLE_HDMI_DESKTOP_USER" ]; then
  mv "$ENABLE_HDMI_DESKTOP_USER" "${ENABLE_HDMI_DESKTOP_USER}.disabled" 2>/dev/null || rm -f "$ENABLE_HDMI_DESKTOP_USER"
  echo -e "    ${GREEN}✓ Deaktiviert: $(basename "$ENABLE_HDMI_DESKTOP_USER")${NC}"
fi

# Falls enable-hdmi.sh existiert, benenne es um (als Backup)
if [ -f "$ENABLE_HDMI_SCRIPT" ]; then
  mv "$ENABLE_HDMI_SCRIPT" "${ENABLE_HDMI_SCRIPT}.disabled" 2>/dev/null || true
  echo -e "    ${GREEN}✓ Deaktiviert: $(basename "$ENABLE_HDMI_SCRIPT")${NC}"
fi

# Aktualisiere .xprofile (entferne lange Sleeps, korrigiere Position)
XPROFILE="$HOME_DIR/.xprofile"
if [ -f "$XPROFILE" ]; then
  # Backup erstellen
  cp "$XPROFILE" "${XPROFILE}.backup.$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
  
  # Entferne lange Sleeps und ersetze durch minimale Verzögerung
  sed -i 's/sleep [0-9][0-9]*/sleep 1/g' "$XPROFILE" 2>/dev/null || true
  
  # Stelle sicher, dass DSI zuerst gesetzt wird (Position korrekt)
  # Ersetze xrandr-Befehle, die HDMI zuerst setzen
  if grep -q "xrandr.*--output.*HDMI.*--output.*DSI" "$XPROFILE" 2>/dev/null; then
    # Erstelle neue .xprofile mit korrekter Reihenfolge
    sed -i '/xrandr.*--fb.*--output.*HDMI.*--output.*DSI/{
      s/--output \([^ ]*HDMI[^ ]*\)[^ ]* --output \([^ ]*DSI[^ ]*\)/--output \2 --output \1/
    }' "$XPROFILE" 2>/dev/null || true
  fi
  
  echo -e "    ${GREEN}✓ .xprofile aktualisiert (Sleeps reduziert, Position korrigiert)${NC}"
fi

echo ""

# --- 5. monitors.xml sichern/entfernen ---
echo -e "${CYAN}[5] monitors.xml prüfen${NC}"
MONITORS_XML="$HOME_DIR/.config/monitors.xml"
if [ -f "$MONITORS_XML" ]; then
  BACKUP_MONITORS="$HOME_DIR/.config/monitors.xml.bak.pi-installer-$(date +%Y%m%d-%H%M%S)"
  cp "$MONITORS_XML" "$BACKUP_MONITORS"
  chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$BACKUP_MONITORS"
  rm -f "$MONITORS_XML"
  echo -e "    ${GREEN}✓ monitors.xml gesichert und entfernt${NC}"
else
  echo -e "    ${GREEN}Keine monitors.xml vorhanden${NC}"
fi
echo ""

# --- 6. config.txt: DSI-Rotation vor Boot ---
echo -e "${CYAN}[6] DSI-Rotation in config.txt einrichten${NC}"
CONFIG_FILE="/boot/firmware/config.txt"
[ -f "$CONFIG_FILE" ] || CONFIG_FILE="/boot/config.txt"
if [ -f "$CONFIG_FILE" ]; then
  BACKUP_CONFIG="${CONFIG_FILE}.backup.pi-installer-$(date +%Y%m%d-%H%M%S)"
  cp "$CONFIG_FILE" "$BACKUP_CONFIG" 2>/dev/null || true
  echo -e "    ${GREEN}Backup: $(basename "$BACKUP_CONFIG")${NC}"
  
  # display_rotate=1 setzen (90° im Uhrzeigersinn = Portrait für DSI)
  if grep -q '^display_rotate=' "$CONFIG_FILE"; then
    sed -i '/^display_rotate=/d' "$CONFIG_FILE"
  fi
  echo "display_rotate=1" >> "$CONFIG_FILE"
  echo -e "    ${GREEN}display_rotate=1 gesetzt${NC}"
else
  echo -e "    ${YELLOW}config.txt nicht gefunden${NC}"
fi
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Dual Display Setup abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Konfiguration:${NC}"
echo -e "  • LightDM session-setup-script: Läuft als User nach Login, vor Desktop"
echo -e "  • Systemd User Service: Zusätzliche Sicherheitsschicht"
echo -e "  • DSI-1: Portrait (480x800), links unten (0,1440) - wird ZUERST gesetzt"
echo -e "  • HDMI-1-2: Hauptbildschirm (${HDMI_WIDTH}x1440), rechts oben (480,0)"
echo ""
echo -e "${YELLOW}Vorteile dieser Lösung:${NC}"
echo -e "  ✓ Konfiguration erfolgt früher im Boot-Prozess"
echo -e "  ✓ Keine mehrfachen Umschaltungen mehr"
echo -e "  ✓ Einmalige, atomare Konfiguration"
echo -e "  ✓ Desktop-Inhalt bleibt sichtbar"
echo ""
echo -e "${CYAN}Nächste Schritte:${NC}"
echo -e "  1. Neustart ausführen: ${YELLOW}sudo reboot${NC}"
echo -e "  2. Nach Neustart sollte die Konfiguration sofort korrekt sein"
echo -e "  3. Falls Probleme auftreten, Logs prüfen:"
echo -e "     ${CYAN}journalctl -u lightdm -b${NC}"
echo ""
