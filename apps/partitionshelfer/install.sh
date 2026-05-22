#!/bin/bash
# install.sh – Setuphelfer Partitionierungstool einrichten
# Aufruf: bash install.sh

set -e

GRUEN='\033[0;32m'
GELB='\033[1;33m'
ROT='\033[0;31m'
AKZENT='\033[0;36m'
RESET='\033[0m'

echo ""
echo -e "${AKZENT}╔══════════════════════════════════════════╗${RESET}"
echo -e "${AKZENT}║   Setuphelfer Partitionshelfer           ║${RESET}"
echo -e "${AKZENT}║   Installation                           ║${RESET}"
echo -e "${AKZENT}╚══════════════════════════════════════════╝${RESET}"
echo ""

# ── Betriebssystem erkennen ──────────────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

echo -e "  System: ${GELB}$DISTRO${RESET}"
echo ""

# ── Python prüfen ────────────────────────────────────────────
echo -e "→ Prüfe Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "  ${ROT}✗ Python 3 nicht gefunden${RESET}"
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "  ${GRUEN}✓ Python $PYTHON_VER${RESET}"

# ── tkinter installieren ─────────────────────────────────────
echo -e "→ Prüfe tkinter..."
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo -e "  ${GELB}⚠ tkinter fehlt – wird installiert...${RESET}"

    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            sudo apt-get install -y python3-tk
            ;;
        fedora|rhel|centos)
            sudo dnf install -y python3-tkinter
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm tk
            ;;
        opensuse*)
            sudo zypper install -y python3-tk
            ;;
        *)
            echo -e "  ${ROT}Unbekannte Distribution. Installiere python3-tk manuell.${RESET}"
            exit 1
            ;;
    esac
else
    echo -e "  ${GRUEN}✓ tkinter vorhanden${RESET}"
fi

# ── lsblk prüfen ─────────────────────────────────────────────
echo -e "→ Prüfe lsblk..."
if ! command -v lsblk &>/dev/null; then
    echo -e "  ${ROT}✗ lsblk fehlt (util-linux benötigt)${RESET}"
    exit 1
fi
echo -e "  ${GRUEN}✓ lsblk vorhanden${RESET}"

# ── Startscript ausführbar machen ────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/start.py"

# ── Desktop-Eintrag erstellen (optional) ─────────────────────
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/setuphelfer-partition.desktop" << EOF
[Desktop Entry]
Name=Setuphelfer Partitionshelfer
Comment=Festplatten anzeigen und Partitionierung planen
Exec=python3 $SCRIPT_DIR/start.py
Icon=drive-harddisk
Terminal=false
Type=Application
Categories=System;
StartupNotify=true
EOF

echo -e "  ${GRUEN}✓ Desktop-Eintrag erstellt${RESET}"

# ── Zusammenfassung ───────────────────────────────────────────
echo ""
echo -e "${GRUEN}╔══════════════════════════════════════════╗${RESET}"
echo -e "${GRUEN}║   Installation abgeschlossen! ✓          ║${RESET}"
echo -e "${GRUEN}╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Starten mit:"
echo -e "  ${AKZENT}python3 $SCRIPT_DIR/start.py${RESET}"
echo ""
echo -e "  Oder aus dem Anwendungsmenü: ${AKZENT}Setuphelfer Partitionshelfer${RESET}"
echo ""
