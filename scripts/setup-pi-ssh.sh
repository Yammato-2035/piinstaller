#!/bin/bash
# Script zum manuellen Kopieren des SSH-Keys auf den Pi
# Verwendung: ./setup-pi-ssh.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔑 SSH-Key Setup für Raspberry Pi${NC}"
echo ""

# Öffentlichen Key anzeigen
echo -e "${BLUE}Dein öffentlicher SSH-Key:${NC}"
echo ""
cat ~/.ssh/id_ed25519_pi.pub
echo ""
echo ""

# Optionen anbieten
echo -e "${YELLOW}Wähle eine Option:${NC}"
echo "1) Key automatisch kopieren (benötigt Passwort)"
echo "2) Key manuell kopieren (Anleitung anzeigen)"
read -p "Option (1 oder 2): " option

case $option in
    1)
        echo -e "${BLUE}Versuche Key automatisch zu kopieren...${NC}"
        ssh-copy-id -i ~/.ssh/id_ed25519_pi.pub pi@192.168.178.68
        ;;
    2)
        echo ""
        echo -e "${BLUE}📋 Manuelle Anleitung:${NC}"
        echo ""
        echo "1. Kopiere den oben angezeigten SSH-Key (die gesamte Zeile)"
        echo ""
        echo "2. Verbinde dich mit dem Pi:"
        echo -e "   ${GREEN}ssh pi@192.168.178.68${NC}"
        echo ""
        echo "3. Auf dem Pi ausführen:"
        echo -e "   ${GREEN}mkdir -p ~/.ssh${NC}"
        echo -e "   ${GREEN}chmod 700 ~/.ssh${NC}"
        echo -e "   ${GREEN}echo 'DEIN_GEKOPIERTER_KEY' >> ~/.ssh/authorized_keys${NC}"
        echo -e "   ${GREEN}chmod 600 ~/.ssh/authorized_keys${NC}"
        echo ""
        echo "4. Zurück auf dem Laptop testen:"
        echo -e "   ${GREEN}ssh pi${NC}"
        ;;
    *)
        echo -e "${YELLOW}Ungültige Option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Setup abgeschlossen!${NC}"
