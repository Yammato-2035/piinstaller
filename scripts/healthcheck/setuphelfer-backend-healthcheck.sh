#!/usr/bin/env bash
# Read-only Backend-Liveness fuer optionalen systemd-Timer (nicht automatisch aktiv).
# ENABLE_RESTART=0 (Default): nur Exit-Code + Log, kein systemctl restart.
# ENABLE_RESTART=1: systemctl restart setuphelfer-backend.service (nur als root/systemd).

set -euo pipefail

BASE_URL="${SETUPHELFER_HEALTH_URL:-http://127.0.0.1:8000/health}"
CONNECT_TIMEOUT="${SETUPHELFER_HEALTH_CONNECT_TIMEOUT:-2}"
MAX_TIME="${SETUPHELFER_HEALTH_MAX_TIME:-4}"
SERVICE="${SETUPHELFER_BACKEND_SERVICE:-setuphelfer-backend.service}"
ENABLE_RESTART="${ENABLE_RESTART:-0}"

log() { printf '%s\n' "$*" >&2; }

if ! command -v curl >/dev/null 2>&1; then
  log "setuphelfer-backend-healthcheck: curl fehlt"
  exit 2
fi

http_code="000"
set +e
http_code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout "$CONNECT_TIMEOUT" --max-time "$MAX_TIME" "$BASE_URL" 2>/dev/null)"
curl_ec=$?
set -e

if [[ "$curl_ec" -eq 0 ]] && [[ "$http_code" == "200" ]]; then
  log "setuphelfer-backend-healthcheck: OK HTTP $http_code"
  exit 0
fi

if [[ "$curl_ec" -eq 28 ]]; then
  log "setuphelfer-backend-healthcheck: FAIL timeout (HTTP $http_code)"
elif [[ "$curl_ec" -eq 7 ]]; then
  log "setuphelfer-backend-healthcheck: FAIL unreachable"
else
  log "setuphelfer-backend-healthcheck: FAIL curl_ec=$curl_ec HTTP $http_code"
fi

if [[ "$ENABLE_RESTART" == "1" ]]; then
  if command -v systemctl >/dev/null 2>&1; then
    log "setuphelfer-backend-healthcheck: ENABLE_RESTART=1 -> systemctl restart $SERVICE"
    systemctl restart "$SERVICE"
  else
    log "setuphelfer-backend-healthcheck: systemctl nicht verfuegbar"
    exit 3
  fi
fi

exit 1
