#!/bin/bash
# Release-Service: Automatisiert Version-Bump, Build, Packaging, Commit, Push und Update
# 
# Dieses Script:
# 1. Erhöht die Patch-Version (W in X.Y.Z.W)
# 2. Aktualisiert Dokumentation und Changelog
# 3. Baut die Tauri-App
# 4. Erstellt das DEB-Paket
# 5. Committet und pusht nach GitHub
# 6. Updated die lokale Installation
# 7. Behebt Fehler automatisch und wiederholt bei Bedarf
#
# Aufruf: bash scripts/release-service.sh [--skip-update] [--feature-bump]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Konfiguration
LOG_FILE="$REPO_ROOT/logs/release-service.log"
MAX_RETRIES=3
SKIP_UPDATE=false
FEATURE_BUMP=false

# Parse Argumente
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-update)
      SKIP_UPDATE=true
      shift
      ;;
    --feature-bump)
      FEATURE_BUMP=true
      shift
      ;;
    *)
      echo "Unbekanntes Argument: $1"
      exit 1
      ;;
  esac
done

# Farben
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging-Funktionen (schreiben nach stderr UND Log-Datei, aber NIE nach stdout)
log() {
  local msg="${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
  echo -e "$msg" >> "$LOG_FILE"
  echo -e "$msg" >&2
}

log_success() {
  local msg="${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
  echo -e "$msg" >> "$LOG_FILE"
  echo -e "$msg" >&2
}

log_warn() {
  local msg="${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
  echo -e "$msg" >> "$LOG_FILE"
  echo -e "$msg" >&2
}

log_error() {
  local msg="${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
  echo -e "$msg" >> "$LOG_FILE"
  echo -e "$msg" >&2
}

# Fehlerbehandlung
handle_error() {
  local step="$1"
  local error_msg="$2"
  log_error "Fehler in Schritt '$step': $error_msg"
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR [$step]: $error_msg" >> "$LOG_FILE"
  
  # Versuche Fehler automatisch zu beheben
  fix_error "$step" "$error_msg"
}

# Automatische Fehlerbehebung mit Log-Analyse
fix_error() {
  local step="$1"
  local error_msg="$2"
  
  log "Analysiere Fehler und versuche automatische Behebung..."
  log "Fehler-Details: $error_msg"
  
  # Schreibe Fehler ins Log für spätere Analyse
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR [$step]: $error_msg" >> "$LOG_FILE"
  
  case "$step" in
    "version_bump")
      log "Version-Bump-Fehler: Prüfe VERSION-Datei..."
      if [ ! -f "$REPO_ROOT/VERSION" ]; then
        local last_version=$(git log -1 --pretty=format:"%s" | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1 || echo "1.3.4.5")
        echo "$last_version" > "$REPO_ROOT/VERSION"
        log_success "VERSION-Datei neu erstellt mit: $last_version"
      fi
      # Prüfe Versionsformat
      local version=$(cat "$REPO_ROOT/VERSION" | tr -d '\n')
      if ! echo "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
        log "Korrigiere Versionsformat..."
        echo "1.3.4.5" > "$REPO_ROOT/VERSION"
        log_success "Versionsformat korrigiert"
      fi
      ;;
    "git_status")
      log "Git-Status-Fehler: Prüfe Git-Repository..."
      if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Kein Git-Repository gefunden"
        return 1
      fi
      # Prüfe ob wir auf main branch sind
      local current_branch=$(git rev-parse --abbrev-ref HEAD)
      if [ "$current_branch" != "main" ]; then
        log "Wechsle zu main branch..."
        git checkout main || git checkout -b main || {
          log_error "Konnte nicht zu main wechseln"
          return 1
        }
      fi
      # Hole neueste Änderungen
      git fetch origin main || log_warn "Konnte nicht fetchen, fahre fort..."
      git pull origin main || log_warn "Konnte nicht pullen, fahre fort..."
      ;;
    "tauri_build")
      log "Tauri-Build-Fehler: Analysiere Fehlerursache..."
      
      # Prüfe ob Fehler mit Rust/Cargo zusammenhängt
      if echo "$error_msg" | grep -qiE "(cargo|rust|rustc)"; then
        log "Rust/Cargo-Problem erkannt..."
        if ! command -v cargo >/dev/null 2>&1; then
          log_error "Cargo nicht gefunden. Bitte Rust installieren: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
          return 1
        fi
        # Prüfe Rust-Version
        local rust_version=$(rustc --version 2>/dev/null || echo "")
        if [ -z "$rust_version" ]; then
          log_error "Rust nicht richtig installiert"
          return 1
        fi
      fi
      
      # Prüfe ob Fehler mit npm/node zusammenhängt
      if echo "$error_msg" | grep -qiE "(npm|node)"; then
        log "npm/node-Problem erkannt..."
        cd "$REPO_ROOT/frontend"
        if [ ! -d "node_modules" ]; then
          log "Installiere npm-Abhängigkeiten..."
          npm install || {
            log_error "npm install fehlgeschlagen"
            cd "$REPO_ROOT"
            return 1
          }
        fi
        cd "$REPO_ROOT"
      fi
      
      # Bereinige Build-Cache
      log "Bereinige Build-Cache..."
      cd "$REPO_ROOT/frontend"
      rm -rf src-tauri/target/debug src-tauri/target/release 2>/dev/null || true
      npm run clean 2>/dev/null || true
      cd "$REPO_ROOT"
      
      # Prüfe ob Tauri-Konfiguration korrekt ist
      if [ -f "$REPO_ROOT/frontend/src-tauri/tauri.conf.json" ]; then
        if ! python3 -m json.tool "$REPO_ROOT/frontend/src-tauri/tauri.conf.json" > /dev/null 2>&1; then
          log_warn "Tauri-Konfiguration möglicherweise ungültig"
        fi
      fi
      ;;
    "deb_build")
      log "DEB-Build-Fehler: Analysiere Fehlerursache..."
      
      # Prüfe Build-Abhängigkeiten
      if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
        log "Installiere debhelper..."
        sudo apt-get update -qq && sudo apt-get install -y debhelper rsync || {
          log_error "Konnte debhelper nicht installieren"
          return 1
        }
      fi
      
      # Prüfe ob debian/control existiert
      if [ ! -f "$REPO_ROOT/debian/control" ]; then
        log_error "debian/control nicht gefunden"
        return 1
      fi
      
      # Bereinige alte Build-Artefakte
      log "Bereinige alte Build-Artefakte..."
      rm -rf debian/pi-installer debian/*.debhelper debian/files ../pi-installer_*.deb ../pi-installer_*.changes ../pi-installer_*.buildinfo 2>/dev/null || true
      
      # Prüfe ob VERSION und changelog synchron sind
      local version=$(cat "$REPO_ROOT/VERSION" | tr -d '\n')
      local changelog_version=$(head -1 "$REPO_ROOT/debian/changelog" | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1 || echo "")
      if [ -n "$changelog_version" ] && [ "$changelog_version" != "$version" ]; then
        log "Synchronisiere changelog mit VERSION..."
        # Changelog wird in update_documentation aktualisiert
      fi
      ;;
    "git_commit")
      log "Git-Commit-Fehler: Analysiere Fehlerursache..."
      
      # Prüfe ob es Änderungen gibt
      if [ -z "$(git status --porcelain)" ]; then
        log_warn "Keine Änderungen zum Committen"
        return 0
      fi
      
      # Prüfe ob Git konfiguriert ist
      if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
        log_warn "Git-Benutzer nicht konfiguriert, verwende Standard..."
        git config user.name "PI-Installer Release Service" || true
        git config user.email "release@pi-installer.local" || true
      fi
      ;;
    "git_push")
      log "Git-Push-Fehler: Analysiere Fehlerursache..."
      
      # Prüfe Remote-Verbindung
      if ! git remote get-url origin > /dev/null 2>&1; then
        log_error "Kein origin remote konfiguriert"
        return 1
      fi
      
      # Prüfe ob wir vor origin/main sind
      git fetch origin main || {
        log_error "Konnte nicht von origin/main fetchen"
        return 1
      }
      
      # Prüfe ob lokale Commits vorhanden sind
      local ahead_count=$(git rev-list --count HEAD ^origin/main 2>/dev/null || echo 0)
      if [ "$ahead_count" -eq 0 ]; then
        log_warn "Keine neuen Commits zum Pushen"
        return 0
      fi
      
      # Prüfe ob es Konflikte gibt
      if git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
        log "Lokale Commits sind vor origin/main, Push sollte funktionieren"
      else
        log_warn "Mögliche Divergenz mit origin/main erkannt"
      fi
      ;;
    "local_update")
      log "Update-Fehler: Analysiere Fehlerursache..."
      
      local deb_file=$(ls -t ../pi-installer_*_all.deb 2>/dev/null | head -1)
      if [ -z "$deb_file" ]; then
        log_error "Kein DEB-Paket gefunden"
        return 1
      fi
      
      # Prüfe ob Paket gültig ist
      if ! dpkg-deb -I "$deb_file" > /dev/null 2>&1; then
        log_error "DEB-Paket ist ungültig oder beschädigt"
        return 1
      fi
      
      # Prüfe ob sudo verfügbar ist
      if ! sudo -n true 2>/dev/null; then
        log_warn "Sudo-Passwort erforderlich für Update"
      fi
      ;;
  esac
  
  log "Fehlerbehebung abgeschlossen"
}

# Schritt 1: Version erhöhen
bump_version() {
  log "Schritt 1: Version erhöhen..." >&2
  
  if [ ! -f "$REPO_ROOT/VERSION" ]; then
    handle_error "version_bump" "VERSION-Datei nicht gefunden" >&2
    return 1
  fi
  
  local current_version=$(cat "$REPO_ROOT/VERSION" | tr -d '\n')
  log "Aktuelle Version: $current_version" >&2
  
  local parts=($(echo "$current_version" | tr '.' ' '))
  if [ ${#parts[@]} -ne 4 ]; then
    handle_error "version_bump" "Ungültiges Versionsformat: $current_version" >&2
    return 1
  fi
  
  if [ "$FEATURE_BUMP" = true ]; then
    # Feature-Bump: Z erhöhen, W auf 0 setzen
    parts[2]=$((${parts[2]} + 1))
    parts[3]=0
  else
    # Patch-Bump: W erhöhen
    parts[3]=$((${parts[3]} + 1))
  fi
  
  local new_version="${parts[0]}.${parts[1]}.${parts[2]}.${parts[3]}"
  echo "$new_version" > "$REPO_ROOT/VERSION"
  log_success "Version erhöht: $current_version -> $new_version" >&2
  
  # Tauri-Version (nur X.Y.Z)
  local tauri_version="${parts[0]}.${parts[1]}.${parts[2]}"
  
  # Aktualisiere Tauri-Konfigurationen
  if [ -f "$REPO_ROOT/frontend/src-tauri/tauri.conf.json" ]; then
    sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$tauri_version\"/" "$REPO_ROOT/frontend/src-tauri/tauri.conf.json" 2>/dev/null
    log_success "Tauri-Version aktualisiert: $tauri_version" >&2
  fi
  
  if [ -f "$REPO_ROOT/frontend/src-tauri/Cargo.toml" ]; then
    sed -i "s/^version = \"[^\"]*\"/version = \"$tauri_version\"/" "$REPO_ROOT/frontend/src-tauri/Cargo.toml" 2>/dev/null
    log_success "Cargo.toml-Version aktualisiert: $tauri_version" >&2
  fi
  
  # Synchronisiere Frontend-Version
  if [ -f "$REPO_ROOT/frontend/sync-version.js" ]; then
    cd "$REPO_ROOT/frontend"
    node sync-version.js >/dev/null 2>&1 || {
      log_warn "sync-version.js fehlgeschlagen, fahre fort..." >&2
    }
    cd "$REPO_ROOT"
  fi
  
  # Gib Version NUR nach stdout aus (alle Logs gehen nach stderr)
  echo "$new_version"
}

# Schritt 2: Dokumentation aktualisieren
update_documentation() {
  log "Schritt 2: Dokumentation aktualisieren..."
  
  local new_version="$1"
  local date_str=$(date '+%Y-%m-%d')
  local time_str=$(date '+%H:%M:%S')
  # Datum im RFC 2822 Format für debian/changelog (z.B. "Mon, 16 Feb 2026 16:55:04 +0100")
  local date_full=$(LC_TIME=en_US.UTF-8 date '+%a, %d %b %Y %H:%M:%S %z')
  
  # Aktualisiere debian/changelog (ohne Log-Ausgaben zu stören)
  if [ -f "$REPO_ROOT/debian/changelog" ]; then
    # Hole IMMER saubere Version aus Git (vor jedem Update)
    # Verwende einen temporären Dateinamen außerhalb des Repos, um sicherzustellen, dass keine Log-Ausgaben hineingeschrieben werden
    local temp_changelog=$(mktemp /tmp/changelog_XXXXXX)
    local changelog_source=""
    
    # Versuche IMMER zuerst saubere Version aus Git zu holen
    if git rev-parse --git-dir > /dev/null 2>&1; then
      # Hole aus Git-Index (staged) oder HEAD - IMMER, auch wenn working directory beschädigt ist
      if git show :debian/changelog 2>/dev/null | grep -q "^pi-installer"; then
        git show :debian/changelog > "$temp_changelog" 2>/dev/null
        changelog_source="git-index"
      elif git show HEAD:debian/changelog 2>/dev/null | grep -q "^pi-installer"; then
        git show HEAD:debian/changelog > "$temp_changelog" 2>/dev/null
        changelog_source="git-head"
      else
        # Fallback: Verwende eine minimale saubere Changelog-Struktur
        {
          echo "pi-installer (1.3.4.5-1) unstable; urgency=medium"
          echo ""
          echo "  * Initial"
          echo ""
          echo " -- PI-Installer Team <https://github.com/Yammato-2035/piinstaller>  Mon, 16 Feb 2026 14:00:00 +0100"
        } > "$temp_changelog"
        changelog_source="fallback"
      fi
    else
      # Kein Git - verwende minimale Struktur
      {
        echo "pi-installer (1.3.4.5-1) unstable; urgency=medium"
        echo ""
        echo "  * Initial"
        echo ""
        echo " -- PI-Installer Team <https://github.com/Yammato-2035/piinstaller>  Mon, 16 Feb 2026 14:00:00 +0100"
      } > "$temp_changelog"
      changelog_source="no-git"
    fi
    
    # Erstelle neuen Changelog-Eintrag direkt in Datei (ohne stdout/stderr zu verwenden)
    {
      printf "pi-installer (%s-1) unstable; urgency=medium\n\n" "$new_version"
      printf "  * Automatisches Release: Version %s\n" "$new_version"
      printf "  * Build-Datum: %s\n\n" "$(date '+%d.%m.%Y %H:%M:%S')"
      printf " -- PI-Installer Team <https://github.com/Yammato-2035/piinstaller>  %s\n\n" "$date_full"
      # Füge nur gültige Changelog-Zeilen hinzu (die mit pi-installer beginnen und gültig sind)
      grep -E '^pi-installer \([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' "$temp_changelog" | head -1
      # Füge dann alle Zeilen nach dem ersten pi-installer-Eintrag hinzu
      awk '/^pi-installer \([0-9]/ {found=1} found' "$temp_changelog" | tail -n +2
    } > "$REPO_ROOT/debian/changelog" 2>&1
    
    rm -f "$temp_changelog"
    log_success "debian/changelog aktualisiert (Quelle: $changelog_source)"
  fi
  
  # Aktualisiere CHANGELOG.md falls vorhanden
  if [ -f "$REPO_ROOT/CHANGELOG.md" ]; then
    local changelog_md_entry="## [$new_version] - $date_str

### Added
- Automatisches Release: Version $new_version

### Changed
- Build-Prozess optimiert

"
    # Füge am Anfang ein (nach dem Header, vor dem ersten ##)
    local temp_changelog_md=$(mktemp)
    if grep -q "^## \[" "$REPO_ROOT/CHANGELOG.md"; then
      # Füge vor dem ersten ## ein
      awk -v entry="$changelog_md_entry" '/^## \[/ && !done {print entry; done=1} 1' "$REPO_ROOT/CHANGELOG.md" > "$temp_changelog_md"
      mv "$temp_changelog_md" "$REPO_ROOT/CHANGELOG.md"
    else
      echo -e "$changelog_md_entry$(cat "$REPO_ROOT/CHANGELOG.md")" > "$REPO_ROOT/CHANGELOG.md"
    fi
    log_success "CHANGELOG.md aktualisiert"
  fi
  
  # Aktualisiere Documentation.tsx (Changelog-Bereich)
  if [ -f "$REPO_ROOT/frontend/src/pages/Documentation.tsx" ]; then
    # Suche nach "Aktuelle Version:" und aktualisiere (mit korrektem Escaping)
    local doc_file="$REPO_ROOT/frontend/src/pages/Documentation.tsx"
    sed -i "s/Aktuelle Version: [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/Aktuelle Version: $new_version/" "$doc_file" || {
      log_warn "Konnte Documentation.tsx nicht automatisch aktualisieren"
    }
    log_success "Documentation.tsx aktualisiert"
  fi
}

# Schritt 3: Tauri-App bauen
build_tauri() {
  log "Schritt 3: Tauri-App bauen..."
  
  cd "$REPO_ROOT/frontend"
  
  # Prüfe ob Rust/Cargo verfügbar ist
  if ! command -v cargo >/dev/null 2>&1; then
    handle_error "tauri_build" "Cargo nicht gefunden"
    return 1
  fi
  
  # Prüfe ob npm install nötig ist
  if [ ! -d "node_modules" ]; then
    log "Installiere npm-Abhängigkeiten..."
    npm install || {
      handle_error "tauri_build" "npm install fehlgeschlagen"
      return 1
    }
  fi
  
  # Baue Tauri-App
  log "Baue Tauri-App (Release)..."
  export PATH="$HOME/.cargo/bin:/usr/local/bin:$PATH"
  [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
  
  npm run tauri:build || {
    handle_error "tauri_build" "Tauri-Build fehlgeschlagen"
    return 1
  }
  
  if [ -f "src-tauri/target/release/pi-installer" ]; then
    log_success "Tauri-App erfolgreich gebaut"
  else
    log_warn "Tauri-Binary nicht gefunden, aber Build erfolgreich"
  fi
  
  cd "$REPO_ROOT"
}

# Schritt 4: DEB-Paket erstellen
build_deb() {
  log "Schritt 4: DEB-Paket erstellen..."
  
  # Prüfe Build-Abhängigkeiten
  if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
    log "Installiere debhelper..."
    sudo apt-get update -qq && sudo apt-get install -y debhelper rsync || {
      handle_error "deb_build" "Konnte debhelper nicht installieren"
      return 1
    }
  fi
  
  # Bereinige alte Build-Artefakte
  rm -rf debian/pi-installer debian/*.debhelper debian/files ../pi-installer_*.deb ../pi-installer_*.changes ../pi-installer_*.buildinfo 2>/dev/null || true
  
  # Baue DEB-Paket
  log "Baue DEB-Paket..."
  dpkg-buildpackage -us -uc -b -tc || {
    handle_error "deb_build" "DEB-Build fehlgeschlagen"
    return 1
  }
  
  local deb_file=$(ls -t ../pi-installer_*_all.deb 2>/dev/null | head -1)
  if [ -n "$deb_file" ]; then
    log_success "DEB-Paket erstellt: $deb_file"
  else
    handle_error "deb_build" "DEB-Paket nicht gefunden nach Build"
    return 1
  fi
}

# Schritt 5: Git Commit und Push
git_commit_and_push() {
  log "Schritt 5: Git Commit und Push..."
  
  # Prüfe Git-Status
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    handle_error "git_status" "Kein Git-Repository"
    return 1
  fi
  
  # Prüfe ob es Änderungen gibt
  if [ -z "$(git status --porcelain)" ]; then
    log_warn "Keine Änderungen zum Committen"
    return 0
  fi
  
  # Stash uncommitted changes falls nötig (außer den neuen Dateien)
  git add -A
  
  local new_version="$1"
  local commit_msg="chore: Release Version $new_version

- Version auf $new_version erhöht
- Tauri-App gebaut
- DEB-Paket erstellt
- Dokumentation aktualisiert
- Automatisches Release via release-service.sh"
  
  git commit -m "$commit_msg" || {
    handle_error "git_commit" "Git-Commit fehlgeschlagen"
    return 1
  }
  
  log_success "Git-Commit erstellt"
  
  # Push nach GitHub
  log "Pushe nach GitHub..."
  git push origin main || {
    handle_error "git_push" "Git-Push fehlgeschlagen"
    return 1
  }
  
  log_success "Nach GitHub gepusht"
}

# Schritt 6: Lokale Installation updaten
update_local_installation() {
  if [ "$SKIP_UPDATE" = true ]; then
    log "Update übersprungen (--skip-update)"
    return 0
  fi
  
  log "Schritt 6: Lokale Installation updaten..."
  
  local deb_file=$(ls -t ../pi-installer_*_all.deb 2>/dev/null | head -1)
  if [ -z "$deb_file" ]; then
    handle_error "local_update" "Kein DEB-Paket gefunden"
    return 1
  fi
  
  log "Installiere DEB-Paket: $deb_file"
  sudo cp "$deb_file" /tmp/pi-installer-update.deb
  sudo apt install --only-upgrade -y /tmp/pi-installer-update.deb || {
    handle_error "local_update" "Installation fehlgeschlagen"
    return 1
  }
  
  log_success "Lokale Installation aktualisiert"
  rm -f /tmp/pi-installer-update.deb
}

# Analysiere Log auf Fehler und behebe sie
analyze_and_fix_log_errors() {
  log "Analysiere Log-Datei auf Fehler..."
  
  if [ ! -f "$LOG_FILE" ]; then
    return 0
  fi
  
  # Suche nach bekannten Fehlermustern
  local errors_found=false
  
  # Prüfe auf Rust/Cargo-Fehler
  if grep -qiE "(cargo|rustc).*not found|failed to run.*cargo" "$LOG_FILE"; then
    log "Rust/Cargo-Fehler erkannt im Log..."
    if ! command -v cargo >/dev/null 2>&1; then
      log_error "Cargo muss installiert werden. Bitte manuell: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
      errors_found=true
    fi
  fi
  
  # Prüfe auf npm/node-Fehler
  if grep -qiE "npm.*not found|node.*not found" "$LOG_FILE"; then
    log "npm/node-Fehler erkannt im Log..."
    if ! command -v npm >/dev/null 2>&1; then
      log_error "npm muss installiert werden"
      errors_found=true
    fi
  fi
  
  # Prüfe auf Git-Fehler
  if grep -qiE "git.*failed|git.*error|permission denied.*git" "$LOG_FILE"; then
    log "Git-Fehler erkannt im Log..."
    # Prüfe Git-Konfiguration
    if [ -z "$(git config user.name)" ]; then
      git config user.name "PI-Installer Release Service" || true
    fi
    if [ -z "$(git config user.email)" ]; then
      git config user.email "release@pi-installer.local" || true
    fi
  fi
  
  # Prüfe auf DEB-Build-Fehler
  if grep -qiE "dpkg-buildpackage.*not found|debian.*not found" "$LOG_FILE"; then
    log "DEB-Build-Fehler erkannt im Log..."
    if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
      log "Installiere debhelper..."
      sudo apt-get update -qq && sudo apt-get install -y debhelper rsync || {
        log_error "Konnte debhelper nicht installieren"
        errors_found=true
      }
    fi
  fi
  
  if [ "$errors_found" = true ]; then
    return 1
  fi
  
  return 0
}

# Hauptfunktion mit Retry-Logik
main() {
  # Erstelle Log-Verzeichnis
  mkdir -p "$(dirname "$LOG_FILE")"
  
  log "=========================================="
  log "Release-Service gestartet"
  log "=========================================="
  
  local retry_count=0
  local success=false
  local last_error_step=""
  
  while [ $retry_count -lt $MAX_RETRIES ] && [ "$success" = false ]; do
    if [ $retry_count -gt 0 ]; then
      log "Wiederhole nach Fehlerbehebung (Versuch $((retry_count + 1))/$MAX_RETRIES)..."
      
      # Analysiere Log auf Fehler
      analyze_and_fix_log_errors || {
        log_warn "Einige Fehler konnten nicht automatisch behoben werden"
      }
      
      sleep 2
    fi
    
    # Führe alle Schritte aus mit Fehlerbehandlung
    local step_result=0
    
    # Schritt 1: Version erhöhen (nur stdout, stderr bleibt getrennt)
    if ! new_version=$(bump_version 2>/dev/null); then
      last_error_step="version_bump"
      handle_error "version_bump" "Version-Bump fehlgeschlagen"
      step_result=1
    fi
    
    # Schritt 2: Dokumentation aktualisieren
    if [ $step_result -eq 0 ] && ! update_documentation "$new_version" 2>&1; then
      last_error_step="documentation"
      handle_error "documentation" "Dokumentation konnte nicht aktualisiert werden"
      step_result=1
    fi
    
    # Schritt 3: Tauri-App bauen
    if [ $step_result -eq 0 ] && ! build_tauri 2>&1; then
      last_error_step="tauri_build"
      # Fehler wurde bereits in build_tauri behandelt
      step_result=1
    fi
    
    # Schritt 4: DEB-Paket erstellen
    if [ $step_result -eq 0 ] && ! build_deb 2>&1; then
      last_error_step="deb_build"
      # Fehler wurde bereits in build_deb behandelt
      step_result=1
    fi
    
    # Schritt 5: Git Commit und Push
    if [ $step_result -eq 0 ] && ! git_commit_and_push "$new_version" 2>&1; then
      last_error_step="git_push"
      # Fehler wurde bereits in git_commit_and_push behandelt
      step_result=1
    fi
    
    # Schritt 6: Lokale Installation updaten
    if [ $step_result -eq 0 ] && ! update_local_installation 2>&1; then
      last_error_step="local_update"
      handle_error "local_update" "Lokale Installation konnte nicht aktualisiert werden"
      step_result=1
    fi
    
    if [ $step_result -eq 0 ]; then
      success=true
      log_success "=========================================="
      log_success "Release-Service erfolgreich abgeschlossen!"
      log_success "Neue Version: $new_version"
      log_success "DEB-Paket: $(ls -t ../pi-installer_*_all.deb 2>/dev/null | head -1 || echo 'nicht gefunden')"
      log_success "=========================================="
    else
      retry_count=$((retry_count + 1))
      log_warn "Fehler in Schritt: $last_error_step"
      
      if [ $retry_count -ge $MAX_RETRIES ]; then
        log_error "=========================================="
        log_error "Release-Service fehlgeschlagen nach $MAX_RETRIES Versuchen"
        log_error "Letzter Fehler in Schritt: $last_error_step"
        log_error "Bitte Log-Datei prüfen: $LOG_FILE"
        log_error "=========================================="
        
        # Zeige letzten Fehler aus Log
        log "Letzte Fehler aus Log:"
        tail -20 "$LOG_FILE" | grep -i "error\|failed\|✗" || true
        
        exit 1
      fi
    fi
  done
  
  exit 0
}

# Führe Hauptfunktion aus
main
