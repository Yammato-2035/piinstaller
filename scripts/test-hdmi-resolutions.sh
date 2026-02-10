#!/bin/bash
# Test verschiedene HDMI-Auflösungen
# Als Benutzer ausführen: ./test-hdmi-resolutions.sh

echo "Teste verschiedene Auflösungen für HDMI-1-2..."
echo ""

# Verfügbare Modi
echo "Verfügbare Modi:"
xrandr | grep "HDMI-1-2" -A 15 | grep -E "^\s+\d+x\d+" | head -10

echo ""
echo "Teste jetzt verschiedene Auflösungen (jeweils 3 Sekunden):"
echo "Drücke Strg+C zum Abbrechen"
echo ""

for mode in "1920x1080" "2560x1440" "3440x1440"; do
  echo "Teste: $mode"
  xrandr --output HDMI-1-2 --mode $mode --rate 60 --primary --pos 480x0
  sleep 3
done

# Zurück zu auto
echo "Zurück zu auto..."
xrandr --output HDMI-1-2 --auto --primary --pos 480x0
