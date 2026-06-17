#!/usr/bin/env bash
# Public/Private boundary gate — read-only.
# Blocks proprietary cloud, telemetry server, operator dashboard, billing, and secrets
# from public or unknown repository context.
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
EXIT_CLOUD_BACKUP=17
EXIT_CLOUD_FREE_PRO=18
EXIT_DIAGNOSTICS_SERVER=19
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

_set_exit() {
  local new="$1"
  if [[ "${exit_code}" -eq "${EXIT_OK}" || "${exit_code}" -eq "${EXIT_REVIEW}" ]]; then
    exit_code="${new}"
  fi
}

# Paths where forbidden terms may appear when documenting boundaries (not implementing them).
DOC_TERM_ALLOWLIST=(
  "docs/architecture/COMMERCIAL_MODULE_BOUNDARY.md"
  "docs/architecture/PUBLIC_PRIVATE_BOUNDARY.md"
  "docs/architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md"
  "docs/architecture/CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md"
  "docs/architecture/PUBLIC_PRIVATE_PRODUCT_SPLIT.md"
  "docs/architecture/PRIVATE_REPOSITORY_STRATEGY.md"
  "docs/architecture/SETUPHELFER_PRODUCT_FAMILY_V2.md"
  "docs/architecture/SETUPHELFER_CORE_PLATFORM.md"
  "docs/architecture/DCC_PRODUCT_MODEL_V2.md"
  "docs/architecture/TELEMETRY_SERVER_IONOS_PLESK_ARCHITECTURE.md"
  "docs/architecture/PLESK_EXTENSION_ADAPTER_PLAN.md"
  "docs/roadmap/PRODUCT_ROADMAP_V2.md"
  "docs/business/"
  "docs/ui/DCC_MULTI_PRODUCT_DASHBOARD_V2.md"
  "docs/security/PRODUCT_FAMILY_RISK_ANALYSIS_V2.md"
  "docs/deploy/TELEMETRY_PLESK_REVERSE_PROXY_DE.md"
  "docs/security/CLOUDSERVER_EDITION_SECURITY_CONTRACT.md"
  "docs/private-handoff/"
  "docs/evidence/public-private/"
  "docs/evidence/msi/"
  "docs/evidence/monolith/"
  "docs/evidence/blueprints/"
  "docs/evidence/release-gates/"
  "docs/hardware-tests/"
  "docs/runbooks/MSI_"
  "docs/blueprints/"
  "docs/roadmap/STATUS_MATRIX.md"
  "docs/roadmap/ROADMAP_2026.md"
  "docs/roadmap/MASTER_ROADMAP_2026_2030.md"
  "docs/roadmap/PRODUCT_ROADMAP_V2.md"
  "docs/faq/CLOUDSERVER_BOUNDARY_FAQ_DE.md"
  "docs/faq/CLOUDSERVER_BOUNDARY_FAQ_EN.md"
  "docs/faq/ARCHITECTURE_FAQ_DE.md"
  "docs/faq/ARCHITECTURE_FAQ_EN.md"
  "docs/knowledge-base/"
  "docs/dev-dashboard/README.md"
  "docs/legal/"
  "scripts/check-public-private-boundary.sh"
)

_is_doc_allowlisted() {
  local f="$1"
  for prefix in "${DOC_TERM_ALLOWLIST[@]}"; do
    if [[ "${f}" == "${prefix}"* ]]; then
      return 0
    fi
  done
  return 1
}

# --- 1. Forbidden paths ---
FORBIDDEN_PATHS=(
  "backend/cloud_backup"
  "backend/cloudbackup"
  "backend/cloud_edition"
  "backend/cloudserver_private"
  "backend/cloudserver_edition"
  "backend/cloud_free"
  "backend/cloud_pro"
  "backend/telemetry_server"
  "backend/internal_telemetry"
  "backend/diagnostics_server"
  "backend/internal_diagnostics"
  "backend/operator_dashboard"
  "backend/devcontrol"
  "backend/development_control"
  "backend/licensing"
  "backend/billing"
  "backend/subscriptions"
  "backend/commercial"
  "backend/plesk_adapter"
  "frontend/src/operator"
  "frontend/src/cloud-pro"
  "frontend/src/cloud-backup"
  "frontend/src/devcontrol"
  "frontend/src/pages/CloudOperatorDashboard.tsx"
  "plesk-extension"
  "commercial"
  "licensing"
  "billing"
  "subscriptions"
  "private"
  "internal"
  "secrets"
  "infra/production"
  "deploy/production"
)

for p in "${FORBIDDEN_PATHS[@]}"; do
  if [[ -e "${ROOT}/${p}" ]]; then
    case "${p}" in
      *cloud_backup*|*cloudbackup*|*cloud-backup*)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_CLOUD_BACKUP}"
        ;;
      *cloud_edition*|*cloud_free*|*cloud_pro*|*cloud-pro*)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_CLOUD_FREE_PRO}"
        ;;
      *telemetry*|*internal_telemetry*)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_TELEMETRY}"
        ;;
      *diagnostics_server*|*internal_diagnostics*)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_DIAGNOSTICS_SERVER}"
        ;;
      *operator*)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_OPERATOR}"
        ;;
      *licensing*|*billing*|*subscriptions*|*commercial*|*cloudserver*)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_COMMERCIAL}"
        ;;
      *)
        _add blocked "forbidden_path:${p}"
        _set_exit "${EXIT_PRIVATE_CODE}"
        ;;
    esac
  fi
done

# --- 2. Forbidden terms in changed/staged files ---
FORBIDDEN_TERMS=(
  "CLOUD_BACKUP_PRO"
  "CLOUD_BACKUP_COMMERCIAL"
  "CLOUD_EDITION_FREE"
  "CLOUD_EDITION_PRO"
  "CLOUDSERVER_PRO_LICENSE"
  "CLOUDSERVER_COMMERCIAL"
  "TELEMETRY_SERVER_SECRET"
  "INTERNAL_TELEMETRY_INGEST"
  "DIAGNOSTICS_SERVER_PRIVATE"
  "OPERATOR_DASHBOARD"
  "INTERNAL_DIAGNOSTIC_RULE"
  "DIAGNOSTIC_RULE_BUNDLE"
  "DEV_DASHBOARD_INTERNAL"
  "DEVCONTROL_OPERATOR"
  "PLESK_ADMIN_ACTION"
  "PLESK_EXTENSION_SECRET"
  "HARDWARE_FINGERPRINT_PRIVATE"
  "CUSTOMER_BILLING"
  "LICENSE_ENFORCEMENT"
  "SUBSCRIPTION_ENFORCEMENT"
  "PRIVATE_INGEST"
  "PRIVATE_ADMIN_ENDPOINT"
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
  if _is_doc_allowlisted "${f}"; then
    continue
  fi
  for term in "${FORBIDDEN_TERMS[@]}"; do
    if grep -q "${term}" "${ROOT}/${f}" 2>/dev/null; then
      _add blocked "forbidden_term:${term}:in:${f}"
      case "${term}" in
        CLOUD_BACKUP_*)
          _set_exit "${EXIT_CLOUD_BACKUP}"
          ;;
        CLOUD_EDITION_*|CLOUDSERVER_*)
          _set_exit "${EXIT_CLOUD_FREE_PRO}"
          ;;
        *TELEMETRY*|*INGEST*)
          _set_exit "${EXIT_TELEMETRY}"
          ;;
        DIAGNOSTICS_SERVER_PRIVATE|INTERNAL_DIAGNOSTIC_RULE)
          _set_exit "${EXIT_DIAGNOSTICS_SERVER}"
          ;;
        OPERATOR_DASHBOARD)
          _set_exit "${EXIT_OPERATOR}"
          ;;
        *BILLING*|*LICENSE*|*SUBSCRIPTION*|*PLESK*|CUSTOMER_BILLING)
          _set_exit "${EXIT_COMMERCIAL}"
          ;;
        *SECRET*|*TOKEN*|*PASSWORD*|*KEY*)
          _set_exit "${EXIT_SECRET}"
          ;;
      esac
    fi
  done
done

# --- 3. Secret patterns in changed/staged files (or tracked sample if clean tree) ---
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
    *.pem|*.key|*.p12|*.pfx|.env)
      if [[ "${f}" != ".env" ]] || git -C "${ROOT}" ls-files --error-unmatch "${f}" &>/dev/null; then
        _add blocked "secret_file:${f}"
        _set_exit "${EXIT_SECRET}"
      fi
      ;;
  esac
  if grep -qE '-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "private_key_block:in:${f}"
    _set_exit "${EXIT_SECRET}"
  fi
  if grep -qE '-----BEGIN WIREGUARD PRIVATE KEY-----' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "wireguard_private_key:in:${f}"
    _set_exit "${EXIT_SECRET}"
  fi
  if grep -qE 'AKIA[0-9A-Z]{16}' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "aws_key_pattern:in:${f}"
    _set_exit "${EXIT_SECRET}"
  fi
  if grep -qE 'ghp_[A-Za-z0-9]{20,}' "${ROOT}/${f}" 2>/dev/null; then
    _add blocked "github_token_pattern:in:${f}"
    _set_exit "${EXIT_SECRET}"
  fi
  if grep -qE '(?i)(jwt[_-]?secret|api[_-]?key)\s*=\s*["'"'"'][^"'"'"']{8,}' "${ROOT}/${f}" 2>/dev/null; then
    if ! grep -qE 'changeme|example|placeholder|REPLACE_ME|your[_-]?' "${ROOT}/${f}" 2>/dev/null; then
      _add review "jwt_or_api_secret_literal:in:${f}"
    fi
  fi
done

# --- 4. Internal domains (only example domains allowed) ---
ALLOWED_DOMAIN_FRAGMENTS=(
  "telemetry.internal.setuphelfer.example"
  "operator.internal.setuphelfer.example"
  "diagnose.internal.setuphelfer.example"
  "cloud.private.setuphelfer.example"
  "api.internal.setuphelfer.example"
  "telemetrie.setuphelfer.de"
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
  if _is_doc_allowlisted "${f}"; then
    continue
  fi
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
        _set_exit "${EXIT_PRIVATE_DOMAIN}"
      fi
    fi
  done
done

# --- 5. Docker compose checks ---
while IFS= read -r compose; do
  [[ -n "${compose}" ]] || continue
  if grep -qE '0\.0\.0\.0:[0-9]+:5432|0\.0\.0\.0:[0-9]+:3306' "${compose}" 2>/dev/null; then
    _add blocked "public_db_port:in:${compose}"
    _set_exit "${EXIT_PUBLIC_DB}"
  fi
  if grep -qE '0\.0\.0\.0:[0-9]+:6379' "${compose}" 2>/dev/null; then
    _add blocked "public_redis_port:in:${compose}"
    _set_exit "${EXIT_PUBLIC_DB}"
  fi
  if grep -qE '(POSTGRES_PASSWORD|MYSQL_ROOT_PASSWORD|REDIS_PASSWORD)=\$\{[^}]+\}' "${compose}" 2>/dev/null; then
    : # env var reference ok
  elif grep -qE '(POSTGRES_PASSWORD|MYSQL_ROOT_PASSWORD|REDIS_PASSWORD)=[^$\{][^[:space:]]+' "${compose}" 2>/dev/null; then
    if ! grep -qE 'changeme|example|placeholder|REPLACE_ME' "${compose}" 2>/dev/null; then
      _add review "production_secret_literal:in:${compose}"
    fi
  fi
done < <(find "${ROOT}" -maxdepth 4 \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' \) 2>/dev/null)

# --- 6. .env must not be tracked ---
if git -C "${ROOT}" ls-files --error-unmatch .env &>/dev/null; then
  _add blocked "tracked_env_file:.env"
  _set_exit "${EXIT_SECRET}"
fi

# --- 7. Private endpoint literals in non-doc code ---
PRIVATE_ENDPOINT_PATTERNS=(
  '/v1/admin/keys/rotate'
  '/internal/telemetry/ingest'
  '/operator/fleet/production'
  '/plesk/catalog/submit'
)
for f in "${CHANGED_FILES[@]}"; do
  [[ -f "${ROOT}/${f}" ]] || continue
  if _is_doc_allowlisted "${f}"; then
    continue
  fi
  case "${f}" in
    *.py|*.ts|*.tsx|*.js|*.jsx|*.sh)
      ;;
    *)
      continue
      ;;
  esac
  for pat in "${PRIVATE_ENDPOINT_PATTERNS[@]}"; do
    if grep -qF "${pat}" "${ROOT}/${f}" 2>/dev/null; then
      _add blocked "private_endpoint_literal:${pat}:in:${f}"
      _set_exit "${EXIT_PRIVATE_CODE}"
    fi
  done
done

# --- 8. Diagnostic rule bundle filenames ---
for f in "${CHANGED_FILES[@]}"; do
  [[ -f "${ROOT}/${f}" ]] || continue
  if _is_doc_allowlisted "${f}"; then
    continue
  fi
  case "${f}" in
    *diagnostic_rule_bundle*|*internal_diagnostic_rules*|*diagnostics_matcher_private*)
      _add blocked "diagnostic_rule_bundle_path:${f}"
      _set_exit "${EXIT_DIAGNOSTICS_SERVER}"
      ;;
  esac
done

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
