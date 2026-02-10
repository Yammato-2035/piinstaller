#!/bin/bash
# PI-Installer – Dual Display Setup für X11
# Konfiguriert DSI-1 auf Portrait (480x800, 90° nach links) und HDMI-1-2 als Hauptbildschirm
#
# Mit sudo ausführen: sudo ./fix-gabriel-dual-display-x11.sh

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
echo -e "${CYAN}  Dual Display Setup für X11${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Prüfe ob wir unter X11 sind
if [ "$XDG_SESSION_TYPE" != "x11" ] && [ -z "$DISPLAY" ]; then
  echo -e "${YELLOW}Warnung: Scheint nicht unter X11 zu laufen.${NC}"
  echo -e "${YELLOW}XDG_SESSION_TYPE: ${XDG_SESSION_TYPE:-nicht gesetzt}${NC}"
  echo -e "${YELLOW}DISPLAY: ${DISPLAY:-nicht gesetzt}${NC}"
  echo ""
fi

# --- 1. xrandr-Befehle für sofortige Anwendung ---
echo -e "${CYAN}[1] Display-Konfiguration anwenden (xrandr)${NC}"

# Verfügbare Outputs ermitteln
HDMI_MAIN=""
DSI_OUTPUT=""
HDMI_SECONDARY=""

# Prüfe verfügbare Outputs
if command -v xrandr >/dev/null 2>&1; then
  # HDMI-1-2 als Hauptbildschirm (normalerweise HDMI1)
  if xrandr | grep -q "HDMI-1-2"; then
    HDMI_MAIN="HDMI-1-2"
  elif xrandr | grep -q "HDMI-1"; then
    HDMI_MAIN="HDMI-1"
  fi
  
  # DSI-1 finden
  if xrandr | grep -q "DSI-1"; then
    DSI_OUTPUT="DSI-1"
  fi
  
  # HDMI-1-1 als sekundärer HDMI
  if xrandr | grep -q "HDMI-1-1"; then
    HDMI_SECONDARY="HDMI-1-1"
  fi
  
  echo -e "    Gefundene Outputs:"
  echo -e "      Hauptbildschirm (HDMI): ${HDMI_MAIN:-nicht gefunden}"
  echo -e "      DSI: ${DSI_OUTPUT:-nicht gefunden}"
  echo -e "      HDMI sekundär: ${HDMI_SECONDARY:-nicht gefunden}"
  echo ""
  
  if [ -z "$DSI_OUTPUT" ]; then
    echo -e "${RED}Fehler: DSI-1 Output nicht gefunden!${NC}"
    echo -e "${YELLOW}Verfügbare Outputs:${NC}"
    xrandr | grep " connected" | sed 's/^/      /' || true
    exit 1
  fi
  
  if [ -z "$HDMI_MAIN" ]; then
    echo -e "${YELLOW}Warnung: HDMI-Hauptbildschirm nicht gefunden.${NC}"
  fi
else
  echo -e "${RED}Fehler: xrandr nicht gefunden!${NC}"
  exit 1
fi

# --- 2. HDMI-Breite ermitteln ---
echo -e "${CYAN}[2] HDMI-Breite ermitteln${NC}"

HDMI_WIDTH=3440  # Standard-Wert
if [ -n "$HDMI_MAIN" ] && command -v xrandr >/dev/null 2>&1; then
  # Aktuelle Auflösung des HDMI-Hauptbildschirms ermitteln
  CURRENT_MODE=$(xrandr | grep "$HDMI_MAIN" | grep -oP '\d+x\d+' | head -1)
  if [ -n "$CURRENT_MODE" ]; then
    HDMI_WIDTH=$(echo "$CURRENT_MODE" | cut -dx -f1)
    echo -e "    ${GREEN}HDMI-Breite: ${HDMI_WIDTH}px${NC}"
  else
    echo -e "    ${YELLOW}Konnte HDMI-Breite nicht ermitteln, verwende Standard: ${HDMI_WIDTH}px${NC}"
  fi
fi

# --- 3. xrandr-Befehle ausführen (als Benutzer, nicht root) ---
echo -e "${CYAN}[3] Display-Konfiguration anwenden${NC}"

# Als Benutzer ausführen (benötigt DISPLAY)
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME_DIR/.Xauthority}"

# xrandr-Befehle zusammenstellen
XRANDR_CMDS=()

# HDMI-1-1 ausschalten (kein Bildschirm angeschlossen)
if [ -n "$HDMI_SECONDARY" ]; then
  XRANDR_CMDS+=("xrandr --output $HDMI_SECONDARY --off")
fi

# Explizite Framebuffer-Größe: verhindert, dass der Pi-KMS-Treiber DSI oben links
# auf HDMI spiegelt (virtueller Screen = 480+HDMI-Breite x 1440+800).
DSI_WIDTH=480
DSI_HEIGHT=800
HDMI_HEIGHT=1440
FB_WIDTH=$((DSI_WIDTH + HDMI_WIDTH))
FB_HEIGHT=$((HDMI_HEIGHT + DSI_HEIGHT))

# Beide Ausgaben in einem atomaren Befehl setzen (wie unter Wayland pro Output-Name).
# Pi5: DSI-1 = Anschluss 0 (äquivalent HDMI-1-1), HDMI-1-2 = Hauptmonitor. Layout:
# DSI links unten (0,1440), HDMI rechts oben (480,0).
DUAL_CMD="xrandr --fb ${FB_WIDTH}x${FB_HEIGHT}"
if [ -n "$HDMI_MAIN" ]; then
  DUAL_CMD="$DUAL_CMD --output $HDMI_MAIN --auto --primary --pos 480x0"
fi
if [ -n "$DSI_OUTPUT" ]; then
  DUAL_CMD="$DUAL_CMD --output $DSI_OUTPUT --mode 800x480 --rotate left --pos 0x1440"
fi
XRANDR_CMDS+=("$DUAL_CMD")

# Befehle ausführen
for cmd in "${XRANDR_CMDS[@]}"; do
  echo -e "    ${CYAN}Ausführe: $cmd${NC}"
  sudo -u "$USER" env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" bash -c "$cmd" || {
    echo -e "    ${YELLOW}Warnung: Befehl fehlgeschlagen (möglicherweise nicht in X11-Session)${NC}"
  }
done

echo ""

# --- 3b. DSI-1 Rotation vor Boot einrichten (config.txt) ---
echo -e "${CYAN}[3b] DSI-1 Rotation vor Boot einrichten (config.txt)${NC}"
CONFIG_FILE="/boot/firmware/config.txt"
[ -f "$CONFIG_FILE" ] || CONFIG_FILE="/boot/config.txt"
if [ -f "$CONFIG_FILE" ]; then
  # Backup erstellen
  BACKUP_CONFIG="${CONFIG_FILE}.backup.pi-installer-$(date +%Y%m%d-%H%M%S)"
  cp "$CONFIG_FILE" "$BACKUP_CONFIG" 2>/dev/null || true
  echo -e "    ${GREEN}Backup: $(basename "$BACKUP_CONFIG")${NC}"
  
  # display_rotate=1 setzen (90° im Uhrzeigersinn = Portrait für DSI)
  # Entferne alte display_rotate-Zeile
  if grep -q '^display_rotate=' "$CONFIG_FILE"; then
    sed -i '/^display_rotate=/d' "$CONFIG_FILE"
  fi
  # Neue Zeile hinzufügen
  echo "display_rotate=1" >> "$CONFIG_FILE"
  echo -e "    ${GREEN}display_rotate=1 gesetzt (90° im Uhrzeigersinn)${NC}"
  echo -e "    ${YELLOW}Hinweis: Nach Neustart ist DSI-1 bereits vor dem Bootvorgang gedreht${NC}"
else
  echo -e "    ${YELLOW}config.txt nicht gefunden - DSI-Rotation muss manuell gesetzt werden${NC}"
fi
echo ""

# --- 4. Persistente Konfiguration (.xprofile) ---
echo -e "${CYAN}[4] Persistente Konfiguration erstellen (.xprofile)${NC}"

XPROFILE="$HOME_DIR/.xprofile"
mkdir -p "$HOME_DIR"

# Backup falls vorhanden
if [ -f "$XPROFILE" ]; then
  cp "$XPROFILE" "${XPROFILE}.backup.$(date +%Y%m%d-%H%M%S)"
fi

# xrandr-Befehle für .xprofile: ein atomarer Befehl für beide Ausgaben (Position pro Output-Name)
cat > "$XPROFILE" << XPROFILE_EOF
#!/bin/bash
# PI-Installer: Dual Display Setup für X11
# Wird automatisch beim X11-Login ausgeführt.
# Zusätzlich: ~/.config/autostart/pi-installer-dual-display-x11-delayed.desktop
# wendet die Konfiguration nach ~15s erneut an.

# Warte, damit Display-Server und HDMI bereit sind (HDMI braucht oft >5s)
sleep 8

# HDMI-1-1 ausschalten (kein Bildschirm angeschlossen)
xrandr --output HDMI-1-1 --off 2>/dev/null || true

# Beide Ausgaben in einem Befehl (DSI links unten 0x1440, HDMI rechts oben 480x0)
XPROFILE_EOF

# Ein Zeile: --fb und beide --output in einem xrandr-Aufruf
XPROFILE_DUAL="xrandr --fb ${FB_WIDTH}x${FB_HEIGHT}"
if [ -n "$HDMI_MAIN" ]; then
  XPROFILE_DUAL="$XPROFILE_DUAL --output $HDMI_MAIN --auto --primary --pos 480x0"
fi
if [ -n "$DSI_OUTPUT" ]; then
  XPROFILE_DUAL="$XPROFILE_DUAL --output $DSI_OUTPUT --mode 800x480 --rotate left --pos 0x1440"
fi
echo "$XPROFILE_DUAL" >> "$XPROFILE"

# Direkt nach Layout: PCManFM-Desktop neu starten (Trigger für Desktop → Primary/HDMI)
# Ohne Neustart nutzt PCManFM den linkesten Monitor (DSI); nach Neustart sieht es Primary = HDMI.
cat >> "$XPROFILE" << 'XPROFILE_EOF'

# Desktop-Zuordnung auslösen: Layout ist gesetzt, PCManFM neu starten (~2 s danach)
( sleep 2
  if command -v pcmanfm >/dev/null 2>&1; then
    killall pcmanfm 2>/dev/null || true
    sleep 1
    for p in LXDE-pi default; do [ -d "${XDG_CONFIG_HOME:-$HOME/.config}/pcmanfm/$p" ] && break; p=default; done
    pcmanfm --desktop --profile "$p" --display "${DISPLAY:-:0}" &
  fi
) &
XPROFILE_EOF

# HDMI-1-1 ausschalten (falls vorhanden)
if [ -n "$HDMI_SECONDARY" ]; then
  echo "xrandr --output $HDMI_SECONDARY --off" >> "$XPROFILE"
fi

chmod +x "$XPROFILE"
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$XPROFILE"
echo -e "    ${GREEN}✓ .xprofile erstellt${NC}"

echo ""

# --- 4b. monitors.xml sichern/entfernen (überschreibt sonst DSI zu Landscape) ---
echo -e "${CYAN}[4b] monitors.xml prüfen (kann DSI auf Landscape setzen)${NC}"
MONITORS_XML="$HOME_DIR/.config/monitors.xml"
if [ -f "$MONITORS_XML" ]; then
  BACKUP_MONITORS="$HOME_DIR/.config/monitors.xml.bak.pi-installer-$(date +%Y%m%d-%H%M%S)"
  cp "$MONITORS_XML" "$BACKUP_MONITORS"
  chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$BACKUP_MONITORS"
  rm -f "$MONITORS_XML"
  echo -e "    ${GREEN}monitors.xml gesichert und entfernt (Backup: $(basename "$BACKUP_MONITORS"))${NC}"
else
  echo -e "    ${GREEN}Keine monitors.xml vorhanden${NC}"
fi
echo ""

# --- 4c. Verzögertes Autostart-Script (DSI Portrait + HDMI 480x0 nach ~15s) ---
echo -e "${CYAN}[4c] Verzögertes Autostart für Dual Display einrichten${NC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPLY_SCRIPT="$SCRIPT_DIR/apply-dual-display-x11-delayed.sh"
AUTOSTART_DIR="$HOME_DIR/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
DESKTOP_FILE="$AUTOSTART_DIR/pi-installer-dual-display-x11-delayed.desktop"
cat > "$DESKTOP_FILE" << DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=PI-Installer Dual Display (verzögert)
Comment=Wendet HDMI+DSI-Konfiguration ~15s nach Login an (DSI Portrait, HDMI 0x0)
Exec=$APPLY_SCRIPT
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
DESKTOP_EOF
chmod +x "$APPLY_SCRIPT" 2>/dev/null || true
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$DESKTOP_FILE"
echo -e "    ${GREEN}✓ Autostart: $DESKTOP_FILE${NC}"
echo -e "    ${GREEN}✓ Script: $APPLY_SCRIPT (sleep 15, dann xrandr)${NC}"
echo ""

# --- 5. .screenlayout für arandr/autorandr (optional) ---
echo -e "${CYAN}[5] .screenlayout für arandr/autorandr erstellen${NC}"

SCREENLAYOUT_DIR="$HOME_DIR/.screenlayout"
mkdir -p "$SCREENLAYOUT_DIR"

SCREENLAYOUT_FILE="$SCREENLAYOUT_DIR/pi-installer-dual.sh"
cat > "$SCREENLAYOUT_FILE" << SCREENLAYOUT_EOF
#!/bin/bash
# PI-Installer: Dual Display Setup (--fb + beide Ausgaben in einem Befehl)
# Generiert von fix-gabriel-dual-display-x11.sh

SCREENLAYOUT_EOF

# Ein atomarer Befehl für beide Ausgaben (wie unter Wayland pro Output-Name)
SCREENLAYOUT_DUAL="xrandr --fb ${FB_WIDTH}x${FB_HEIGHT}"
if [ -n "$HDMI_MAIN" ]; then
  SCREENLAYOUT_DUAL="$SCREENLAYOUT_DUAL --output $HDMI_MAIN --auto --primary --pos 480x0"
fi
if [ -n "$DSI_OUTPUT" ]; then
  SCREENLAYOUT_DUAL="$SCREENLAYOUT_DUAL --output $DSI_OUTPUT --mode 800x480 --rotate left --pos 0x1440"
fi
echo "$SCREENLAYOUT_DUAL" >> "$SCREENLAYOUT_FILE"

# HDMI-1-1 ausschalten (kein Bildschirm angeschlossen)
if [ -n "$HDMI_SECONDARY" ]; then
  echo "xrandr --output $HDMI_SECONDARY --off" >> "$SCREENLAYOUT_FILE"
fi

chmod +x "$SCREENLAYOUT_FILE"
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$SCREENLAYOUT_FILE"
echo -e "    ${GREEN}✓ .screenlayout/pi-installer-dual.sh erstellt${NC}"

echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Dual Display Setup abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Konfiguration:${NC}"
echo -e "  • DSI-1: Portrait (480x800), links unten (0,1440)"
echo -e "  • HDMI-1-2: Hauptbildschirm (3440x1440), rechts vom DSI mit Versatz 480 (480,0)"
echo -e "  • HDMI-1-1: Ausgeschaltet (kein Bildschirm angeschlossen)"
echo ""
echo -e "${YELLOW}Hinweise:${NC}"
echo -e "  • Die Konfiguration wurde sofort angewendet"
echo -e "  • config.txt: display_rotate=1 gesetzt (DSI-1 ist bereits vor Bootvorgang gedreht)"
echo -e "  • .xprofile: HDMI explizit 0x0, DSI Portrait 0x1440 (beim Login)"
echo -e "  • Autostart: ~30s nach Login wird die Konfiguration erneut angewendet (DSI Portrait, HDMI 480x0)"
echo -e "  • monitors.xml wurde ggf. gesichert und entfernt (verhinderte DSI Portrait)"
echo -e "  • Desktop erscheint auf HDMI-1-2 (Primary Display)"
echo -e "  • Taskleisten-Icons (AnyDesk, RVNC, Cursor) können kurz flackern, bis die Displays stabil sind"
echo ""
echo -e "${CYAN}Wichtig:${NC}"
echo -e "  • Neustart erforderlich: sudo reboot (damit display_rotate=1 wirkt)"
echo -e "  • Nach Neustart: DSI-1 ist bereits vor dem Bootvorgang gedreht"
echo ""
