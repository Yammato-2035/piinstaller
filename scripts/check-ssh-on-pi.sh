#!/bin/bash
# Script zum Prüfen und Aktivieren von SSH auf dem Raspberry Pi
# Auf dem PI ausführen!

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 SSH Status-Prüfung auf Raspberry Pi${NC}"
echo ""

# 1. SSH-Status prüfen
echo -e "${BLUE}1. Prüfe SSH-Dienst-Status...${NC}"
if systemctl is-active --quiet ssh; then
    echo -e "${GREEN}✅ SSH-Dienst läuft${NC}"
else
    echo -e "${YELLOW}⚠️  SSH-Dienst läuft NICHT${NC}"
    echo ""
    read -p "SSH jetzt aktivieren? (j/n): " activate
    if [[ "$activate" == "j" ]]; then
        sudo systemctl enable ssh
        sudo systemctl start ssh
        echo -e "${GREEN}✅ SSH aktiviert und gestartet${NC}"
    fi
fi

echo ""

# 2. SSH-Port prüfen
echo -e "${BLUE}2. Prüfe SSH-Port (22)...${NC}"
if sudo netstat -tlnp | grep -q ":22 "; then
    echo -e "${GREEN}✅ Port 22 ist offen und SSH hört darauf${NC}"
    sudo netstat -tlnp | grep ":22 "
else
    echo -e "${RED}❌ Port 22 ist nicht offen${NC}"
    echo ""
    echo "Mögliche Ursachen:"
    echo "- SSH läuft auf einem anderen Port"
    echo "- Firewall blockiert Port 22"
    echo "- SSH-Dienst läuft nicht"
fi

echo ""

# 3. Firewall-Status prüfen
echo -e "${BLUE}3. Prüfe Firewall-Status...${NC}"
if command -v ufw > /dev/null 2>&1; then
    ufw_status=$(sudo ufw status | head -1)
    echo "UFW Status: $ufw_status"
    if echo "$ufw_status" | grep -q "active"; then
        echo -e "${YELLOW}⚠️  Firewall ist aktiv${NC}"
        if sudo ufw status | grep -q "22"; then
            echo -e "${GREEN}✅ Port 22 ist in der Firewall erlaubt${NC}"
        else
            echo -e "${RED}❌ Port 22 ist NICHT in der Firewall erlaubt${NC}"
            echo ""
            read -p "Port 22 in Firewall freigeben? (j/n): " allow_port
            if [[ "$allow_port" == "j" ]]; then
                sudo ufw allow 22/tcp
                echo -e "${GREEN}✅ Port 22 freigegeben${NC}"
            fi
        fi
    else
        echo -e "${GREEN}✅ Firewall ist nicht aktiv${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  UFW nicht installiert (andere Firewall möglich)${NC}"
fi

echo ""

# 4. SSH-Konfiguration prüfen
echo -e "${BLUE}4. Prüfe SSH-Konfiguration...${NC}"
if [ -f /etc/ssh/sshd_config ]; then
    ssh_port=$(sudo grep "^Port" /etc/ssh/sshd_config | awk '{print $2}' || echo "22")
    echo "SSH Port in Config: ${ssh_port:-22}"
    
    ssh_enabled=$(sudo grep "^PermitRootLogin" /etc/ssh/sshd_config | tail -1 || echo "Nicht gefunden")
    echo "SSH Config gefunden"
else
    echo -e "${RED}❌ SSH-Konfiguration nicht gefunden${NC}"
fi

echo ""

# 5. Zusammenfassung
echo -e "${BLUE}📊 Zusammenfassung:${NC}"
echo ""
if systemctl is-active --quiet ssh && sudo netstat -tlnp | grep -q ":22 "; then
    echo -e "${GREEN}✅ SSH sollte funktionieren!${NC}"
    echo ""
    echo "Teste von einem anderen Gerät:"
    echo "  ssh pi@$(hostname -I | awk '{print $1}')"
else
    echo -e "${YELLOW}⚠️  SSH benötigt noch Konfiguration${NC}"
    echo ""
    echo "Nächste Schritte:"
    echo "1. SSH aktivieren: sudo systemctl enable ssh && sudo systemctl start ssh"
    echo "2. Firewall prüfen: sudo ufw status"
    echo "3. Port freigeben: sudo ufw allow 22/tcp"
fi
