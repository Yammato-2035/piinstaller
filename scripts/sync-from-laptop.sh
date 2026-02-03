#!/bin/bash
# Holt neueste Code-Änderungen vom Laptop (über GitHub) auf den Pi
# Verwendung: ./sync-from-laptop.sh

set -e

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}⬇️  Hole neueste Code-Änderungen vom Laptop...${NC}"

# Prüfe ob wir in einem Git-Repository sind
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Fehler: Nicht in einem Git-Repository!${NC}"
    exit 1
fi

# Aktuellen Branch ermitteln
current_branch=$(git branch --show-current)
echo -e "${BLUE}Branch: $current_branch${NC}"

# Status vor Pull anzeigen
echo ""
echo -e "${BLUE}📊 Status vor Pull:${NC}"
git status -sb

# Neueste Änderungen holen
echo ""
echo -e "${BLUE}⬇️  Pull von GitHub...${NC}"
if git pull origin "$current_branch"; then
    echo -e "${GREEN}✅ Code erfolgreich aktualisiert${NC}"
else
    echo -e "${YELLOW}⚠️  Pull fehlgeschlagen - möglicherweise Konflikte${NC}"
    echo -e "${YELLOW}Prüfe 'git status' für Details${NC}"
    exit 1
fi

# Status nach Pull anzeigen
echo ""
echo -e "${BLUE}📊 Status nach Pull:${NC}"
git status -sb

# Änderungen der letzten Commits anzeigen
echo ""
echo -e "${BLUE}📝 Letzte Änderungen:${NC}"
git log --oneline -5

echo ""
echo -e "${GREEN}✅ Synchronisation abgeschlossen!${NC}"
