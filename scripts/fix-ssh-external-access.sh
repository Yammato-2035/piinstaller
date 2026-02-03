#!/bin/bash
# Script zum Aktivieren von externem SSH-Zugriff auf dem Raspberry Pi
# AUF DEM PI AUSFÜHREN!

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 SSH Externer Zugriff aktivieren${NC}"
echo ""

# 1. Prüfe SSH-Konfiguration
echo -e "${BLUE}1. Prüfe SSH-Konfiguration...${NC}"
ssh_config="/etc/ssh/sshd_config"

# Backup erstellen
if [ ! -f "${ssh_config}.backup" ]; then
    sudo cp "$ssh_config" "${ssh_config}.backup"
    echo -e "${GREEN}✅ Backup erstellt: ${ssh_config}.backup${NC}"
fi

# Prüfe ListenAddress
listen_address=$(sudo grep "^ListenAddress" "$ssh_config" || echo "Nicht gesetzt")
echo "Aktuelle ListenAddress: $listen_address"

if echo "$listen_address" | grep -q "127.0.0.1"; then
    echo -e "${YELLOW}⚠️  SSH hört nur auf localhost${NC}"
    echo ""
    read -p "SSH auf alle Interfaces umstellen? (j/n): " change_listen
    if [[ "$change_listen" == "j" ]]; then
        # Kommentiere ListenAddress aus oder ändere es
        sudo sed -i 's/^ListenAddress/#ListenAddress/' "$ssh_config"
        echo -e "${GREEN}✅ ListenAddress angepasst${NC}"
    fi
fi

# 2. Prüfe Port
port=$(sudo grep "^Port" "$ssh_config" | awk '{print $2}' || echo "22")
echo "SSH Port: $port"

# 3. Prüfe ob SSH auf allen Interfaces hört
echo ""
echo -e "${BLUE}2. Prüfe auf welchen Interfaces SSH hört...${NC}"
sudo netstat -tlnp | grep ":${port} " || sudo ss -tlnp | grep ":${port} "

# 4. Firewall prüfen
echo ""
echo -e "${BLUE}3. Prüfe Firewall...${NC}"
if command -v ufw > /dev/null 2>&1; then
    ufw_status=$(sudo ufw status | head -1)
    echo "UFW Status: $ufw_status"
    
    if echo "$ufw_status" | grep -q "active"; then
        if sudo ufw status | grep -q "${port}"; then
            echo -e "${GREEN}✅ Port ${port} ist in der Firewall erlaubt${NC}"
        else
            echo -e "${YELLOW}⚠️  Port ${port} ist NICHT in der Firewall erlaubt${NC}"
            read -p "Port ${port} freigeben? (j/n): " allow_port
            if [[ "$allow_port" == "j" ]]; then
                sudo ufw allow ${port}/tcp
                sudo ufw reload
                echo -e "${GREEN}✅ Port ${port} freigegeben${NC}"
            fi
        fi
    fi
fi

# 5. iptables prüfen (falls vorhanden)
if command -v iptables > /dev/null 2>&1; then
    echo ""
    echo -e "${BLUE}4. Prüfe iptables Regeln...${NC}"
    if sudo iptables -L INPUT -n | grep -q "DROP.*22"; then
        echo -e "${YELLOW}⚠️  iptables blockiert möglicherweise Port 22${NC}"
        echo "Prüfe manuell: sudo iptables -L INPUT -n | grep 22"
    fi
fi

# 6. SSH neu laden
echo ""
echo -e "${BLUE}5. SSH-Konfiguration neu laden...${NC}"
read -p "SSH-Dienst neu laden (testen der Konfiguration)? (j/n): " reload
if [[ "$reload" == "j" ]]; then
    # Teste Konfiguration
    if sudo sshd -t; then
        echo -e "${GREEN}✅ SSH-Konfiguration ist gültig${NC}"
        sudo systemctl reload sshd
        echo -e "${GREEN}✅ SSH-Dienst neu geladen${NC}"
    else
        echo -e "${RED}❌ SSH-Konfiguration hat Fehler!${NC}"
        echo "Stelle Backup wieder her: sudo cp ${ssh_config}.backup ${ssh_config}"
        exit 1
    fi
fi

# 7. Zusammenfassung
echo ""
echo -e "${BLUE}📊 Zusammenfassung:${NC}"
echo ""
echo "SSH Status:"
sudo systemctl status ssh --no-pager | head -3

echo ""
echo "SSH hört auf:"
sudo netstat -tlnp | grep ":${port} " || sudo ss -tlnp | grep ":${port} "

echo ""
echo -e "${GREEN}✅ Fertig!${NC}"
echo ""
echo "Teste die Verbindung von einem anderen Gerät:"
echo "  ssh gabrielglienke@192.168.178.68"
