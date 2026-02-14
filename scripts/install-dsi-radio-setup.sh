#!/bin/bash
# DSI-Radio Setup – GStreamer und Python-Bindings (gi) für Audiowiedergabe
#
# Behebt: "GStreamer nicht verfügbar – No module named 'gi'"
# Installiert Systempakete und richtet die Venv so ein, dass sie gi nutzen kann.
#
# Aufruf (mit sudo für Paketinstallation):
#   sudo ./scripts/install-dsi-radio-setup.sh
#
# Optional: Als normaler Benutzer nur Venv neu anlegen (wenn Pakete schon installiert):
#   ./scripts/install-dsi-radio-setup.sh --venv-only

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DSI_RADIO_DIR="$REPO_ROOT/apps/dsi_radio"
REAL_USER="${SUDO_USER:-$USER}"
VENV_ONLY=false

for arg in "$@"; do
  [ "$arg" = "--venv-only" ] && VENV_ONLY=true
done

echo "DSI-Radio Setup – $REPO_ROOT"
echo ""

if [ "$VENV_ONLY" = true ]; then
  echo "Nur Venv mit System-Paketen anlegen (apt-Installation übersprungen)."
  echo ""
else
  if [ "$(id -u)" -ne 0 ]; then
    echo "Hinweis: Ohne sudo werden keine Systempakete installiert."
    echo "Für GStreamer/gi bitte ausführen: sudo $0"
    echo ""
  else
    echo "[1] GStreamer und Python-GObject (gi) installieren …"
    # apt-get update kann fehlschlagen, wenn andere Repos (z. B. Cursor) keinen gültigen GPG-Schlüssel haben.
    # GStreamer-Pakete kommen von den Standard-Distro-Repos; Install wird trotzdem versucht.
    apt-get update -qq 2>/dev/null || true
    apt-get install -y --no-install-recommends \
      python3-gi \
      gir1.2-gstreamer-1.0 \
      gstreamer1.0-tools \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-pulseaudio \
      gstreamer1.0-libav
    echo "    Pakete installiert (inkl. gstreamer1.0-libav für AAC, z. B. NDR 1)."
    echo ""
  fi
fi

if [ ! -f "$DSI_RADIO_DIR/requirements.txt" ]; then
  echo "apps/dsi_radio/requirements.txt nicht gefunden. Abbruch."
  exit 1
fi

echo "[2] Venv mit System-Paketen (--system-site-packages) anlegen …"
echo "    So kann die App das systemweit installierte 'gi' (GStreamer) nutzen."
cd "$DSI_RADIO_DIR"

if [ -d ".venv" ]; then
  echo "    Alte .venv wird entfernt und neu erstellt."
  rm -rf .venv
fi

# Als root: Venv im Namen des echten Benutzers anlegen (damit Besitzer stimmt)
if [ "$(id -u)" -eq 0 ] && [ -n "$REAL_USER" ] && [ "$REAL_USER" != "root" ]; then
  chown -R "$REAL_USER:" "$DSI_RADIO_DIR" 2>/dev/null || true
  su - "$REAL_USER" -c "cd '$DSI_RADIO_DIR' && python3 -m venv --system-site-packages .venv && .venv/bin/pip install --quiet -r requirements.txt" || {
    echo "    Venv als $REAL_USER fehlgeschlagen, versuche als root …"
    python3 -m venv --system-site-packages .venv
    .venv/bin/pip install --quiet -r requirements.txt
  }
else
  python3 -m venv --system-site-packages .venv
  .venv/bin/pip install --quiet -r requirements.txt
fi

echo "    Venv bereit."
echo ""
echo "Fertig. DSI Radio neu starten (z. B. über Desktop-Starter „DSI Radio“)."
echo "WDR 2 und andere Streams sollten nun mit GStreamer laufen."
