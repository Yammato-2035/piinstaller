#!/usr/bin/env bash
# Bootstrap local private monorepo from public skeleton (no fork).
# Usage: ./scripts/bootstrap-setuphelfer-private-repo.sh [target-dir]
# Optional: GITHUB_OWNER=Yammato-2035 gh repo create ...
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-${HOME}/setuphelfer-private}"
OWNER="${GITHUB_OWNER:-Yammato-2035}"
REPO_NAME="${PRIVATE_REPO_NAME:-setuphelfer-private}"
SKELETON="${ROOT}/docs/private-server-skeletons"

die() { echo "ERROR: $*" >&2; exit 1; }

[[ -d "$SKELETON" ]] || die "skeleton missing: $SKELETON"

if [[ -e "$TARGET" ]]; then
  die "target exists: $TARGET — remove or choose another path"
fi

mkdir -p "$TARGET"
cp -a "$SKELETON/." "$TARGET/"
cp "$SKELETON/gitignore.template" "$TARGET/.gitignore"
rm -f "$TARGET/gitignore.template"

cd "$TARGET"
git init -b main
git submodule add "https://github.com/${OWNER}/piinstaller.git" public-contracts 2>/dev/null || {
  echo "WARN: submodule add failed — run manually: git submodule add https://github.com/${OWNER}/piinstaller.git public-contracts"
}

cat > README.md <<EOF
# Setuphelfer Private

Generated from public piinstaller skeleton. **Private repository — no secrets in git.**

- \`public-contracts/\` — submodule to piinstaller (contracts)
- \`beta-registration-server/\` — port 8100 lab
- \`telemetry-server/\` — port 8101 lab
- \`diagnostics-server/\` — port 8102 lab

Lab: \`docker compose -f infra/docker-compose.lab.yml up\`
EOF

git add .
git commit -m "chore: bootstrap setuphelfer-private from public skeleton"

if command -v gh >/dev/null 2>&1; then
  echo "Creating private GitHub repo ${OWNER}/${REPO_NAME} ..."
  if gh repo create "${OWNER}/${REPO_NAME}" --private --source=. --remote=origin --push; then
    echo "Pushed to https://github.com/${OWNER}/${REPO_NAME}"
  else
    echo "gh repo create failed — push manually after creating empty private repo on GitHub"
  fi
else
  echo "gh not installed — create private repo on GitHub and:"
  echo "  git remote add origin https://github.com/${OWNER}/${REPO_NAME}.git"
  echo "  git push -u origin main"
fi

echo "Done: $TARGET"
