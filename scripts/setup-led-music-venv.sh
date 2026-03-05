#!/usr/bin/env bash
# Erstellt eine virtuelle Umgebung (venv) für das LED-Musik-Skript und
# installiert numpy und sounddevice. Unter Raspberry Pi OS / Debian ist
# systemweites pip blockiert (externally-managed-environment); die venv
# umgeht das.
#
# Verwendung:
#   ./scripts/setup-led-music-venv.sh
# Danach starten:
#   ./scripts/venv-led-music/bin/python scripts/led-music-reactive.py

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv-led-music"

echo "Python venv für LED-Musik-Skript einrichten ..."

# System-Pakete (I2C, venv-Unterstützung, PortAudio für sounddevice)
if command -v apt-get &>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y python3-smbus python3-venv python3-full libportaudio2
fi

# venv anlegen (--system-site-packages, damit python3-smbus aus apt sichtbar ist)
if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv --system-site-packages "${VENV_DIR}"
  echo "venv erstellt: ${VENV_DIR} (mit System-Paketen, u.a. smbus)"
else
  echo "venv existiert bereits: ${VENV_DIR}"
  echo "Falls 'No module named smbus' erscheint: ${VENV_DIR} löschen und dieses Skript erneut ausführen."
fi

# pip upgraden und Abhängigkeiten installieren
"${VENV_DIR}/bin/pip" install --upgrade pip -q
"${VENV_DIR}/bin/pip" install numpy sounddevice

echo "Fertig. Starten mit:"
echo "  ${VENV_DIR}/bin/python ${SCRIPT_DIR}/led-music-reactive.py"
