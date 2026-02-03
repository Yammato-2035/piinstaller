#!/bin/bash
# Synchronisiert Code-Änderungen vom Laptop zum Pi über GitHub
# Verwendung: ./sync-to-pi.sh [commit-message]

set -e

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Synchronisiere Code-Änderungen zum Pi...${NC}"

# Prüfe ob wir in einem Git-Repository sind
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Fehler: Nicht in einem Git-Repository!${NC}"
    exit 1
fi

# Prüfe auf uncommitted Änderungen
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}📝 Lokale Änderungen gefunden...${NC}"
    
    # Commit-Nachricht als Parameter oder interaktiv
    if [[ -n "$1" ]]; then
        commit_msg="$1"
    else
        read -p "Commit-Nachricht eingeben: " commit_msg
        if [[ -z "$commit_msg" ]]; then
            echo -e "${YELLOW}⚠️  Keine Commit-Nachricht - überspringe Commit${NC}"
        fi
    fi
    
    if [[ -n "$commit_msg" ]]; then
        git add .
        git commit -m "$commit_msg"
        echo -e "${GREEN}✅ Änderungen committed${NC}"
    fi
fi

# Auf GitHub pushen
echo -e "${BLUE}⬆️  Pushe auf GitHub...${NC}"
current_branch=$(git branch --show-current)
git push origin "$current_branch"

# Auf dem Pi pullen (optional, falls SSH verfügbar)
if command -v ssh > /dev/null 2>&1; then
    echo -e "${BLUE}⬇️  Aktualisiere Pi-Repository...${NC}"
    if ssh -o ConnectTimeout=5 pi "cd ~/Documents/PI-Installer && git pull origin $current_branch" 2>/dev/null; then
        echo -e "${GREEN}✅ Pi-Repository aktualisiert${NC}"
    else
        echo -e "${YELLOW}⚠️  Pi-Update übersprungen (SSH nicht verfügbar oder Fehler)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SSH nicht verfügbar - Pi-Update übersprungen${NC}"
fi

echo -e "${GREEN}✅ Synchronisation abgeschlossen!${NC}"
