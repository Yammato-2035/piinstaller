#!/bin/bash
# Installiert asusctl und asusd für ASUS ROG Lüftersteuerung unter Linux
#
# Aufruf: sudo bash scripts/install-asusctl.sh

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

# Prüfe ob als root/sudo ausgeführt
if [ "$EUID" -ne 0 ]; then 
  err "Bitte mit sudo ausführen: sudo bash $0"
  exit 1
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  ASUS ROG Lüftersteuerung (asusctl)${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Prüfe ob ASUS ROG System
info "Prüfe ob ASUS ROG System erkannt..."
if [ -f /sys/class/dmi/id/product_name ]; then
  PRODUCT_NAME=$(cat /sys/class/dmi/id/product_name)
  echo "  Produkt: $PRODUCT_NAME"
  if ! echo "$PRODUCT_NAME" | grep -qiE "(ROG|ASUS|Republic of Gamers)"; then
    warn "Kein ASUS ROG System erkannt. Installation wird trotzdem fortgesetzt."
  else
    ok "ASUS ROG System erkannt"
  fi
else
  warn "Kann Produktname nicht ermitteln. Installation wird fortgesetzt."
fi

# Prüfe Distribution
info "Prüfe Linux-Distribution..."
if command -v apt-get >/dev/null 2>&1; then
  DISTRO="debian"
  ok "Debian/Ubuntu-basierte Distribution erkannt"
elif command -v dnf >/dev/null 2>&1; then
  DISTRO="fedora"
  ok "Fedora/RHEL-basierte Distribution erkannt"
elif command -v pacman >/dev/null 2>&1; then
  DISTRO="arch"
  ok "Arch-basierte Distribution erkannt"
else
  err "Nicht unterstützte Distribution. Bitte manuell installieren."
  exit 1
fi

# Installiere asusctl je nach Distribution
INSTALL_SUCCESS=false

if [ "$DISTRO" = "debian" ]; then
  # Debian/Ubuntu: Versuche zuerst Repository-Installation
  info "Versuche Installation über Repository..."
  
  # Prüfe ob Repository bereits vorhanden
  REPO_EXISTS=false
  if [ -f /etc/apt/sources.list.d/asus-linux.list ]; then
    if grep -q "repo.asus-linux.org" /etc/apt/sources.list.d/asus-linux.list 2>/dev/null; then
      REPO_EXISTS=true
    fi
  fi
  
  if [ "$REPO_EXISTS" = false ]; then
    info "Prüfe Repository-Verfügbarkeit..."
    if curl -fsSL --connect-timeout 5 https://repo.asus-linux.org/asus-linux.gpg >/dev/null 2>&1; then
      info "Füge asus-linux Repository hinzu..."
      if curl -fsSL https://repo.asus-linux.org/asus-linux.gpg 2>/dev/null | gpg --dearmor 2>/dev/null | tee /usr/share/keyrings/asus-linux.gpg > /dev/null 2>&1; then
        echo "deb [signed-by=/usr/share/keyrings/asus-linux.gpg] https://repo.asus-linux.org/debian/ stable main" | tee /etc/apt/sources.list.d/asus-linux.list > /dev/null
        ok "Repository hinzugefügt"
      else
        warn "Repository-Schlüssel konnte nicht heruntergeladen werden"
      fi
    else
      warn "Repository ist nicht erreichbar (DNS/Netzwerk-Problem)"
      warn "Überspringe Repository-Installation, verwende Quellcode-Kompilierung"
    fi
  else
    ok "Repository bereits vorhanden"
  fi
  
  # Versuche Repository-Update (ignoriere Fehler)
  UPDATE_OUTPUT=$(apt-get update -qq 2>&1 || true)
  if echo "$UPDATE_OUTPUT" | grep -qiE "repo.asus-linux.org.*(konnte nicht aufgelöst|could not be resolved|could not resolve)"; then
    warn "Repository-Update fehlgeschlagen (Repository nicht erreichbar)"
  fi
  
  # Versuche Installation über Repository
  if apt-get install -y asusctl supergfxctl 2>/dev/null; then
    INSTALL_SUCCESS=true
    ok "asusctl und supergfxctl über Repository installiert"
  else
    warn "Repository-Installation fehlgeschlagen. Versuche Kompilierung aus Quellcode..."
  fi
  
elif [ "$DISTRO" = "fedora" ]; then
  # Fedora/RHEL
  if dnf install -y asusctl supergfxctl 2>/dev/null; then
    INSTALL_SUCCESS=true
    ok "asusctl und supergfxctl installiert"
  else
    warn "Paket-Installation fehlgeschlagen. Versuche Kompilierung aus Quellcode..."
  fi
  
elif [ "$DISTRO" = "arch" ]; then
  # Arch Linux: AUR (benötigt yay oder ähnliches)
  if command -v yay >/dev/null 2>&1; then
    if yay -S --noconfirm asusctl supergfxctl 2>/dev/null; then
      INSTALL_SUCCESS=true
      ok "asusctl und supergfxctl installiert"
    else
      warn "AUR-Installation fehlgeschlagen. Versuche Kompilierung aus Quellcode..."
    fi
  else
    warn "yay nicht gefunden. Versuche Kompilierung aus Quellcode..."
  fi
fi

# Falls Repository-Installation fehlgeschlagen, kompiliere aus Quellcode
if [ "$INSTALL_SUCCESS" = false ]; then
  info "Kompiliere asusctl aus Quellcode..."
  
  # Installiere Build-Abhängigkeiten
  if [ "$DISTRO" = "debian" ]; then
    info "Installiere Build-Abhängigkeiten..."
    apt-get update -qq
    apt-get install -y \
      build-essential \
      curl \
      git \
      libgtk-3-dev \
      libpango1.0-dev \
      libgdk-pixbuf-2.0-dev \
      libglib2.0-dev \
      cmake \
      libclang-dev \
      libudev-dev \
      libayatana-appindicator3-dev \
      pkg-config \
      >/dev/null 2>&1 || warn "Einige Abhängigkeiten konnten nicht installiert werden"
    
    # Installiere Rust falls nicht vorhanden
    if ! command -v rustc >/dev/null 2>&1; then
      info "Installiere Rust..."
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y >/dev/null 2>&1
      export PATH="$HOME/.cargo/bin:$PATH"
      source "$HOME/.cargo/env" 2>/dev/null || true
    fi
    
  elif [ "$DISTRO" = "fedora" ]; then
    info "Installiere Build-Abhängigkeiten..."
    dnf install -y \
      cmake \
      clang-devel \
      systemd-devel \
      glib2-devel \
      cairo-devel \
      atkmm-devel \
      pangomm-devel \
      gdk-pixbuf2-devel \
      gtk3-devel \
      libappindicator-gtk3 \
      rust \
      cargo \
      >/dev/null 2>&1 || warn "Einige Abhängigkeiten konnten nicht installiert werden"
  fi
  
  # Prüfe ob Rust verfügbar ist
  if ! command -v rustc >/dev/null 2>&1 && ! command -v cargo >/dev/null 2>&1; then
    err "Rust ist nicht verfügbar. Bitte manuell installieren:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
  fi
  
  # Stelle sicher, dass Rust im PATH ist
  if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  fi
  
  # Erstelle temporäres Verzeichnis für Build
  BUILD_DIR=$(mktemp -d)
  trap "rm -rf $BUILD_DIR" EXIT
  
  # Klone und kompiliere asusctl
  info "Klone asusctl Repository..."
  if git clone --depth 1 https://gitlab.com/asus-linux/asusctl.git "$BUILD_DIR/asusctl" 2>/dev/null; then
    ok "Repository geklont"
    
    cd "$BUILD_DIR/asusctl"
    
    info "Kompiliere asusctl (dies kann einige Minuten dauern)..."
    if make 2>&1 | tail -20; then
      ok "Kompilierung erfolgreich"
      
      info "Installiere asusctl..."
      if make install 2>&1; then
        INSTALL_SUCCESS=true
        ok "asusctl installiert"
      else
        err "Installation fehlgeschlagen"
      fi
    else
      err "Kompilierung fehlgeschlagen"
    fi
  else
    err "Repository konnte nicht geklont werden"
  fi
  
  # Versuche supergfxctl zu installieren (optional)
  if [ "$INSTALL_SUCCESS" = true ]; then
    info "Versuche supergfxctl zu installieren..."
    if git clone --depth 1 https://gitlab.com/asus-linux/supergfxctl.git "$BUILD_DIR/supergfxctl" 2>/dev/null; then
      cd "$BUILD_DIR/supergfxctl"
      if make && make install 2>/dev/null; then
        ok "supergfxctl installiert"
      else
        warn "supergfxctl konnte nicht installiert werden (optional)"
      fi
    fi
  fi
fi

# Prüfe ob Installation erfolgreich war
if [ "$INSTALL_SUCCESS" = false ]; then
  err "Installation fehlgeschlagen!"
  echo ""
  warn "Alternative Installationsmethoden:"
  echo "  1. Manuelle Installation: https://asus-linux.org/guides/asusctl-install/"
  echo "  2. DistroBox verwenden für nicht unterstützte Distributionen"
  echo "  3. Repository-URL prüfen: https://repo.asus-linux.org/"
  exit 1
fi

ok "asusctl und supergfxctl installiert"

# Starte und aktiviere asusd Service
info "Starte asusd Service..."
systemctl enable --now asusd.service || {
  warn "asusd Service konnte nicht gestartet werden. Möglicherweise wird Ihre Hardware nicht unterstützt."
}

# Prüfe ob Service läuft
sleep 2
if systemctl is-active --quiet asusd.service; then
  ok "asusd Service läuft"
else
  warn "asusd Service läuft nicht. Prüfe mit: systemctl status asusd"
fi

# Prüfe ob asusctl funktioniert
info "Prüfe asusctl Installation..."
if command -v asusctl >/dev/null 2>&1; then
  ok "asusctl ist verfügbar"
  
  # Zeige verfügbare Profile
  echo ""
  info "Verfügbare Profile:"
  asusctl profile list || warn "Profile konnten nicht abgerufen werden"
  
  echo ""
  info "Aktuelle Lüfter-Kurven-Status:"
  asusctl fan-curve --get-enabled || warn "Lüfter-Kurven-Status konnte nicht abgerufen werden"
  
else
  err "asusctl wurde nicht korrekt installiert"
  exit 1
fi

echo ""
ok "Installation abgeschlossen!"
echo ""
info "Nützliche Befehle:"
echo "  asusctl profile list                                    # Zeige verfügbare Profile"
echo "  asusctl profile set Performance                         # Setze Performance-Profil"
echo "  asusctl profile set Balanced                            # Setze Balanced-Profil"
echo "  asusctl profile set Quiet                               # Setze Quiet-Profil"
echo "  asusctl fan-curve --get-enabled                        # Zeige aktuelle Lüfter-Kurven"
echo "  asusctl fan-curve --mod-profile Performance            # Zeige Performance Lüfter-Kurven"
echo "  asusctl fan-curve --mod-profile Performance --enable-fan-curves true  # Aktiviere Performance Lüfter-Kurven"
echo ""
info "Für detaillierte Hilfe: asusctl --help"
