#!/bin/bash
# PI-Installer – Installations-Wrapper
# Bietet Auswahl zwischen systemweiter und Benutzer-Installation
#
# Verwendung:
#   curl -sSL https://raw.githubusercontent.com/IHR-USERNAME/PI-Installer/main/scripts/install.sh | bash
#   Oder: ./scripts/install.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Prüfe ob wir im Repository sind
if [ -f "$REPO_ROOT/start.sh" ] && [ -d "$REPO_ROOT/backend" ] && [ -d "$REPO_ROOT/frontend" ]; then
  FROM_REPO=1
else
  FROM_REPO=0
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  PI-Installer Installation${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${CYAN}Wählen Sie die Installationsmethode:${NC}"
echo ""
echo -e "  ${GREEN}1)${NC} Systemweite Installation (empfohlen für Produktion)"
echo -e "     → Installiert nach /opt/pi-installer/"
echo -e "     → Globale Befehle verfügbar"
echo -e "     → Benötigt sudo"
echo ""
echo -e "  ${GREEN}2)${NC} Benutzer-Installation (für Entwicklung/Test)"
echo -e "     → Installiert nach \$HOME/PI-Installer/"
echo -e "     → Keine Root-Rechte nötig"
echo ""
echo -e "  ${GREEN}3)${NC} Abbrechen"
echo ""

if [ "$FROM_REPO" -eq 1 ]; then
  # Im Repository: lokale Skripte verwenden
  read -p "Ihre Wahl (1-3): " choice
  
  case $choice in
    1)
      echo ""
      echo -e "${CYAN}Starte systemweite Installation...${NC}"
      sudo "$SCRIPT_DIR/install-system.sh"
      ;;
    2)
      echo ""
      echo -e "${CYAN}Starte Benutzer-Installation...${NC}"
      "$SCRIPT_DIR/create_installer.sh"
      ;;
    3)
      echo "Installation abgebrochen."
      exit 0
      ;;
    *)
      echo -e "${RED}Ungültige Auswahl.${NC}"
      exit 1
      ;;
  esac
else
  # Nicht im Repository: von GitHub laden
  DEFAULT_REPO="${PI_INSTALLER_REPO:-https://github.com/pi-installer/PI-Installer.git}"
  REPO_OWNER=$(echo "$DEFAULT_REPO" | sed -n 's|.*github.com/\([^/]*\)/.*|\1|p')
  
  if [ -z "$REPO_OWNER" ]; then
    REPO_OWNER="IHR-USERNAME"
  fi
  
  read -p "Ihre Wahl (1-3): " choice
  
  case $choice in
    1)
      echo ""
      echo -e "${CYAN}Lade Installations-Skript von GitHub...${NC}"
      curl -sSL "https://raw.githubusercontent.com/$REPO_OWNER/PI-Installer/main/scripts/install-system.sh" | sudo bash
      ;;
    2)
      echo ""
      echo -e "${CYAN}Lade Installations-Skript von GitHub...${NC}"
      curl -sSL "https://raw.githubusercontent.com/$REPO_OWNER/PI-Installer/main/scripts/create_installer.sh" | bash
      ;;
    3)
      echo "Installation abgebrochen."
      exit 0
      ;;
    *)
      echo -e "${RED}Ungültige Auswahl.${NC}"
      exit 1
      ;;
  esac
fi
