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
      echo -e "  ${YELLOW}WARN:${NC} unter $d wurden ausführbare Dateien gefunden (Archiv prüfen, nichts automatisch löschen)."
      bump_warn
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

_legacy_desktop_names=$(
  find /usr/share/applications /home/*/.local/share/applications /home/*/Desktop \
    -maxdepth 1 -type f -name 'pi-installer*.desktop' 2>/dev/null || true
)
if [[ -n "$_legacy_desktop_names" ]]; then
  _legacy_name_warn=0
  while IFS= read -r _df; do
    [[ -n "$_df" ]] || continue
    _is_hidden=0
    if grep -qE '^[[:space:]]*Hidden[[:space:]]*=[[:space:]]*true' "$_df" 2>/dev/null && \
       grep -qE '^[[:space:]]*NoDisplay[[:space:]]*=[[:space:]]*true' "$_df" 2>/dev/null; then
      _is_hidden=1
    fi
    _base="$(basename "$_df")"
    _user_override="${HOME}/.local/share/applications/${_base}"
    if [[ "$_is_hidden" -eq 0 ]] && [[ "$_df" == /usr/share/applications/* ]] && [[ -f "$_user_override" ]]; then
      if grep -qE '^[[:space:]]*Hidden[[:space:]]*=[[:space:]]*true' "$_user_override" 2>/dev/null && \
         grep -qE '^[[:space:]]*NoDisplay[[:space:]]*=[[:space:]]*true' "$_user_override" 2>/dev/null; then
        _is_hidden=1
      fi
    fi
    if [[ "$_is_hidden" -eq 1 ]]; then
      echo -e "${CYAN}INFO:${NC} historischer Desktop-Dateiname deaktiviert: $_df"
    else
      echo -e "${YELLOW}WARN:${NC} historischer Desktop-Dateiname aktiv sichtbar: $_df"
      _legacy_name_warn=1
    fi
  done <<< "$_legacy_desktop_names"
  if [[ "$_legacy_name_warn" -eq 1 ]]; then
    bump_warn
  fi
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

section "Frontend-Build (dist) vs. Source"
_DIST_DIR="$REPO_ROOT/frontend/dist"
if [[ ! -d "$_DIST_DIR" ]]; then
  echo -e "${YELLOW}WARN:${NC} frontend/dist fehlt — für Produktion: cd frontend && npm run build"
  bump_warn
else
  _dist_newest=$(find "$_DIST_DIR" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1 || echo "0")
  _src_newest=$(find "$REPO_ROOT/frontend/src" -type f \( -name '*.tsx' -o -name '*.ts' -o -name '*.css' \) -printf '%T@\n' 2>/dev/null | sort -n | tail -1 || echo "0")
  if awk -v d="$_dist_newest" -v s="$_src_newest" 'BEGIN{exit !(s>d)}'; then
    echo -e "${YELLOW}WARN:${NC} frontend/src wirkt neuer als frontend/dist — Build veraltet (npm run build)."
    bump_warn
  else
    echo -e "${GREEN}OK:${NC} dist-Zeitstempel nicht hinter dem jüngsten relevanten Source-Stand zurück."
  fi
  _dist_needle_hits=$(grep -rIl "${_NEEDLE}" "$_DIST_DIR" 2>/dev/null | wc -l)
  if [[ "${_dist_needle_hits:-0}" -gt 0 ]]; then
    echo -e "${RED}FAIL:${NC} frontend/dist enthält funktionalen Legacy-Pfad ${_NEEDLE}:"
    grep -rIn "${_NEEDLE}" "$_DIST_DIR" 2>/dev/null | head -20 | sed 's/^/  /'
    bump_fail
  else
    echo -e "${GREEN}OK:${NC} kein ${_NEEDLE} in frontend/dist."
  fi
fi

section "API-Version vs. config/version.json"
_CFG_VER="$(read_version_file "$REPO_ROOT/config/version.json")"
echo "Repo config/version.json: ${_CFG_VER}"
_BACKEND_LISTEN=0
if command -v ss >/dev/null 2>&1 && ss -tln 2>/dev/null | grep -qE '127\.0\.0\.1:8000|:8000'; then
  _BACKEND_LISTEN=1
fi
if [[ "$_BACKEND_LISTEN" -eq 1 ]]; then
  _API_RAW=$(curl -sS --max-time 4 http://127.0.0.1:8000/api/version 2>/dev/null || true)
  _API_VER=""
  if command -v jq >/dev/null 2>&1; then
    _API_VER=$(echo "$_API_RAW" | jq -r '.version // empty' 2>/dev/null || true)
  else
    _API_VER=$(echo "$_API_RAW" | sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
  fi
  if [[ -z "$_API_VER" ]]; then
    echo -e "${RED}FAIL:${NC} Port 8000 lauscht, aber /api/version liefert keine Version (Antwort evtl. leer oder kein Setuphelfer)."
    bump_fail
  elif [[ "$_API_VER" != "$_CFG_VER" ]]; then
    echo -e "${RED}FAIL:${NC} Versionskonflikt: API meldet \"${_API_VER}\", Repo config \"${_CFG_VER}\"."
    bump_fail
  else
    echo -e "${GREEN}OK:${NC} /api/version und config/version.json stimmen überein (${_API_VER})."
  fi
else
  echo -e "${YELLOW}WARN:${NC} Kein Listener auf :8000 — Versionsabgleich mit laufendem Backend übersprungen."
  bump_warn
fi

section "Tauri Release-Binary (Repo) vs. Source & ${_OPT}/setuphelfer"
_REPO_TAURI="$REPO_ROOT/frontend/src-tauri/target/release/pi-installer"
_OPT_TAURI="${_OPT}/setuphelfer/frontend/src-tauri/target/release/pi-installer"
if [[ -x "$_REPO_TAURI" ]]; then
  _bin_mtime=$(stat -c '%Y' "$_REPO_TAURI" 2>/dev/null || stat -f '%m' "$_REPO_TAURI" 2>/dev/null || echo "0")
  _src_tauri_newest=$(find "$REPO_ROOT/frontend/src" "$REPO_ROOT/frontend/src-tauri" -type f \( -name '*.rs' -o -name '*.tsx' -o -name '*.ts' -o -name 'tauri.conf.json' -o -name 'Cargo.toml' \) -printf '%T@\n' 2>/dev/null | sort -n | tail -1 || echo "0")
  if awk -v b="$_bin_mtime" -v s="$_src_tauri_newest" 'BEGIN{exit !(s>b)}'; then
    echo -e "${RED}FAIL:${NC} Repo-Tauri-Binary ist älter als jüngste Quell-Änderung — npm run tauri:build im frontend/ ausführen."
    bump_fail
  else
    echo -e "${GREEN}OK:${NC} Repo-Tauri-Binary nicht hinter src/src-tauri zurück."
  fi
  if [[ "$REPO_ROOT" != "${_OPT}/setuphelfer" ]] && [[ -x "$_OPT_TAURI" ]]; then
    rm=$(stat -c '%Y' "$_REPO_TAURI" 2>/dev/null || stat -f '%m' "$_REPO_TAURI" 2>/dev/null)
    om=$(stat -c '%Y' "$_OPT_TAURI" 2>/dev/null || stat -f '%m' "$_OPT_TAURI" 2>/dev/null)
    rs=$(stat -c '%s' "$_REPO_TAURI" 2>/dev/null || stat -f '%z' "$_REPO_TAURI" 2>/dev/null)
    os=$(stat -c '%s' "$_OPT_TAURI" 2>/dev/null || stat -f '%z' "$_OPT_TAURI" 2>/dev/null)
    _stale=0
    if [[ -n "$rm" && -n "$om" && "$rm" -lt "$om" ]]; then _stale=1; fi
    if [[ -n "$rs" && -n "$os" ]]; then
      _thresh=$((os * 9 / 10))
      if [[ "$rs" -lt "$_thresh" ]]; then _stale=1; fi
    fi
    if [[ "$_stale" -eq 1 ]]; then
      echo -e "${RED}FAIL:${NC} Repo-Tauri ist veraltet gegenüber ${_OPT}/setuphelfer (mtime/Größe) — gleichen Stand bauen oder /opt-Starter nutzen."
      bump_fail
    else
      echo -e "${GREEN}OK:${NC} Repo-Tauri plausibel konsistent zu /opt/setuphelfer-Binary."
    fi
  fi
else
  echo -e "${YELLOW}WARN:${NC} Kein ausführbares Repo-Tauri-Binary unter frontend/src-tauri/target/release/pi-installer (Tauri-Start aus Repo ggf. nicht möglich)."
  bump_warn
fi

section "LocalStorage / Tauri (API-URL Hinweise, nur Heuristik)"
if [[ -d "${HOME}/.local/share/de.pi-installer.app/localstorage" ]]; then
  echo -e "${CYAN}INFO:${NC} Historischer Tauri-Datenpfad de.pi-installer.app vorhanden."
  _ls_warn=0
  for _f in "${HOME}"/.local/share/de.pi-installer.app/localstorage/*.localstorage; do
    [[ -f "$_f" ]] || continue
    if grep -aEo 'https?://[^[:space:]"]+' "$_f" 2>/dev/null | grep -vE '127\.0\.0\.1:8000|localhost:8000|localhost:5173|http://127\.0\.0\.1:5173' | grep -q .; then
      echo -e "${YELLOW}WARN:${NC} In $(basename "$_f") URL(s) außerhalb Standard-Backend (127.0.0.1:8000) — gespeicherte API-Basis in der App prüfen."
      _ls_warn=1
    fi
    if grep -aE '/opt/pi-installer' "$_f" 2>/dev/null | grep -q .; then
      echo -e "${YELLOW}WARN:${NC} In $(basename "$_f") Legacy-Pfadhinweis auf /opt/pi-installer gefunden."
      _ls_warn=1
    fi
  done
  if [[ "$_ls_warn" -eq 1 ]]; then
    bump_warn
  else
    echo -e "${GREEN}OK:${NC} Keine auffälligen Nicht-Standard-URLs in Tauri-LocalStorage (oberflächlich)."
  fi
else
  echo "(kein de.pi-installer.app/localstorage)"
fi

section "Repo-Tauri vs. ${_OPT}/setuphelfer (Kurzüberblick)"
if [[ -f "$_REPO_TAURI" ]] && [[ -f "$_OPT_TAURI" ]]; then
  ls -la "$_REPO_TAURI" "$_OPT_TAURI" 2>/dev/null || true
else
  echo "(mindestens eine Release-Binary fehlt — Details siehe Abschnitt oben)"
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
