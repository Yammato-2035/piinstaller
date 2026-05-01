#!/bin/bash
# Setuphelfer / PI-Installer – Bestandsaufnahme aller Installationen und Startpfade.
# Löscht nichts. Nur lesen/ausgeben (für Entwicklung und Support).
#
# Exit-Codes: 0 = OK, 2 = WARN, 1 = FAIL
#
#   ./scripts/audit-setuphelfer-installations.sh
#   sudo ./scripts/audit-setuphelfer-installations.sh   # optional, für lsof auf /opt

set -uo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

AUDIT_FAIL=0
AUDIT_WARN=0

bump_fail() { AUDIT_FAIL=1; }
bump_warn() { AUDIT_WARN=1; }

section() {
  echo ""
  echo -e "${CYAN}=== $* ===${NC}"
}

read_version_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    if command -v jq >/dev/null 2>&1 && jq -e .version "$f" >/dev/null 2>&1; then
      jq -r '.version // empty' "$f" 2>/dev/null || cat "$f"
    else
      head -1 "$f" | tr -d '\r'
    fi
  else
    echo "(fehlt)"
  fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"

section "Repository (Entwicklung, nicht löschen)"
echo -e "Pfad: ${GREEN}$REPO_ROOT${NC}"
if [[ -f "$REPO_ROOT/config/version.json" ]]; then
  echo -n "config/version.json: "
  read_version_file "$REPO_ROOT/config/version.json"
fi
for _b in "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer"; do
  if [[ -e "$_b" ]]; then
    echo -n "Tauri-Binary (Release): $_b → "
    ls -la "$_b"
    if [[ -L "$_b" ]]; then
      echo "  → Ziel: $(readlink -f "$_b" 2>/dev/null || readlink "$_b")"
    fi
  else
    echo "Tauri-Binary (Release): (noch nicht gebaut)"
  fi
done

section "System-Installation Setuphelfer (/opt/setuphelfer)"
if [[ -d /opt/setuphelfer ]]; then
  echo -n "config/version.json: "
  read_version_file /opt/setuphelfer/config/version.json
  for _b in /opt/setuphelfer/frontend/src-tauri/target/release/pi-installer; do
    if [[ -e "$_b" ]]; then
      ls -la "$_b"
      [[ -L "$_b" ]] && echo "  → Ziel: $(readlink -f "$_b" 2>/dev/null || true)"
    fi
  done
else
  echo "(Verzeichnis fehlt)"
  bump_fail
fi

section "Legacy-Pfad /opt/pi-installer (live)"
if [[ -d /opt/pi-installer ]]; then
  echo -e "${RED}FAIL-Kandidat:${NC} /opt/pi-installer existiert noch als aktiver Pfad."
  bump_fail
else
  echo -e "${GREEN}OK:${NC} Kein Verzeichnis /opt/pi-installer (vermutlich archiviert/entfernt)."
fi

section "Legacy-Archive unter /opt (pi-installer.archiv-*)"
shopt -s nullglob
_arch=(/opt/pi-installer.archiv-*)
if [[ ${#_arch[@]} -gt 0 ]]; then
  for d in "${_arch[@]}"; do
    echo "  $d"
  done
else
  echo "  (keine Archiv-Verzeichnisse gefunden)"
fi
shopt -u nullglob

section "Symlinks unter /usr/local/bin"
ls -la /usr/local/bin 2>/dev/null | grep -E 'setuphelfer|pi-installer' || echo "(keine Treffer)"

section "systemd: Setuphelfer + Legacy pi-installer"
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-unit-files --type=service 2>/dev/null | grep -iE 'setuphelfer|pi-installer' || true

  echo ""
  echo -n "pi-installer.service is-enabled: "
  _pie=$(systemctl is-enabled pi-installer.service 2>&1 || true)
  echo "$_pie"
  if [[ "$_pie" == *masked* ]]; then
    echo -e "  ${GREEN}OK:${NC} pi-installer.service ist maskiert."
  else
    echo -e "  ${RED}FAIL-Kandidat:${NC} pi-installer.service ist nicht maskiert (Status: $_pie)."
    bump_fail
  fi

  for u in setuphelfer-backend setuphelfer; do
    if systemctl cat "$u.service" >/dev/null 2>&1; then
      echo ""
      echo -e "${YELLOW}$u.service${NC} – is-enabled: $(systemctl is-enabled "$u.service" 2>/dev/null || echo '?'), is-active: $(systemctl is-active "$u.service" 2>/dev/null || echo '?')"
      systemctl cat "$u.service" 2>/dev/null | grep -E '^(ExecStart|WorkingDirectory|User=)' || true
      if [[ "$(systemctl is-active "$u.service" 2>/dev/null)" != "active" ]]; then
        echo -e "  ${RED}FAIL-Kandidat:${NC} $u.service ist nicht active."
        bump_fail
      fi
    fi
  done
else
  echo "systemctl nicht verfügbar"
  bump_warn
fi

section "Harte Legacy-Pfade (/opt/pi-installer) in systemd, Desktop, Repo-Skripten"
# Live-Pfad in Unit-Dateien (ohne unser Archiv-Suffix)
_hard_systemd=$(
  grep -rEl \
    --exclude='pi-installer.service.backup.*' \
    --exclude='pi-installer.service.before-mask.*' \
    --exclude='*.dpkg-dist' \
    '/opt/pi-installer(/|$)' /etc/systemd/system 2>/dev/null || true
)
_hard_desktop=$(grep -rEl '/opt/pi-installer(/|$)' /usr/share/applications /home/*/.local/share/applications /home/*/Desktop 2>/dev/null || true)
_hard_scripts=$(
  grep -rEl '/opt/pi-installer' "$REPO_ROOT/scripts" --include='*.sh' 2>/dev/null \
    | grep -v 'audit-setuphelfer-installations\.sh' || true
)

if [[ -n "$_hard_systemd" ]]; then
  echo -e "${RED}Treffer systemd:${NC}"
  echo "$_hard_systemd" | sed 's/^/  /'
  bump_fail
else
  echo "systemd: keine harten /opt/pi-installer-Pfade (außer Archiv/Backup-Namen ausgeschlossen)."
fi

if [[ -n "$_hard_desktop" ]]; then
  echo -e "${YELLOW}WARN Desktop:${NC}"
  echo "$_hard_desktop" | sed 's/^/  /'
  bump_warn
else
  echo "Desktop: keine Exec-Ziele auf /opt/pi-installer."
fi

if [[ -n "$_hard_scripts" ]]; then
  echo -e "${YELLOW}WARN Repo-Skripte (Referenzen auf Legacy-Pfad):${NC}"
  echo "$_hard_scripts" | sed 's/^/  /'
  bump_warn
else
  echo "Repo scripts: keine /opt/pi-installer-Strings unter scripts/."
fi

section "Desktop-Starter (Exec-Zeilen, Auszug)"
for d in /usr/share/applications /home/*/.local/share/applications /home/*/Desktop; do
  [[ -d "$d" ]] || continue
  grep -rH '^Exec=' "$d"/*.desktop 2>/dev/null | grep -iE 'setuphelfer|pi-installer|piinstaller' || true
done

section "Tauri / WebView LocalStorage (Identifier de.pi-installer.app)"
if [[ -d "${HOME}/.local/share/de.pi-installer.app" ]]; then
  ls -la "${HOME}/.local/share/de.pi-installer.app" 2>/dev/null | head -20
  if [[ -d "${HOME}/.local/share/de.pi-installer.app/localstorage" ]]; then
    echo "LocalStorage-Dateien:"
    ls -la "${HOME}/.local/share/de.pi-installer.app/localstorage" 2>/dev/null || true
  fi
else
  echo "(kein Ordner ~/.local/share/de.pi-installer.app)"
fi

section "Konfiguration (Auszug)"
for f in "${HOME}/.config/pi-installer/config.json" /etc/setuphelfer/config.json; do
  [[ -f "$f" ]] && echo "  $f ($(wc -c <"$f") Bytes)" || true
done

section "Lauschende Ports (8000, 3001)"
if command -v ss >/dev/null 2>&1; then
  ss -tlnp 2>/dev/null | grep -E ':8000|:3001' || echo "(keine Listener auf 8000/3001)"
else
  echo "ss nicht verfügbar"
  bump_warn
fi

section "Laufende Prozesse (Auszug)"
pgrep -af 'setuphelfer|pi-installer|uvicorn.*app:app|vite preview' 2>/dev/null | grep -v 'audit-setuphelfer' || true

section "Repo-Tauri vs. /opt/setuphelfer (Release)"
if [[ -f "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer" ]] && [[ -f /opt/setuphelfer/frontend/src-tauri/target/release/pi-installer ]]; then
  _repo_stat=$(stat -c '%Y %s' "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer" 2>/dev/null || stat -f '%m %z' "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer" 2>/dev/null)
  _opt_stat=$(stat -c '%Y %s' /opt/setuphelfer/frontend/src-tauri/target/release/pi-installer 2>/dev/null || stat -f '%m %z' /opt/setuphelfer/frontend/src-tauri/target/release/pi-installer 2>/dev/null)
  _repo_t="${_repo_stat%% *}"
  _opt_t="${_opt_stat%% *}"
  _repo_s="${_repo_stat#* }"
  _opt_s="${_opt_stat#* }"
  if [[ -n "$_repo_t" && -n "$_opt_t" && "$_repo_t" -lt "$_opt_t" ]]; then
    echo -e "${YELLOW}WARN:${NC} Repo-Tauri ist älter (mtime) als /opt/setuphelfer."
    bump_warn
  fi
  _thresh=$((_opt_s * 9 / 10))
  if [[ -n "$_repo_s" && -n "$_opt_s" && "$_repo_s" -lt "$_thresh" ]]; then
    echo -e "${YELLOW}WARN:${NC} Repo-Tauri ist deutlich kleiner als /opt/setuphelfer (${_repo_s} < 90% von ${_opt_s})."
    bump_warn
  fi
  if [[ "$AUDIT_WARN" -eq 0 ]] && [[ "$AUDIT_FAIL" -eq 0 ]]; then
    echo "Repo- und /opt-Tauri wirken konsistent (keine WARN aus diesem Block)."
  fi
else
  echo "(Vergleich übersprungen: eine der beiden Binaries fehlt)"
fi

section "Reversibilität Legacy-Service (Hinweis)"
echo "Wenn pi-installer.service maskiert wurde:"
echo "  sudo systemctl unmask pi-installer.service"
echo "  sudo mv /etc/systemd/system/pi-installer.service.before-mask.* /etc/systemd/system/pi-installer.service   # passendes Datum wählen"
echo "  sudo systemctl daemon-reload"
echo "Oder stattdessen die Datei pi-installer.service.backup.* verwenden."

section "${MAGENTA}Abschlussbewertung${NC}"
if [[ "$AUDIT_FAIL" -ne 0 ]]; then
  echo -e "${RED}FINAL_VERDICT: FAIL${NC}"
  exit 1
fi
if [[ "$AUDIT_WARN" -ne 0 ]]; then
  echo -e "${YELLOW}FINAL_VERDICT: WARN${NC}"
  exit 2
fi
echo -e "${GREEN}FINAL_VERDICT: OK${NC}"
exit 0
