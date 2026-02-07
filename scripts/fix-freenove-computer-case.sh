#!/usr/bin/env bash
# Reparatur-Skript für Freenove Computer Case Kit Pro (Raspberry Pi 5)
# Behebt typische Ursachen, warum die Software nicht mehr startet.
#
# Verwendung (auf dem Pi):
#   ./fix-freenove-computer-case.sh
#   ./fix-freenove-computer-case.sh /pfad/zu/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi

set -e

FREENOVE_DIR="${1:-$HOME/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi}"
CODE_DIR="$FREENOVE_DIR/Code"
RUN_APP="$CODE_DIR/run_app.sh"
DESKTOP_FILE="$CODE_DIR/Freenove.desktop"

echo "=== Freenove Computer Case – Reparatur ==="
echo "Zielverzeichnis: $FREENOVE_DIR"
echo ""

if [[ ! -d "$FREENOVE_DIR" ]]; then
  echo "Fehler: Verzeichnis nicht gefunden: $FREENOVE_DIR"
  echo "Bitte zuerst klonen:"
  echo "  git clone https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi.git $FREENOVE_DIR"
  exit 1
fi

if [[ ! -f "$RUN_APP" ]]; then
  echo "Fehler: run_app.sh nicht gefunden: $RUN_APP"
  exit 1
fi

# 1) run_app.sh: python -> python3, ohne sudo (vermeidet XDG_RUNTIME_DIR-UID-Warnung)
if grep -q 'sudo python app_ui.py' "$RUN_APP"; then
  sed -i 's/sudo python app_ui.py/python3 app_ui.py/' "$RUN_APP"
  echo "[OK] run_app.sh: 'sudo python' durch 'python3' ersetzt (Start ohne root)."
elif grep -q 'sudo env.*python3 app_ui.py' "$RUN_APP"; then
  sed -i 's/sudo env XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" DISPLAY="$DISPLAY" python3 app_ui.py/python3 app_ui.py/' "$RUN_APP"
  echo "[OK] run_app.sh: sudo entfernt (Start ohne root)."
elif grep -q 'sudo python3 app_ui.py' "$RUN_APP"; then
  sed -i 's/sudo python3 app_ui.py/python3 app_ui.py/' "$RUN_APP"
  echo "[OK] run_app.sh: sudo entfernt (Start ohne root)."
else
  echo "[--] run_app.sh: Startzeile wurde nicht geändert."
fi

# 2) Freenove.desktop: Pfad auf aktuellen Benutzer anpassen
if [[ -f "$DESKTOP_FILE" ]]; then
  REAL_DIR="$(cd "$FREENOVE_DIR" && pwd)"
  if grep -q '/home/pi/' "$DESKTOP_FILE"; then
    sed -i "s|/home/pi/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi|$REAL_DIR|g" "$DESKTOP_FILE"
    echo "[OK] Freenove.desktop: Pfade auf $REAL_DIR angepasst."
  else
    echo "[--] Freenove.desktop: Pfade wurden nicht geändert (kein /home/pi/ gefunden)."
  fi
else
  echo "[--] Freenove.desktop nicht gefunden, übersprungen."
fi

echo ""
echo "=== Nächste Schritte ==="
echo "1) Abhängigkeiten auf dem Pi installieren (falls noch nicht geschehen):"
echo "   sudo apt update"
echo "   sudo apt install -y python3-pyqt5 python3-smbus"
echo ""
echo "2) I2C-Zugriff (einmalig): Benutzer in Gruppe i2c, dann abmelden/anmelden:"
echo "   sudo usermod -aG i2c \$USER"
echo ""
echo "3) App starten (ohne sudo):"
echo "   cd $CODE_DIR"
echo "   ./run_app.sh"
echo ""
echo "4) Desktop-Verknüpfung (optional):"
echo "   cp $DESKTOP_FILE ~/.local/share/applications/"
echo ""
echo "Weitere Hinweise: docs/FREENOVE_COMPUTER_CASE.md"
