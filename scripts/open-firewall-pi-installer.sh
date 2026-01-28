#!/bin/bash
# PI-Installer – Firewall-Ports für Frontend, Backend und ggf. Website freigeben
# UFW muss installiert sein. Mit sudo ausführen: ./scripts/open-firewall-pi-installer.sh

set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte mit sudo ausführen: sudo $0"
  exit 1
fi

if ! command -v ufw &>/dev/null; then
  echo "UFW ist nicht installiert. Installieren mit: apt install ufw"
  exit 1
fi

echo "Öffne UFW-Ports für PI-Installer..."
ufw allow 3001/tcp comment 'PI-Installer Frontend'
ufw allow 8000/tcp comment 'PI-Installer Backend'
ufw allow 80/tcp comment 'HTTP (Website)'
ufw allow 443/tcp comment 'HTTPS (Website)'
echo ""
echo "UFW-Status:"
ufw status | grep -E '3001|8000|80|443|Status' || ufw status
echo ""
echo "Falls UFW noch deaktiviert war: 'ufw enable' ausführen und ggf. neu starten."
