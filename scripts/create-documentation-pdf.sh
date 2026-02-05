#!/bin/bash
# Erstellt eine PDF-Datei aus der PI-Installer Dokumentation.
# Verwendung: ./scripts/create-documentation-pdf.sh
#
# Voraussetzungen (eine der Optionen):
#   - pandoc + texlive-xetex:  sudo apt install pandoc texlive-xetex
#   - oder: Node.js/npm (für npx md-to-pdf)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/docs"
PDF_NAME="PI-Installer-Dokumentation.pdf"
MD_NAME="PI-Installer-Dokumentation.md"

cd "$PROJECT_ROOT"

mkdir -p "$OUTPUT_DIR"

# Kombinierte Markdown-Datei erstellen
echo "📝 Erstelle kombinierte Dokumentation..."
{
  echo "# PI-Installer – Dokumentation"
  echo ""
  echo "Version: $(cat VERSION 2>/dev/null || echo '?') | Stand: $(date '+%Y-%m-%d')"
  echo ""
  echo "---"
  echo ""

  # README
  echo "# Teil 1: Übersicht"
  echo ""
  cat README.md 2>/dev/null || true
  echo ""
  echo "---"
  echo ""

  # QUICKSTART
  echo "# Teil 2: Schnellstart & Fehlerbehebung"
  echo ""
  cat QUICKSTART.md 2>/dev/null || true
  echo ""
  echo "---"
  echo ""

  # INSTALL
  echo "# Teil 3: Installationsanleitung"
  echo ""
  cat INSTALL.md 2>/dev/null || true
  echo ""
  echo "---"
  echo ""

  # PI_OPTIMIZATION
  if [ -f PI_OPTIMIZATION.md ]; then
    echo "# Teil 4: Raspberry Pi Optimierung"
    echo ""
    cat PI_OPTIMIZATION.md
    echo ""
    echo "---"
    echo ""
  fi

  # CHANGELOG (gekürzt – letzte Einträge)
  echo "# Teil 5: Changelog (Auszug)"
  echo ""
  head -80 CHANGELOG.md 2>/dev/null || true
  echo ""
  echo "... (vollständig: CHANGELOG.md)"
} > "$OUTPUT_DIR/$MD_NAME"

echo "✅ Markdown erstellt: $OUTPUT_DIR/$MD_NAME"

# PDF erstellen
PDF_PATH="$OUTPUT_DIR/$PDF_NAME"

if command -v pandoc >/dev/null 2>&1; then
  echo "📄 Erstelle PDF mit pandoc..."
  pandoc "$OUTPUT_DIR/$MD_NAME" -o "$PDF_PATH" \
    --pdf-engine=xelatex \
    -V geometry:margin=2.5cm \
    -V lang=de \
    -V documentclass=article \
    -V fontsize=11pt \
    -V toc-title="Inhaltsverzeichnis" \
    --toc \
    --toc-depth=3 \
    2>/dev/null || pandoc "$OUTPUT_DIR/$MD_NAME" -o "$PDF_PATH" -V geometry:margin=2.5cm 2>/dev/null || true
  if [ -f "$PDF_PATH" ]; then
    echo "✅ PDF erstellt: $PDF_PATH"
    exit 0
  fi
fi

if command -v npx >/dev/null 2>&1; then
  echo "📄 Erstelle PDF mit md-to-pdf (npx) – beim ersten Mal kann der Download von Chromium einige Minuten dauern..."
  if npx --yes md-to-pdf "$OUTPUT_DIR/$MD_NAME" --pdf-options '{"format":"A4","margin":"25mm"}'; then
    if [ -f "$OUTPUT_DIR/PI-Installer-Dokumentation.pdf" ]; then
      echo "✅ PDF erstellt: $OUTPUT_DIR/PI-Installer-Dokumentation.pdf"
      exit 0
    fi
  fi
fi

echo ""
echo "⚠️  PDF konnte nicht erstellt werden."
echo ""
echo "Installieren Sie eines der folgenden:"
echo "  • pandoc + texlive-xetex:  sudo apt install pandoc texlive-xetex"
echo "  • oder Node.js, dann:      npx md-to-pdf $OUTPUT_DIR/$MD_NAME"
echo ""
echo "Die kombinierte Markdown-Datei wurde erstellt:"
echo "  $OUTPUT_DIR/$MD_NAME"
echo "Sie können diese z.B. in VS Code mit einer PDF-Extension oder online konvertieren."
exit 1
