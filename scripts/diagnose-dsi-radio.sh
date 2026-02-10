#!/bin/bash
# PI-Installer – DSI Radio Diagnose-Script
# Prüft Audio-Player, PulseAudio, Backend und erstellt Debug-Logs

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== DSI Radio Diagnose ===${NC}"
echo ""

# 1. Audio-Player prüfen
echo -e "${CYAN}[1] Audio-Player${NC}"
PLAYERS=()
for cmd in cvlc mpv mpg123; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PLAYERS+=("$cmd")
        echo -e "  ${GREEN}✓${NC} $cmd gefunden: $(which $cmd)"
    else
        echo -e "  ${RED}✗${NC} $cmd nicht gefunden"
    fi
done
if [ ${#PLAYERS[@]} -eq 0 ]; then
    echo -e "  ${RED}FEHLER: Kein Audio-Player gefunden!${NC}"
    echo -e "  ${YELLOW}Installieren: sudo apt install vlc  oder  sudo apt install mpv${NC}"
else
    echo -e "  ${GREEN}Verfügbarer Player: ${PLAYERS[0]}${NC}"
fi
echo ""

# 2. PulseAudio prüfen
echo -e "${CYAN}[2] PulseAudio${NC}"
if command -v pactl >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} pactl gefunden"
    echo ""
    echo -e "  Verfügbare Audio-Sinks:"
    pactl list short sinks 2>/dev/null | while read -r line; do
        if [ -n "$line" ]; then
            sink_id=$(echo "$line" | awk '{print $1}')
            sink_name=$(echo "$line" | awk '{print $2}')
            sink_desc=$(echo "$line" | awk '{for(i=3;i<=NF;i++) printf "%s ", $i; print ""}')
            hdmi_marker=""
            if echo "$sink_name" | grep -qi "hdmi"; then
                hdmi_marker="${YELLOW}[HDMI]${NC}"
            else
                hdmi_marker="${GREEN}[OK]${NC}"
            fi
            echo -e "    $hdmi_marker $sink_name - $sink_desc"
        fi
    done
    echo ""
    DEFAULT_SINK=$(pactl get-default-sink 2>/dev/null || echo "")
    if [ -n "$DEFAULT_SINK" ]; then
        echo -e "  Standard-Sink: ${DEFAULT_SINK}"
        if echo "$DEFAULT_SINK" | grep -qi "hdmi"; then
            echo -e "  ${YELLOW}⚠ Warnung: Standard-Sink ist HDMI${NC}"
        fi
    fi
else
    echo -e "  ${RED}✗${NC} PulseAudio nicht verfügbar (ALSA wird verwendet)"
fi
echo ""

# 3. Backend prüfen
echo -e "${CYAN}[3] Backend (http://127.0.0.1:8000)${NC}"
BACKEND_URL="http://127.0.0.1:8000"
TEST_URL="${BACKEND_URL}/api/radio/stream-metadata?url=https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3"

if curl -s --max-time 3 "$TEST_URL" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Backend erreichbar"
    echo ""
    echo -e "  Test-Metadaten-Abruf:"
    RESPONSE=$(curl -s --max-time 5 "$TEST_URL" 2>/dev/null)
    if [ -n "$RESPONSE" ]; then
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -15 || echo "$RESPONSE" | head -5
    else
        echo -e "  ${RED}✗${NC} Keine Antwort vom Backend"
    fi
else
    echo -e "  ${RED}✗${NC} Backend nicht erreichbar"
    echo -e "  ${YELLOW}Prüfen: Läuft das Backend? (./start-backend.sh)${NC}"
fi
echo ""

# 4. Konfigurationsverzeichnis prüfen
echo -e "${CYAN}[4] Konfigurationsverzeichnis${NC}"
CONFIG_DIR="$HOME/.config/pi-installer-dsi-radio"
if [ -d "$CONFIG_DIR" ]; then
    echo -e "  ${GREEN}✓${NC} Verzeichnis existiert: $CONFIG_DIR"
    echo ""
    echo -e "  Vorhandene Dateien:"
    ls -lh "$CONFIG_DIR" 2>/dev/null | tail -n +2 | while read -r line; do
        echo "    $line"
    done || echo "    (keine Dateien)"
else
    echo -e "  ${YELLOW}⚠${NC} Verzeichnis existiert nicht (wird beim ersten Start erstellt)"
    mkdir -p "$CONFIG_DIR" 2>/dev/null && echo -e "  ${GREEN}✓${NC} Verzeichnis erstellt"
fi
echo ""

# 5. Zusammenfassung
echo -e "${CYAN}=== Zusammenfassung ===${NC}"
ISSUES=0

if [ ${#PLAYERS[@]} -eq 0 ]; then
    echo -e "${RED}✗${NC} Kein Audio-Player installiert"
    ISSUES=$((ISSUES + 1))
fi

if ! curl -s --max-time 3 "$TEST_URL" >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Backend nicht erreichbar"
    ISSUES=$((ISSUES + 1))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Alle Grundvoraussetzungen erfüllt"
    echo ""
    echo -e "${CYAN}Nächste Schritte:${NC}"
    echo "  1. DSI Radio starten: ./scripts/start-dsi-radio.sh"
    echo "  2. Debug-Logs prüfen: cat ~/.config/pi-installer-dsi-radio/*.log"
else
    echo ""
    echo -e "${YELLOW}Beheben Sie die oben genannten Probleme und führen Sie das Script erneut aus.${NC}"
fi
echo ""
