#!/bin/bash
# PI-Installer: Setze WirePlumber-Audio-Konfiguration zurück
#
# Entfernt benutzerdefinierte WirePlumber-Konfigurationen, die das Audio-Routing
# beeinflussen könnten. Nützlich wenn Audio nach System-Updates oder Konfigurationsänderungen
# nicht mehr funktioniert.
#
# Ausführung: ./scripts/reset-wireplumber-audio-config.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Setze WirePlumber-Audio-Konfiguration zurück ===${NC}"
echo ""

# Prüfe ob WirePlumber läuft
if ! systemctl --user is-active --quiet wireplumber.service 2>/dev/null; then
  echo -e "${YELLOW}⚠${NC} WirePlumber läuft nicht als Systemd-Service"
  echo "  Starte WirePlumber manuell neu oder starte das System neu"
fi

echo -e "${CYAN}[1] Prüfe vorhandene WirePlumber-Konfigurationen:${NC}"
WIREPLUMBER_CONF_DIR="$HOME/.config/wireplumber/wireplumber.conf.d"
if [ -d "$WIREPLUMBER_CONF_DIR" ]; then
  CONFIG_FILES=$(find "$WIREPLUMBER_CONF_DIR" -name "*.conf" -type f 2>/dev/null || echo "")
  if [ -n "$CONFIG_FILES" ]; then
    echo "  Gefundene Konfigurationsdateien:"
    echo "$CONFIG_FILES" | while read -r file; do
      echo "    - $file"
      if echo "$file" | grep -q "50-alsa-hdmi-a1"; then
        echo "      → Diese Datei könnte Card 0 (HDMI-A-1) erzwingen"
      fi
    done
  else
    echo "  Keine Konfigurationsdateien gefunden"
  fi
else
  echo "  Konfigurationsverzeichnis existiert nicht"
fi
echo ""

echo -e "${CYAN}[2] Prüfe persistente State-Dateien:${NC}"
STATE_DIRS=(
  "$HOME/.local/share/wireplumber"
  "$HOME/.config/wireplumber"
  "$HOME/.local/share/pipewire"
  "$HOME/.config/pipewire"
)

FOUND_STATE=false
for dir in "${STATE_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    STATE_FILES=$(find "$dir" -name "*state*" -o -name "*default*" -o -name "*persist*" 2>/dev/null | head -10 || echo "")
    if [ -n "$STATE_FILES" ]; then
      echo "  Gefundene State-Dateien in $dir:"
      echo "$STATE_FILES" | while read -r file; do
        echo "    - $file"
        FOUND_STATE=true
      done
    fi
  fi
done

if [ "$FOUND_STATE" = false ]; then
  echo "  Keine State-Dateien gefunden"
fi
echo ""

echo -e "${CYAN}[3] Optionen:${NC}"
echo ""
echo "1. Benutzerdefinierte WirePlumber-Konfigurationen entfernen"
echo "2. WirePlumber State-Dateien löschen (persistente Einstellungen)"
echo "3. WirePlumber komplett zurücksetzen (Konfiguration + State)"
echo "4. Abbrechen"
echo ""
read -p "Wähle Option [1-4]: " option

case $option in
  1)
    echo ""
    echo -e "${CYAN}[Option 1] Entferne benutzerdefinierte Konfigurationen:${NC}"
    if [ -d "$WIREPLUMBER_CONF_DIR" ]; then
      BACKUP_DIR="$HOME/.config/wireplumber/wireplumber.conf.d.backup.$(date +%Y%m%d_%H%M%S)"
      mkdir -p "$BACKUP_DIR"
      echo "  Erstelle Backup in: $BACKUP_DIR"
      
      if [ -n "$CONFIG_FILES" ]; then
        echo "$CONFIG_FILES" | while read -r file; do
          if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/" 2>/dev/null || true
            rm -f "$file"
            echo "    ✓ Entfernt: $file"
          fi
        done
      fi
      echo ""
      echo "  Konfigurationsdateien wurden entfernt und gesichert."
    else
      echo "  Keine Konfigurationsdateien gefunden"
    fi
    ;;
  2)
    echo ""
    echo -e "${CYAN}[Option 2] Lösche WirePlumber State-Dateien:${NC}"
    BACKUP_DIR="$HOME/.wireplumber-state-backup.$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    for dir in "${STATE_DIRS[@]}"; do
      if [ -d "$dir" ]; then
        STATE_FILES=$(find "$dir" -name "*state*" -o -name "*default*" -o -name "*persist*" 2>/dev/null || echo "")
        if [ -n "$STATE_FILES" ]; then
          echo "$STATE_FILES" | while read -r file; do
            if [ -f "$file" ]; then
              cp "$file" "$BACKUP_DIR/" 2>/dev/null || true
              rm -f "$file"
              echo "    ✓ Entfernt: $file"
            fi
          done
        fi
      fi
    done
    echo ""
    echo "  State-Dateien wurden entfernt und gesichert in: $BACKUP_DIR"
    ;;
  3)
    echo ""
    echo -e "${CYAN}[Option 3] Setze WirePlumber komplett zurück:${NC}"
    BACKUP_DIR="$HOME/.wireplumber-full-backup.$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup Konfiguration
    if [ -d "$WIREPLUMBER_CONF_DIR" ]; then
      cp -r "$WIREPLUMBER_CONF_DIR" "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    # Backup State
    for dir in "${STATE_DIRS[@]}"; do
      if [ -d "$dir" ]; then
        STATE_FILES=$(find "$dir" -name "*state*" -o -name "*default*" -o -name "*persist*" 2>/dev/null || echo "")
        if [ -n "$STATE_FILES" ]; then
          mkdir -p "$BACKUP_DIR/$(basename $dir)"
          echo "$STATE_FILES" | while read -r file; do
            if [ -f "$file" ]; then
              cp "$file" "$BACKUP_DIR/$(basename $dir)/" 2>/dev/null || true
            fi
          done
        fi
      fi
    done
    
    # Entferne Konfiguration
    if [ -n "$CONFIG_FILES" ]; then
      echo "$CONFIG_FILES" | while read -r file; do
        if [ -f "$file" ]; then
          rm -f "$file"
          echo "    ✓ Entfernt: $file"
        fi
      done
    fi
    
    # Entferne State
    for dir in "${STATE_DIRS[@]}"; do
      if [ -d "$dir" ]; then
        STATE_FILES=$(find "$dir" -name "*state*" -o -name "*default*" -o -name "*persist*" 2>/dev/null || echo "")
        if [ -n "$STATE_FILES" ]; then
          echo "$STATE_FILES" | while read -r file; do
            if [ -f "$file" ]; then
              rm -f "$file"
              echo "    ✓ Entfernt: $file"
            fi
          done
        fi
      fi
    done
    
    echo ""
    echo "  WirePlumber wurde komplett zurückgesetzt."
    echo "  Backup gespeichert in: $BACKUP_DIR"
    ;;
  4)
    echo "Abgebrochen."
    exit 0
    ;;
  *)
    echo -e "${RED}✗${NC} Ungültige Option"
    exit 1
    ;;
esac

echo ""
echo -e "${CYAN}[4] Starte WirePlumber neu:${NC}"
if systemctl --user restart wireplumber.service 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} WirePlumber neu gestartet"
  sleep 2
else
  echo -e "  ${YELLOW}⚠${NC} Konnte WirePlumber nicht neu starten"
  echo "  Starte manuell: systemctl --user restart wireplumber.service"
fi

echo ""
echo -e "${CYAN}[5] Prüfe Audio-Sinks nach Reset:${NC}"
sleep 1
SINKS=$(pactl list short sinks 2>/dev/null || echo "")
if [ -n "$SINKS" ]; then
  echo "  Verfügbare Sinks:"
  echo "$SINKS" | while read -r line; do
    echo "    $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} Keine Sinks gefunden"
fi

echo ""
echo -e "${CYAN}[6] Nächste Schritte:${NC}"
echo ""
echo "1. Teste Audio:"
echo "   ./scripts/test-both-hdmi-sinks.sh"
echo ""
echo "2. Falls Audio immer noch nicht funktioniert:"
echo "   - Prüfe Hardware-Verbindungen"
echo "   - Teste ohne Monitor: ./scripts/test-audio-without-monitor.sh"
echo "   - Siehe: docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md"
echo ""
echo "3. Falls das Problem behoben ist:"
echo "   - Backup-Dateien können gelöscht werden: rm -rf $BACKUP_DIR"
echo ""
echo -e "${GREEN}Fertig.${NC}"
