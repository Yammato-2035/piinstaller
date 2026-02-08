#!/usr/bin/env bash
# PI-Installer – Wayfire-Fensterregel für DSI-Radio prüfen/anlegen
#
# Beim Start von DSI-Radio legt Wayfire das Fenster standardmäßig oft auf HDMI.
# Diese Regel verhindert das: Sobald ein Fenster mit Titel „PI-Installer DSI …“
# erstellt wird, wird es automatisch auf DSI-1 (TFT) gelegt – nicht auf HDMI.
#
# Als Benutzer ausführen (nicht sudo): ./scripts/ensure-dsi-window-rule.sh
# Danach: einmal abmelden/anmelden oder Wayfire neu starten.
# Ausgabe-Name prüfen: wlr-randr oder ./scripts/display-names-test.sh

set -e

# Wayfire-Ausgabe für das DSI/TFT-Display (beim Freenove TFT: DSI-1)
DSI_OUTPUT="${PI_INSTALLER_DSI_OUTPUT:-DSI-1}"

WF_INI="${XDG_CONFIG_HOME:-$HOME/.config}/wayfire.ini"
MARKER="# --- PI-Installer: DSI-Fensterregel ---"
MARKER_END="# --- Ende PI-Installer DSI ---"
# Zwei getrennte Regeln (OR-Syntax kann je nach Wayfire-Version Probleme machen)
RULE_APP="dsi_pi_installer_app = on created if app_id is \"pi-installer-dsi-radio\" then start_on_output \"$DSI_OUTPUT\""
RULE_TITLE="dsi_pi_installer_title = on created if title contains \"PI-Installer DSI\" then start_on_output \"$DSI_OUTPUT\""

mkdir -p "$(dirname "$WF_INI")"

# Alte PI-Installer DSI-Regel entfernen (unser Block mit Marker)
if [ -f "$WF_INI" ] && grep -q "$MARKER" "$WF_INI" 2>/dev/null; then
  sed -i "/$MARKER/,/$MARKER_END/d" "$WF_INI"
fi

# Wenn beide Regeln schon da sind, nichts tun
if [ -f "$WF_INI" ] && grep -q "dsi_pi_installer_app" "$WF_INI" 2>/dev/null && grep -q "dsi_pi_installer_title" "$WF_INI" 2>/dev/null; then
  echo "Wayfire-Regeln für DSI-Radio sind bereits in $WF_INI vorhanden (start_on_output $DSI_OUTPUT)."
  grep "dsi_pi_installer\|start_on_output.*DSI" "$WF_INI" 2>/dev/null || true
  exit 0
fi

# Regeln anhängen (evtl. neuer [window-rules]-Block)
# Zwei Regeln: app_id (native App) und title (Fallback/Browser) – eine reicht für start_on_output DSI-1
{
  echo ""
  echo "$MARKER"
  echo "# DSI-Radio: Fenster erscheint sonst auf HDMI – diese Regeln legen es beim Start auf DSI-1 (TFT)."
  echo "[window-rules]"
  echo "$RULE_APP"
  echo "$RULE_TITLE"
  echo "$MARKER_END"
} >> "$WF_INI"

echo "Wayfire-Regel in $WF_INI eingetragen:"
echo "  Beim Start von DSI-Radio wird das Fenster automatisch auf $DSI_OUTPUT gelegt (nicht auf HDMI)."
echo ""
echo "Damit es greift: einmal abmelden/anmelden oder Wayfire neu starten."
echo "Danach DSI-Radio starten: ./scripts/start-dsi-radio.sh"
echo ""
