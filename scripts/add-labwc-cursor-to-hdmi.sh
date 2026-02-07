#!/bin/bash
# PI-Installer: Cursor (und andere große Apps) auf HDMI-Hauptbildschirm öffnen
# Verhindert, dass Cursor mit 800x480 auf dem DSI startet und nicht vergrößerbar ist.
#
# Auf dem Pi ausführen (als gabrielglienke oder mit sudo -u gabrielglienke)

set -e

USER="${1:-gabrielglienke}"
HOME_DIR="/home/$USER"
LABWC_RC="$HOME_DIR/.config/labwc/rc.xml"

if [ "$(id -u)" -eq 0 ] && [ -n "$SUDO_USER" ]; then
  USER="$SUDO_USER"
  HOME_DIR="/home/$USER"
  LABWC_RC="$HOME_DIR/.config/labwc/rc.xml"
fi

mkdir -p "$(dirname "$LABWC_RC")"

MARKER="<!-- PI-Installer: Cursor auf HDMI1 -->"

if [ ! -f "$LABWC_RC" ]; then
  cat > "$LABWC_RC" << 'RCEOF'
<?xml version="1.0"?>
<labwc_config>
  <windowRules>
    <windowRule identifier="cursor*">
      <action name="MoveToOutput" output="HDMI-A-2"/>
    </windowRule>
    <windowRule identifier="cursor-url-handler">
      <action name="MoveToOutput" output="HDMI-A-2"/>
    </windowRule>
    <windowRule identifier="code*">
      <action name="MoveToOutput" output="HDMI-A-2"/>
    </windowRule>
  </windowRules>
</labwc_config>
RCEOF
  echo "Labwc rc.xml erstellt: $LABWC_RC"
else
  if grep -q "$MARKER" "$LABWC_RC" 2>/dev/null; then
    echo "Fensterregel bereits vorhanden: $LABWC_RC"
    exit 0
  fi
  # Regel per Temp-Datei einfügen
  TMP=$(mktemp)
  awk '
    /<\/labwc_config>/ {
      print "  " marker
      print "  <windowRules>"
      print "    <windowRule identifier=\"cursor*\">"
      print "      <action name=\"MoveToOutput\" output=\"HDMI-A-2\"/>"
      print "    </windowRule>"
      print "    <windowRule identifier=\"cursor-url-handler\">"
      print "      <action name=\"MoveToOutput\" output=\"HDMI-A-2\"/>"
      print "    </windowRule>"
      print "    <windowRule identifier=\"code*\">"
      print "      <action name=\"MoveToOutput\" output=\"HDMI-A-2\"/>"
      print "    </windowRule>"
      print "  </windowRules>"
    }
    { print }
  ' -v marker="$MARKER" "$LABWC_RC" > "$TMP" && mv "$TMP" "$LABWC_RC"
  echo "Fensterregel hinzugefügt: $LABWC_RC"
fi

echo ""
echo "Cursor sollte beim nächsten Start auf dem HDMI-Hauptbildschirm öffnen."
echo "Labwc-Konfiguration neu laden: Drücke Alt+F2, tippe 'reconfigure', Enter"
echo "Oder: Abmelden und neu anmelden"
