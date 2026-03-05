#!/bin/bash
# Legt unter ~/Pictures/PI-Installer-Samples einen Ordner an und lädt
# Musterbilder zum Testen des Bilderrahmen-Apps (z. B. von Picsum).
# Optional: Nutzer können eigene Bilder von Pixabay etc. in den Ordner legen.
#
# Verwendung: ./scripts/setup-picture-frame-samples.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PICTURES="${HOME}/Pictures"
SAMPLES="${PICTURES}/PI-Installer-Samples"
mkdir -p "$SAMPLES"
# Kurze Info für Nutzer (z. B. eigene Bilder von Pixabay hier ablegen)
if [ ! -f "${SAMPLES}/README.txt" ]; then
  cat > "${SAMPLES}/README.txt" << 'EOF'
PI-Installer Bilderrahmen – Musterordner
Weitere freie Bilder z. B. von https://pixabay.com hier ablegen (jpg, png, gif).
EOF
fi

echo "Ordner: $SAMPLES"

# Einige Musterbilder von Picsum (kostenlos, keine API nötig)
# Falls curl fehlt: Ordner ist trotzdem angelegt, Bilder manuell einfügen.
if command -v curl >/dev/null 2>&1; then
  for i in 1 2 3 4 5; do
    out="${SAMPLES}/sample-${i}.jpg"
    if [ ! -f "$out" ]; then
      echo "Lade Musterbild $i …"
      curl -sL -o "$out" "https://picsum.photos/800/600?random=$i" || true
    fi
  done
  echo "Musterbilder in $SAMPLES angelegt."
else
  echo "Hinweis: curl nicht gefunden. Ordner $SAMPLES ist angelegt."
  echo "Bilder manuell ablegen oder von https://pixabay.com/images/search/nature/ herunterladen."
fi

echo ""
echo "Bilderrahmen starten: $REPO_ROOT/scripts/start-picture-frame.sh"
echo "In der App unter Einstellungen den Ordner '$SAMPLES' wählen."
