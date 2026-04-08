#!/bin/bash
# Phase F – Zielsystem-Prüfung nach Installation (Setuphelfer oder Legacy pi-installer)
# Nutzt: systemctl, curl, optional journalctl (ohne Änderungen am System).
#
# Aufruf (im Repo oder auf dem Zielsystem):
#   ./scripts/verify-setuphelfer-install.sh
#   ./scripts/verify-setuphelfer-install.sh --no-journal
#
# Umgebung:
#   VERIFY_BACKEND_URL   (Default http://127.0.0.1:8000)
#   VERIFY_FRONTEND_URL  (Default http://127.0.0.1:3001)

set -uo pipefail

BACKEND_URL="${VERIFY_BACKEND_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${VERIFY_FRONTEND_URL:-http://127.0.0.1:3001}"
API_VERSION="${BACKEND_URL%/}/api/version"

INCLUDE_JOURNAL=1
if [[ "${1:-}" == "--no-journal" ]]; then
  INCLUDE_JOURNAL=0
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

fail() {
  echo -e "${RED}FAIL${NC} $*"
  FAILED=1
}
ok() {
  echo -e "${GREEN}OK${NC}   $*"
}
info() {
  echo -e "${CYAN}…${NC}   $*"
}
warn() {
  echo -e "${YELLOW}WARN${NC} $*"
}

FAILED=0

echo ""
echo -e "${CYAN}=== Setuphelfer – Zielsystem-Prüfung (Phase F) ===${NC}"
echo ""

# --- systemd: erkannte Units ---
BACKEND_UNIT=""
WEB_UNIT=""
if systemctl cat setuphelfer-backend.service &>/dev/null; then
  BACKEND_UNIT="setuphelfer-backend.service"
  WEB_UNIT="setuphelfer.service"
elif systemctl cat pi-installer-backend.service &>/dev/null; then
  BACKEND_UNIT="pi-installer-backend.service"
  WEB_UNIT="pi-installer.service"
  warn "Legacy-Units (pi-installer*) – Migration: Paket setuphelfer / docs/SYSTEM_INSTALLATION.md"
fi

if [[ -z "$BACKEND_UNIT" ]]; then
  warn "Keine bekannte Backend-Unit (setuphelfer-backend / pi-installer-backend). API-Check trotzdem."
else
  info "Backend-Unit: $BACKEND_UNIT"
  if systemctl is-active --quiet "$BACKEND_UNIT" 2>/dev/null; then
    ok "systemd: $BACKEND_UNIT ist active"
  else
    fail "systemd: $BACKEND_UNIT ist nicht active (sudo systemctl status $BACKEND_UNIT)"
  fi

  if [[ -n "$WEB_UNIT" ]] && systemctl cat "$WEB_UNIT" &>/dev/null; then
    info "Web-UI-Unit: $WEB_UNIT"
    if systemctl is-active --quiet "$WEB_UNIT" 2>/dev/null; then
      ok "systemd: $WEB_UNIT ist active"
    else
      warn "systemd: $WEB_UNIT ist nicht active (nur Backend möglich – siehe BETRIEB_REPO_VS_SERVICE.md)"
    fi
  fi
fi

echo ""

# --- curl: API ---
API_TMP=""
if command -v curl &>/dev/null; then
  API_TMP=$(mktemp) || API_TMP="/tmp/setuphelfer-verify-api-$$.json"
  # Kein „|| echo 000“: sonst doppelte Ausgabe, wenn curl scheitert aber -w schon „000“ liefert
  set +e
  HTTP_CODE=$(curl -sS -o "$API_TMP" -w "%{http_code}" --max-time 5 "$API_VERSION" 2>/dev/null)
  _ce=$?
  set -e
  [[ "$_ce" -eq 0 && -n "$HTTP_CODE" ]] || HTTP_CODE="000"
  if [[ "$HTTP_CODE" == "200" ]]; then
    ok "HTTP $HTTP_CODE $API_VERSION"
    if [[ -s "$API_TMP" ]]; then
      info "Antwort (Auszug): $(head -c 200 "$API_TMP" 2>/dev/null | tr -d '\n' | head -c 200)…"
    fi
  else
    fail "HTTP $HTTP_CODE $API_VERSION (Backend erwartet unter :8000)"
  fi
  rm -f "$API_TMP"
else
  warn "curl nicht installiert – API-Check übersprungen"
  FAILED=1
fi

echo ""

# --- curl: Frontend (optional, kein harter Fehler wenn nur API-Dev) ---
if command -v curl &>/dev/null; then
  set +e
  FE_CODE=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 "$FRONTEND_URL/" 2>/dev/null)
  _fe=$?
  set -e
  [[ "$_fe" -eq 0 && -n "$FE_CODE" ]] || FE_CODE="000"
  if [[ "$FE_CODE" == "200" ]] || [[ "$FE_CODE" == "304" ]]; then
    ok "HTTP $FE_CODE $FRONTEND_URL/ (Web-UI)"
  else
    warn "HTTP $FE_CODE $FRONTEND_URL/ (Web-UI; bei reinem Backend-Test ignorierbar)"
  fi
fi

echo ""

# --- journalctl (letzte Zeilen) ---
if [[ "$INCLUDE_JOURNAL" -eq 1 ]] && [[ -n "$BACKEND_UNIT" ]]; then
  JU="${BACKEND_UNIT%.service}"
  if command -v journalctl &>/dev/null; then
    info "Letzte Logzeilen: journalctl -u $JU -n 12 --no-pager"
    journalctl -u "$JU" -n 12 --no-pager 2>/dev/null || warn "journalctl nicht lesbar (ggf. sudo oder fehlende Rechte)"
  fi
  echo ""
fi

# --- Paket (optional) ---
if command -v dpkg &>/dev/null; then
  if dpkg -l setuphelfer 2>/dev/null | grep -q '^ii'; then
    ok "dpkg: Paket setuphelfer installiert"
  elif dpkg -l pi-installer 2>/dev/null | grep -q '^ii'; then
    warn "dpkg: Legacy-Paket pi-installer installiert"
  else
    info "dpkg: weder setuphelfer noch pi-installer als Paket (manuelle Installation möglich)"
  fi
fi

echo ""
if [[ "$FAILED" -eq 0 ]]; then
  echo -e "${GREEN}Prüfung abgeschlossen: keine harten Fehler.${NC}"
  echo ""
  exit 0
fi

echo -e "${RED}Prüfung abgeschlossen: mindestens ein harter Fehler (siehe oben).${NC}"
echo "Hinweise: docs/VERIFY_TARGET_SYSTEM.md · docs/BETRIEB_REPO_VS_SERVICE.md"
echo ""
exit 1
