#!/usr/bin/env bash
# Public/Private boundary gate — read-only. Prevents proprietary cloudserver,
# internal telemetry server, operator dashboard, and secrets from public context.
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "${ROOT}"

EXIT_OK=0
EXIT_PRIVATE_CODE=10
EXIT_TELEMETRY=11
EXIT_COMMERCIAL=12
EXIT_SECRET=13
EXIT_OPERATOR=14
EXIT_PUBLIC_DB=15
EXIT_PRIVATE_DOMAIN=16
EXIT_REVIEW=20
EXIT_UNKNOWN=99

status="ok"
exit_code="${EXIT_OK}"
findings=()

_add() {
  local code="$1"
  local msg="$2"
  findings+=("${code}:${msg}")
  if [[ "${code}" == "blocked" ]]; then
    status="blocked"
    if [[ "${exit_code}" -eq "${EXIT_OK}" ]]; then
      exit_code="${EXIT_REVIEW}"
    fi
  elif [[ "${code}" == "review" && "${status}" != "blocked" ]]; then
    status="review_required"
    if [[ "${exit_code}" -eq "${EXIT_OK}" ]]; then
      exit_code="${EXIT_REVIEW}"
    fi
  fi
}

# --- 1. Forbidden paths ---
FORBIDDEN_PATHS=(
  "backend/cloudserver_private"
  "backend/cloudserver_edition"
  "backend/telemetry_server"
  "backend/internal_telemetry"
  "backend/diagnostics_server"
  "backend/internal_diagnostics"
  "backend/operator_dashboard"
  "frontend/src/pages/CloudOperatorDashboard.tsx"
  "frontend/src/operator"
  "commercial"
  "licensing"
  "billing"
  "subscriptions"
  "private"
  "internal"
  "secrets"
  "deploy/production"
  "infra/production"
)

for p in "${FORBIDDEN_PATHS[@]}"; do
  if [[ -e "${ROOT}/${p}" ]]; then
  case "${p}" in
    *telemetry*|*internal_telemetry*)
      _add blocked "forbidden_path:${p}"
      exit_code="${EXIT_TELEMETRY}"
      ;;
    *operator*)
      _add blocked "forbidden_path:${p}"
      exit_code="${EXIT_OPERATOR}"
      ;;
    *cloudserver*|commercial|licensing|billing|subscriptions)
      _add blocked "forbidden_path:${p}"
      exit_code="${EXIT_COMMERCIAL}"
      ;;
    *)
      _add blocked "forbidden_path:${p}"
      if [[ "${exit_code}" -eq "${EXIT_OK}" ]]; then
        exit_code="${EXIT_PRIVATE_CODE}"
      fi
      ;;
  esac
  fi
done

# --- 2. Forbidden terms in changed/staged files ---
FORBIDDEN_TERMS=(
  "CLOUDSERVER_PRO_LICENSE"
  "CLOUDSERVER_COMMERCIAL"
  "TELEMETRY_SERVER_SECRET"
  "INTERNAL_TELEMETRY_INGEST"
  "OPERATOR_DASHBOARD"
  "INTERNAL_DIAGNOSTIC_RULE"
  "HARDWARE_FINGERPRINT_PRIVATE"
  "CUSTOMER_BILLING"
  "LICENSE_ENFORCEMENT"
  "PRIVATE_INGEST"
  "PLESK_CATALOG_SUBMISSION_SECRET"
  "IONOS_PRODUCTION_TOKEN"
  "PLESK_API_TOKEN"
  "SMTP_PASSWORD"
  "JWT_SECRET"
  "CLIENT_SIGNING_PRIVATE_KEY"
  "TELEMETRY_SIGNING_PRIVATE_KEY"
)

CHANGED_FILES=()
while IFS= read -r f; do
  [[ -n "${f}" ]] && CHANGED_FILES+=("${f}")
done < <(git -C "${ROOT}" diff --name-only 2>/dev/null; git -C "${ROOT}" diff --cached --name-only 2>/dev/null | sort -u)

for f in "${CHANGED_FILES[@]}"; do
  [[ -f "${ROOT}/${f}" ]] || continue
  for term in "${FORBIDDEN_TERMS[@]}"; do
    if grep -q "${term}" "${ROOT}/${f}" 2>/dev/null; then
      _add blocked "forbidden_term:${term}:in:${f}"
      case "${term}" in
        *TELEMETRY*|*INGEST*) exit_code="${EXIT_TELEMETRY}" ;;
        *OPERATOR*) exit_code="${EXIT_OPERATOR}" ;;
        *CLOUDSERVER*|*BILLING*|*LICENSE*|*PLESK*) exit_code="${EXIT_COMMERCIAL}" ;;
        *SECRET*|*TOKEN*|*PASSWORD*|*KEY*) exit_code="${EXIT_SECRET}" ;;
      esac
    fi
  done
done

# --- 3. Secret patterns in changed/staged files ---
SECRET_SCAN_FILES=("${CHANGED_FILES[@]}")
if [[ ${#SECRET_SCAN_FILES[@]} -eq 0 ]]; then
  SECRET_SCAN_FILES=()
  while IFS= read -r f; do
    [[ -n "${f}" ]] && SECRET_SCAN_FILES+=("${f}")
  done < <(git -C "${ROOT}" ls-files 2>/dev/null | head -5000)
fi

for f in "${SECRET_SCAN_FILES[@]}"; do
  [[ -f "${ROOT}/${f}" ]] || continue
  case "${f}" in
    *.pem|*.key|*.p12|*.pfx|.env) _add blocked "secret_file:${f}"; exit_code="${EXIT_SECRET}" ;;
  esac
  if grep -qE '-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "private_key_block:in:${f}"
    exit_code="${EXIT_SECRET}"
  fi
  if grep -qE 'AKIA[0-9A-Z]{16}' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "aws_key_pattern:in:${f}"
    exit_code="${EXIT_SECRET}"
  fi
  if grep -qE 'ghp_[A-Za-z0-9]{20,}' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "github_token_pattern:in:${f}"
    exit_code="${EXIT_SECRET}"
  fi
done

# --- 4. Internal domains (only example domains allowed) ---
ALLOWED_DOMAIN_FRAGMENTS=(
  "telemetry.internal.setuphelfer.example"
  "operator.internal.setuphelfer.example"
  "diagnose.internal.setuphelfer.example"
  "cloud.private.setuphelfer.example"
  "api.internal.setuphelfer.example"
  "setuphelfer.example"
  "example.com"
  "localhost"
  "127.0.0.1"
)

SUSPICIOUS_DOMAIN_PATTERNS=(
  '\.internal\.setuphelfer\.(de|com|net|io)'
  'telemetry\.[a-z0-9.-]+\.(de|com|net)'
  'operator\.[a-z0-9.-]+\.(de|com|net)'
  'diagnose\.[a-z0-9.-]+\.(de|com|net)'
)

for f in "${CHANGED_FILES[@]}"; do
  [[ -f "${ROOT}/${f}" ]] || continue
  for pat in "${SUSPICIOUS_DOMAIN_PATTERNS[@]}"; do
    if grep -qE "${pat}" "${ROOT}/${f}" 2>/dev/null; then
      allowed=false
      for ok in "${ALLOWED_DOMAIN_FRAGMENTS[@]}"; do
        if grep -q "${ok}" "${ROOT}/${f}" 2>/dev/null; then
          allowed=true
          break
        fi
      done
      if [[ "${allowed}" == "false" ]]; then
        _add blocked "private_domain_pattern:${pat}:in:${f}"
        exit_code="${EXIT_PRIVATE_DOMAIN}"
      fi
    fi
  done
done

# --- 5. Docker compose checks ---
while IFS= read -r compose; do
  [[ -n "${compose}" ]] || continue
  if grep -qE '0\.0\.0\.0:[0-9]+:5432|0\.0\.0\.0:[0-9]+:3306' "${compose}" 2>/dev/null; then
    _add blocked "public_db_port:in:${compose}"
    exit_code="${EXIT_PUBLIC_DB}"
  fi
  if grep -qE '0\.0\.0\.0:[0-9]+:6379' "${compose}" 2>/dev/null; then
    _add blocked "public_redis_port:in:${compose}"
    exit_code="${EXIT_PUBLIC_DB}"
  fi
  if grep -qE '(POSTGRES_PASSWORD|MYSQL_ROOT_PASSWORD|REDIS_PASSWORD)=\$\{[^}]+\}' "${compose}" 2>/dev/null; then
    : # env var reference ok
  elif grep -qE '(POSTGRES_PASSWORD|MYSQL_ROOT_PASSWORD|REDIS_PASSWORD)=[^$\{][^[:space:]]+' "${compose}" 2>/dev/null; then
  if ! grep -qE 'changeme|example|placeholder|REPLACE_ME' "${compose}" 2>/dev/null; then
    _add review "production_secret_literal:in:${compose}"
  fi
  fi
done < <(find "${ROOT}" -maxdepth 4 -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' 2>/dev/null)

# --- JSON output ---
FINDINGS_JSON="[]"
if [[ ${#findings[@]} -gt 0 ]]; then
  FINDINGS_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${findings[@]}")"
fi
python3 - <<PY
import json
findings = json.loads('''${FINDINGS_JSON}''')
print(json.dumps({
    "status": "${status}",
    "exit_code": ${exit_code},
    "findings": findings,
    "changed_files_scanned": ${#CHANGED_FILES[@]},
}, ensure_ascii=False))
PY

exit "${exit_code}"
