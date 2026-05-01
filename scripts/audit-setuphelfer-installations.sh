#!/bin/bash
# Setuphelfer – Bestandsaufnahme aller Installationen und Startpfade.
# Löscht nichts. Nur lesen/ausgeben (für Entwicklung und Support).
#
# Exit-Codes: 0 = OK, 2 = WARN, 1 = FAIL
#
#   ./scripts/audit-setuphelfer-installations.sh
#   sudo ./scripts/audit-setuphelfer-installations.sh   # optional, für lsof auf /opt
#
# Legacy-Installationspfad wird zur Laufzeit aus ${_OPT}/${_LEG} zusammengesetzt
# (kein harter String im Quelltext), die Prüfung anderer Dateien nutzt denselben Needle.

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
_OPT="/opt"
_LEG="pi-installer"
_LIVE_LEGACY="${_OPT}/${_LEG}"
_NEEDLE="${_LIVE_LEGACY}"

scan_functional_sources_for_needle() {
  section "Repository-Quellcode: harte Legacy-Pfad-String (${_NEEDLE})"
  echo "Regel: Treffer in ausführbaren Pfaden (Skripte, Backend, frontend/src, debian) → FAIL mit Datei:Zeile."
  echo "Ausnahmen: frontend/dist (Build-Artefakt), dieses Audit-Skript, debian/changelog (historisch), docs/, website/, CHANGELOG.md (nur Hinweis)."

  _scan_one() {
    local f="$1"
    [[ -f "$f" ]] || return 0
    if grep -qF "${_NEEDLE}" "$f" 2>/dev/null; then
      echo -e "${RED}FAIL${NC} ${f#$REPO_ROOT/}"
      grep -nF "${_NEEDLE}" "$f" | sed 's/^/  /'
      echo "  → Empfehlung: Pfad auf ${_OPT}/setuphelfer migrieren oder Legacy nur in Doku (archiviert) erwähnen."
      bump_fail
    fi
  }

  local sh
  for sh in "$REPO_ROOT"/scripts/*.sh; do
    [[ -f "$sh" ]] || continue
    [[ "$(basename "$sh")" == "audit-setuphelfer-installations.sh" ]] && continue
    _scan_one "$sh"
  done

  local py
  while IFS= read -r -d '' py; do
    _scan_one "$py"
  done < <(find "$REPO_ROOT/backend" -name '*.py' -print0 2>/dev/null)

  local fe
  while IFS= read -r -d '' fe; do
    _scan_one "$fe"
  done < <(find "$REPO_ROOT/frontend/src" \( -name '*.tsx' -o -name '*.ts' -o -name '*.jsx' -o -name '*.js' \) -print0 2>/dev/null)

  local df
  for df in "$REPO_ROOT"/debian/*; do
    [[ -f "$df" ]] || continue
    [[ "$(basename "$df")" == "changelog" ]] && continue
    _scan_one "$df"
  done

  local rootf
  for rootf in "$REPO_ROOT"/*.service "$REPO_ROOT"/*.service.install; do
    [[ -f "$rootf" ]] || continue
    _scan_one "$rootf"
  done

  if [[ "$AUDIT_FAIL" -eq 0 ]]; then
    echo -e "${GREEN}OK:${NC} Keine ${_NEEDLE}-Treffer in geprüften funktionalen Quellen."
  fi

  section "Dokumentation & Changelog (Hinweis, kein automatisches FAIL/WARN)"
  local _dc=0
  if [[ -d "$REPO_ROOT/docs" ]]; then
    _dc=$(grep -rIlF "${_NEEDLE}" "$REPO_ROOT/docs" 2>/dev/null | wc -l)
  fi
  echo "Treffer unter docs/: ${_dc:-0} Datei(en) — erwarten: Kontext ›Legacy / archiviert / nicht mehr verwenden‹."
  if [[ -f "$REPO_ROOT/CHANGELOG.md" ]] && grep -qF "${_NEEDLE}" "$REPO_ROOT/CHANGELOG.md" 2>/dev/null; then
    echo "CHANGELOG.md enthält historische ${_NEEDLE}-Erwähnungen (OK)."
  fi
}

scan_functional_sources_for_needle

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

section "System-Installation Setuphelfer (${_OPT}/setuphelfer)"
if [[ -d ${_OPT}/setuphelfer ]]; then
  echo -n "config/version.json: "
  read_version_file "${_OPT}/setuphelfer/config/version.json"
  for _b in "${_OPT}/setuphelfer/frontend/src-tauri/target/release/pi-installer"; do
    if [[ -e "$_b" ]]; then
      ls -la "$_b"
      [[ -L "$_b" ]] && echo "  → Ziel: $(readlink -f "$_b" 2>/dev/null || true)"
    fi
  done
else
  echo "(Verzeichnis fehlt)"
  bump_fail
fi

section "Legacy-Pfad live (${_LIVE_LEGACY})"
if [[ -d "${_LIVE_LEGACY}" ]]; then
  echo -e "${RED}FAIL:${NC} ${_LIVE_LEGACY} existiert noch — sollte archiviert (z. B. ${_OPT}/${_LEG}.archiv-DATUM) oder entfernt sein."
  bump_fail
else
  echo -e "${GREEN}OK:${NC} Kein Verzeichnis ${_LIVE_LEGACY} (vermutlich archiviert/entfernt)."
fi

section "Legacy-Archive unter ${_OPT} (${_LEG}.archiv-*)"
shopt -s nullglob
_arch=("${_OPT}/${_LEG}.archiv-"*)
if [[ ${#_arch[@]} -gt 0 ]]; then
  for d in "${_arch[@]}"; do
    echo "  $d"
    if find "$d" -maxdepth 3 -type f -perm -111 2>/dev/null | head -5 | grep -q .; then
      echo -e "  ${YELLOW}Hinweis:${NC} unter $d wurden ausführbare Dateien gefunden (nur dokumentiert, nichts gelöscht)."
    fi
  done
else
  echo "  (keine Archiv-Verzeichnisse gefunden)"
fi
shopt -u nullglob

section "Symlinks unter /usr/local/bin"
ls -la /usr/local/bin 2>/dev/null | grep -E 'setuphelfer|pi-installer' || echo "(keine Treffer)"

section "systemd: Setuphelfer + Legacy ${_LEG}"
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-unit-files --type=service 2>/dev/null | grep -iE 'setuphelfer|pi-installer' || true

  echo ""
  echo -n "${_LEG}.service is-enabled: "
  _pie=$(systemctl is-enabled "${_LEG}.service" 2>&1 || true)
  echo "$_pie"
  if [[ "$_pie" == *masked* ]]; then
    echo -e "  ${GREEN}OK:${NC} ${_LEG}.service ist maskiert."
  else
    echo -e "  ${RED}FAIL:${NC} ${_LEG}.service ist nicht maskiert (Status: $_pie). Handlung: sudo systemctl mask ${_LEG}.service"
    bump_fail
  fi

  for u in setuphelfer-backend setuphelfer; do
    if systemctl cat "$u.service" >/dev/null 2>&1; then
      echo ""
      echo -e "${YELLOW}$u.service${NC} – is-enabled: $(systemctl is-enabled "$u.service" 2>/dev/null || echo '?'), is-active: $(systemctl is-active "$u.service" 2>/dev/null || echo '?')"
      systemctl cat "$u.service" 2>/dev/null | grep -E '^(ExecStart|WorkingDirectory|User=)' || true
      if [[ "$(systemctl is-active "$u.service" 2>/dev/null)" != "active" ]]; then
        echo -e "  ${RED}FAIL:${NC} $u.service ist nicht active."
        bump_fail
      fi
    fi
  done
else
  echo "systemctl nicht verfügbar"
  bump_warn
fi

section "Harte Legacy-Pfade (${_NEEDLE}) in systemd & Desktop"
_hard_systemd=$(
  grep -rEl \
    --exclude='pi-installer.service.backup.*' \
    --exclude='pi-installer.service.before-mask.*' \
    --exclude='*.dpkg-dist' \
    "${_NEEDLE}(/|$)" /etc/systemd/system 2>/dev/null || true
)
_hard_desktop=$(grep -rEl "${_NEEDLE}(/|$)" /usr/share/applications /home/*/.local/share/applications /home/*/Desktop 2>/dev/null || true)

if [[ -n "$_hard_systemd" ]]; then
  echo -e "${RED}FAIL systemd:${NC}"
  echo "$_hard_systemd" | sed 's/^/  /'
  echo "  → Unit-Dateien auf ${_OPT}/setuphelfer und setuphelfer-User prüfen."
  bump_fail
else
  echo "systemd: keine ${_NEEDLE}-Pfade (außer ausgeschlossene Backups)."
fi

if [[ -n "$_hard_desktop" ]]; then
  echo -e "${YELLOW}WARN Desktop:${NC}"
  echo "$_hard_desktop" | sed 's/^/  /'
  echo "  → Desktop-Starter auf scripts/start-setuphelfer.sh bzw. ${_OPT}/setuphelfer ausrichten."
  bump_warn
else
  echo "Desktop: keine Exec-Ziele auf ${_NEEDLE}."
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

section "Repo-Tauri vs. ${_OPT}/setuphelfer (Release, nur Hinweis)"
if [[ -f "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer" ]] && [[ -f ${_OPT}/setuphelfer/frontend/src-tauri/target/release/pi-installer ]]; then
  _repo_stat=$(stat -c '%Y %s' "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer" 2>/dev/null || stat -f '%m %z' "$REPO_ROOT/frontend/src-tauri/target/release/pi-installer" 2>/dev/null)
  _opt_stat=$(stat -c '%Y %s' "${_OPT}/setuphelfer/frontend/src-tauri/target/release/pi-installer" 2>/dev/null || stat -f '%m %z' "${_OPT}/setuphelfer/frontend/src-tauri/target/release/pi-installer" 2>/dev/null)
  _repo_t="${_repo_stat%% *}"
  _opt_t="${_opt_stat%% *}"
  _repo_s="${_repo_stat#* }"
  _opt_s="${_opt_stat#* }"
  if [[ -n "$_repo_t" && -n "$_opt_t" && "$_repo_t" -lt "$_opt_t" ]]; then
    echo -e "${CYAN}Hinweis:${NC} Repo-Tauri ist älter (mtime) als ${_OPT}/setuphelfer — bei Deploy ggf. neu bauen."
  fi
  _thresh=$((_opt_s * 9 / 10))
  if [[ -n "$_repo_s" && -n "$_opt_s" && "$_repo_s" -lt "$_thresh" ]]; then
    echo -e "${CYAN}Hinweis:${NC} Repo-Tauri ist deutlich kleiner als ${_OPT}/setuphelfer (${_repo_s} vs ${_opt_s} Bytes)."
  fi
  if [[ -n "$_repo_t" && -n "$_opt_t" && "$_repo_t" -ge "$_opt_t" ]] && [[ -n "$_repo_s" && -n "$_opt_s" && "$_repo_s" -ge "$_thresh" ]]; then
    echo "Repo- und /opt-Tauri wirken konsistent."
  fi
else
  echo "(Vergleich übersprungen: eine der beiden Binaries fehlt)"
fi

section "Reversibilität Legacy-Service (Hinweis)"
echo "Wenn ${_LEG}.service maskiert wurde:"
echo "  sudo systemctl unmask ${_LEG}.service"
echo "  sudo mv /etc/systemd/system/${_LEG}.service.before-mask.* /etc/systemd/system/${_LEG}.service   # passendes Datum"
echo "  sudo systemctl daemon-reload"
echo "Oder die passende ${_LEG}.service.backup.*-Datei verwenden."

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
