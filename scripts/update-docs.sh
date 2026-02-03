#!/bin/bash
# Aktualisiert Dokumentation auf dem Raspberry Pi und pusht auf GitHub
# Verwendung: ./update-docs.sh [datei] [commit-message]

set -e

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📚 Dokumentations-Update...${NC}"

# Prüfe ob wir in einem Git-Repository sind
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Fehler: Nicht in einem Git-Repository!${NC}"
    exit 1
fi

# Neueste Änderungen vom GitHub holen
echo -e "${BLUE}⬇️  Hole neueste Änderungen...${NC}"
current_branch=$(git branch --show-current)
git pull origin "$current_branch" || echo -e "${YELLOW}⚠️  Pull fehlgeschlagen - fortfahren...${NC}"

# Dokumentationsdateien auflisten
echo ""
echo -e "${BLUE}Verfügbare Dokumentationsdateien:${NC}"
docs=$(find . -maxdepth 1 -name "*.md" -type f | sort)
if [[ -n "$docs" ]]; then
    echo "$docs" | nl
else
    echo -e "${YELLOW}Keine .md Dateien gefunden${NC}"
fi

# Datei auswählen
if [[ -n "$1" ]]; then
    doc_file="$1"
else
    echo ""
    read -p "Welche Datei möchtest du bearbeiten? (Enter für Skip): " doc_file
fi

if [[ -n "$doc_file" ]] && [[ -f "$doc_file" ]]; then
    # Editor auswählen (nano als Fallback)
    if command -v nano > /dev/null 2>&1; then
        editor="nano"
    elif command -v vim > /dev/null 2>&1; then
        editor="vim"
    else
        editor="vi"
    fi
    
    echo -e "${BLUE}📝 Öffne $doc_file mit $editor...${NC}"
    $editor "$doc_file"
    
    # Änderungen prüfen
    if [[ -n $(git status -s "$doc_file") ]]; then
        # Commit-Nachricht
        if [[ -n "$2" ]]; then
            commit_msg="$2"
        else
            read -p "Commit-Nachricht: " commit_msg
            if [[ -z "$commit_msg" ]]; then
                commit_msg="docs: Update $doc_file"
            fi
        fi
        
        # Committen und pushen
        git add "$doc_file"
        git commit -m "docs: $commit_msg"
        echo -e "${GREEN}✅ Änderungen committed${NC}"
        
        echo -e "${BLUE}⬆️  Pushe auf GitHub...${NC}"
        git push origin "$current_branch"
        echo -e "${GREEN}✅ Dokumentation aktualisiert!${NC}"
    else
        echo -e "${YELLOW}⏭️  Keine Änderungen erkannt${NC}"
    fi
else
    if [[ -n "$doc_file" ]]; then
        echo -e "${YELLOW}⚠️  Datei '$doc_file' nicht gefunden${NC}"
    else
        echo -e "${YELLOW}⏭️  Übersprungen${NC}"
    fi
fi

echo -e "${GREEN}✅ Fertig!${NC}"
