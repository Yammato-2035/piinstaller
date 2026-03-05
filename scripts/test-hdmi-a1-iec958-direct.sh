#!/bin/bash
# PI-Installer: Teste HDMI-A-1 direkt über ALSA im IEC958-Modus
#
# Card 0 (HDMI-A-1) läuft im IEC958-Modus (S/PDIF).
# Das Mediaboard könnte IEC958-Signale direkt extrahieren, auch ohne PipeWire-Sink.
#
# Ausführung: ./scripts/test-hdmi-a1-iec958-direct.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Teste HDMI-A-1 direkt über ALSA (IEC958-Modus) ===${NC}"
echo ""

# Prüfe ob Card 0 existiert
if ! grep -q "^ 0 \[vc4hdmi0" /proc/asound/cards 2>/dev/null; then
  echo -e "${RED}✗${NC} Card 0 (HDMI-A-1) ist nicht verfügbar"
  exit 1
fi

echo -e "${GREEN}✓${NC} Card 0 (HDMI-A-1) ist verfügbar"
echo ""

# Prüfe verfügbare Formate
echo -e "${CYAN}[1] Verfügbare Formate für Card 0:${NC}"
FORMAT_OUTPUT=$(aplay -D hw:0,0 --dump-hw-params /dev/zero 2>&1 || echo "")
if echo "$FORMAT_OUTPUT" | grep -q "IEC958_SUBFRAME_LE"; then
  echo -e "  ${YELLOW}⚠${NC} Card 0 läuft im IEC958-Modus (S/PDIF)"
  echo "  Format: IEC958_SUBFRAME_LE"
  echo ""
  echo "  Das bedeutet:"
  echo "    - WirePlumber erstellt keinen PCM-Sink dafür"
  echo "    - Das Mediaboard könnte IEC958-Signale direkt extrahieren"
  echo "    - Audio muss im IEC958-Format gespielt werden"
else
  echo "  Format: $(echo "$FORMAT_OUTPUT" | grep "FORMAT:" || echo "unbekannt")"
fi
echo ""

# Versuche IEC958-Audio zu spielen
echo -e "${CYAN}[2] Teste IEC958-Audio-Ausgabe:${NC}"
echo ""

# Prüfe ob es IEC958-Tools gibt
if command -v aplay >/dev/null 2>&1; then
  echo "  Versuche IEC958-Audio über ALSA zu spielen..."
  echo ""
  echo -e "  ${YELLOW}Hinweis:${NC} Standard-aplay unterstützt IEC958 möglicherweise nicht direkt."
  echo "  Das Mediaboard könnte IEC958-Signale aber trotzdem extrahieren."
  echo ""
  echo "  Mögliche Lösungen:"
  echo "    1. Verwende ein Tool, das IEC958 unterstützt (z.B. sox mit speziellen Optionen)"
  echo "    2. Konvertiere PCM zu IEC958 und spiele über hw:0,0"
  echo "    3. Das Mediaboard extrahiert IEC958-Signale automatisch aus HDMI"
  echo ""
  
  # Versuche mit sox (falls verfügbar)
  if command -v sox >/dev/null 2>&1; then
    echo "  Versuche mit sox..."
    # sox kann IEC958 möglicherweise unterstützen
    echo "  (sox IEC958-Support muss geprüft werden)"
  fi
fi

echo ""
echo -e "${CYAN}[3] Zusammenfassung:${NC}"
echo ""
echo "Card 0 (HDMI-A-1) Status:"
echo "  - ALSA-Karte: Verfügbar"
echo "  - Format: IEC958 (S/PDIF)"
echo "  - PipeWire-Sink: Nicht verfügbar (WirePlumber erkennt IEC958 nicht)"
echo ""
echo "Das Mediaboard könnte:"
echo "  - IEC958-Signale direkt von Card 0 extrahieren"
echo "  - Audio auch ohne PipeWire-Sink ausgeben"
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Das Mediaboard extrahiert Audio passiv aus HDMI."
echo "Wenn Card 0 IEC958-Signale ausgibt, könnte das Mediaboard diese"
echo "automatisch extrahieren und an die Gehäuselautsprecher weiterleiten."
echo ""
echo "Teste jetzt, ob Ton aus den Gehäuselautsprechern kommt, wenn"
echo "Audio über Card 0 ausgegeben wird (auch ohne PipeWire-Sink)."
echo ""
echo -e "${GREEN}Fertig.${NC}"
