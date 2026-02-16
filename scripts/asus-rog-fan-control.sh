#!/bin/bash
# ASUS ROG Lüftersteuerung - Setzt Lüfter-Profil oder benutzerdefinierte Kurve
#
# Aufruf:
#   bash scripts/asus-rog-fan-control.sh Performance    # Performance-Profil aktivieren
#   bash scripts/asus-rog-fan-control.sh Balanced       # Balanced-Profil aktivieren
#   bash scripts/asus-rog-fan-control.sh Quiet          # Quiet-Profil aktivieren
#   bash scripts/asus-rog-fan-control.sh status        # Status anzeigen

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Farben für Ausgabe
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info() { echo -e "${CYAN}[INFO]${NC} $1"; }
ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }

# Prüfe ob asusctl installiert ist
if ! command -v asusctl >/dev/null 2>&1; then
  err "asusctl ist nicht installiert!"
  echo ""
  info "Bitte zuerst installieren:"
  echo "  sudo bash scripts/install-asusctl.sh"
  exit 1
fi

# Prüfe ob asusd läuft
if ! systemctl is-active --quiet asusd.service 2>/dev/null; then
  warn "asusd Service läuft nicht. Versuche zu starten..."
  sudo systemctl start asusd.service || {
    err "asusd Service konnte nicht gestartet werden"
    exit 1
  }
fi

# Funktion: Status anzeigen
show_status() {
  echo -e "${CYAN}============================================${NC}"
  echo -e "${CYAN}  ASUS ROG Lüfter-Status${NC}"
  echo -e "${CYAN}============================================${NC}"
  echo ""
  
  info "Verfügbare Profile:"
  asusctl profile list || warn "Profile konnten nicht abgerufen werden"
  
  echo ""
  info "Aktuelles Profil:"
  asusctl profile get || warn "Aktuelles Profil konnte nicht abgerufen werden"
  
  echo ""
  info "Aktuelle Lüfter-Kurven-Status:"
  asusctl fan-curve --get-enabled || warn "Lüfter-Kurven konnten nicht abgerufen werden"
  
  echo ""
  info "System-Informationen:"
  asusctl info || warn "System-Informationen konnten nicht abgerufen werden"
}

# Funktion: Profil aktivieren
activate_profile() {
  local profile=$1
  
  case "$profile" in
    Performance|performance|perf|p)
      profile="Performance"
      ;;
    Balanced|balanced|bal|b)
      profile="Balanced"
      ;;
    Quiet|quiet|q)
      profile="Quiet"
      ;;
    *)
      err "Unbekanntes Profil: $profile"
      echo ""
      info "Verfügbare Profile:"
      asusctl profile list || true
      exit 1
      ;;
  esac
  
  info "Setze $profile-Profil..."
  
  # Setze Profil
  if sudo asusctl profile set "$profile"; then
    ok "$profile-Profil gesetzt"
  else
    err "Profil konnte nicht gesetzt werden"
    exit 1
  fi
  
  # Aktiviere Lüfter-Kurven für das Profil
  info "Aktiviere Lüfter-Kurven für $profile..."
  if sudo asusctl fan-curve --mod-profile "$profile" --enable-fan-curves true; then
    ok "Lüfter-Kurven für $profile aktiviert"
  else
    warn "Lüfter-Kurven konnten nicht aktiviert werden (möglicherweise bereits aktiv oder nicht unterstützt)"
  fi
  
  # Zeige aktuelle Kurve
  echo ""
  info "Aktuelle Lüfter-Kurven für $profile:"
  asusctl fan-curve --mod-profile "$profile" || warn "Kurven konnten nicht abgerufen werden"
  
  echo ""
  info "Aktuelles Profil:"
  asusctl profile get || warn "Aktuelles Profil konnte nicht abgerufen werden"
}

# Hauptlogik
if [ $# -eq 0 ]; then
  show_status
elif [ "$1" = "status" ] || [ "$1" = "--status" ] || [ "$1" = "-s" ]; then
  show_status
else
  activate_profile "$1"
fi
