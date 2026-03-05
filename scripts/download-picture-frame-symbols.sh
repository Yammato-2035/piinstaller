#!/bin/bash
# Lädt rechtefreie Symbol-Icons (Lucide Icons, MIT-Lizenz) für den Bilderrahmen.
# Quelle: https://lucide.dev – Open Source, kommerziell nutzbar.
# Konvertiert SVG → PNG, damit die App die Symbole auch ohne PyQt6-QtSvg anzeigen kann.
#
# Verwendung: ./scripts/download-picture-frame-symbols.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYMBOLS_BASE="$REPO_ROOT/apps/picture_frame/symbols"
CDN="https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons"
PNG_SIZE=128

mkdir -p "$SYMBOLS_BASE"

# SVG zu PNG konvertieren (App braucht keine QtSvg)
svg2png() {
  local svg="$1"
  local png="${svg%.svg}.png"
  [ ! -f "$svg" ] || [ -s "$svg" ] || return 0
  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w $PNG_SIZE -h $PNG_SIZE -o "$png" "$svg" 2>/dev/null && return 0
  fi
  if command -v convert >/dev/null 2>&1; then
    convert -background none -resize "${PNG_SIZE}x${PNG_SIZE}" "$svg" "$png" 2>/dev/null && return 0
  fi
  return 1
}

# Theme -> Icon-Dateinamen (Lucide, kebab-case)
download_theme() {
  local theme="$1"
  shift
  local dir="$SYMBOLS_BASE/$theme"
  mkdir -p "$dir"
  for icon in "$@"; do
    local out="$dir/${icon}.svg"
    if [ ! -f "$out" ]; then
      echo "  $theme: $icon.svg"
      curl -sL -o "$out" "$CDN/${icon}.svg" 2>/dev/null || true
      [ -s "$out" ] || rm -f "$out"
    fi
    # PNG erzeugen, damit die App ohne QtSvg auskommt
    if [ -s "$out" ]; then
      if [ ! -f "${out%.svg}.png" ] || [ "$out" -nt "${out%.svg}.png" ]; then
        svg2png "$out" && echo "    → ${icon}.png"
      fi
    fi
  done
}

echo "Lade rechtefreie Icons (Lucide, MIT) …"

download_theme weihnachten   tree-pine gift bell star snowflake
download_theme ostern       egg flower-2 flower
download_theme geburtstag   cake gift party-popper sparkles
download_theme valentinstag heart flower-2
download_theme hochzeitstag heart circle flower-2
download_theme halloween    skull moon cat ghost

echo "Fertig. Symbole in: $SYMBOLS_BASE"
echo "Hinweis: Ohne rsvg-convert oder ImageMagick (convert) bleiben nur .svg – dann PyQt6 mit QtSvg nutzen."
