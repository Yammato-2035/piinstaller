#!/usr/bin/env bash
# Deploy Setuphelfer Backup-Starter + Polkit (idempotent). Run as root.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

HELPER_SRC="${REPO_ROOT}/packaging/helpers/setuphelfer-backup-starter.py"
HELPER_DST="/usr/lib/setuphelfer/setuphelfer-backup-starter"
POLKIT_RULE_SRC="${REPO_ROOT}/packaging/polkit/10-setuphelfer-backup.rules"
POLKIT_RULE_DST="/etc/polkit-1/rules.d/10-setuphelfer-backup.rules"
POLKIT_POLICY_SRC="${REPO_ROOT}/packaging/polkit/org.setuphelfer.backup.policy"
POLKIT_POLICY_DST="/usr/share/polkit-1/actions/org.setuphelfer.backup.policy"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Bitte als root ausführen: sudo $0" >&2
  exit 1
fi

if [[ ! -f "${HELPER_SRC}" ]]; then
  echo "Helper-Quelle fehlt: ${HELPER_SRC}" >&2
  exit 1
fi

install -d -m 0755 /usr/lib/setuphelfer
install -m 0755 -T "${HELPER_SRC}" "${HELPER_DST}"
chown root:root "${HELPER_DST}"

getent group setuphelfer >/dev/null 2>&1 || groupadd --system setuphelfer

if [[ -f "${POLKIT_POLICY_SRC}" ]]; then
  install -m 0644 -T "${POLKIT_POLICY_SRC}" "${POLKIT_POLICY_DST}"
  chown root:root "${POLKIT_POLICY_DST}"
fi

if [[ -f "${POLKIT_RULE_SRC}" ]]; then
  install -m 0644 -T "${POLKIT_RULE_SRC}" "${POLKIT_RULE_DST}"
  chown root:root "${POLKIT_RULE_DST}"
fi

systemctl daemon-reload 2>/dev/null || true
if systemctl is-active --quiet polkit 2>/dev/null; then
  systemctl restart polkit
elif systemctl is-active --quiet polkit.service 2>/dev/null; then
  systemctl restart polkit.service
fi

echo "OK: ${HELPER_DST} ($(stat -c '%a' "${HELPER_DST}") root:root)"
echo "Polkit: ${POLKIT_POLICY_DST}, ${POLKIT_RULE_DST}"
echo "Gruppe setuphelfer: $(getent group setuphelfer || echo fehlt)"
