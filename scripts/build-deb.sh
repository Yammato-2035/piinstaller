#!/bin/bash
# Baut das PI-Installer Debian-Paket (.deb).
# Voraussetzung: debhelper, rsync (apt install debhelper rsync)
# Ausführung: im Repository-Root: ./scripts/build-deb.sh
# Ergebnis: ../setuphelfer_<version>_all.deb

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -d "debian" ] || [ ! -f "debian/control" ]; then
  echo "Fehler: debian/ nicht gefunden. Bitte im Repository-Root ausführen." >&2
  exit 1
fi

# Version aus config/version.json oder historischer VERSION-Datei
VERSION="1.3.4.5"
if [ -f "config/version.json" ]; then
  if command -v jq >/dev/null 2>&1; then
    VERSION="$(jq -r '.version // empty' config/version.json 2>/dev/null)" || true
  else
    VERSION="$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' config/version.json 2>/dev/null | sed 's/.*"\([^"]*\)"$/\1/')" || true
  fi
fi
[ -z "$VERSION" ] && [ -f "VERSION" ] && VERSION="$(cat VERSION | tr -d '\n')"
[ -z "$VERSION" ] && VERSION="1.3.4.5"
echo "Baue pi-installer ${VERSION}..."

# Tauri Binary bauen, falls nicht vorhanden
TAURI_BINARY="frontend/src-tauri/target/release/pi-installer"
if [ ! -f "$TAURI_BINARY" ]; then
  echo ""
  echo "⚠️  Tauri Binary nicht gefunden. Baue es jetzt..."
  if command -v cargo >/dev/null 2>&1; then
    cd frontend
    export PATH="$HOME/.cargo/bin:/usr/local/bin:$PATH"
    [ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
    if npm run tauri:build; then
      echo "✅ Tauri Binary erfolgreich erstellt."
      cd ..
    else
      echo "❌ Tauri Build fehlgeschlagen. Paket wird ohne Tauri Binary gebaut."
      cd ..
    fi
  else
    echo "⚠️  Cargo nicht gefunden. Paket wird ohne Tauri Binary gebaut."
    echo "   Für Tauri Binary: Rust installieren (curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh)"
  fi
else
  echo "✅ Tauri Binary gefunden: $TAURI_BINARY"
fi

# Hinweis: Source-Paketname in debian/changelog bleibt „pi-installer“ (debian/control: Source); Binary-Paket: setuphelfer.

dpkg-buildpackage -us -uc -b -tc

echo ""
echo "Fertig. Paket liegt im übergeordneten Verzeichnis:"
ls -la ../setuphelfer_*_all.deb 2>/dev/null || true
echo ""
echo "Installation: sudo apt install ./setuphelfer_${VERSION}-1_all.deb"
echo "Update:       sudo apt install --only-upgrade ./setuphelfer_*.deb"
