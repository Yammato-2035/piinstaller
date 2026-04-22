#!/usr/bin/env bash
# Im **Gast** ausführen (als beliebiger User): sucht tools/vm-test/scripts und gibt den
# absoluten Pfad zu einem Skript aus (Standard: in-guest-vmtest-postinstall.sh).
#
#   bash ~/…/in-guest-which-vmtest-script.sh
#   bash ~/…/in-guest-which-vmtest-script.sh in-guest-vmtest-autorun.sh
#
set -euo pipefail
NAME="${1:-in-guest-vmtest-postinstall.sh}"

candidates=(
  "${VMTEST_REPO_DIR:-$HOME/piinstaller-src}/tools/vm-test/scripts/$NAME"
  "$HOME/piinstaller/tools/vm-test/scripts/$NAME"
  "/opt/setuphelfer/tools/vm-test/scripts/$NAME"
)

for f in "${candidates[@]}"; do
  if [[ -f "$f" ]]; then
    echo "$f"
    exit 0
  fi
done

found="$(find "$HOME" -maxdepth 6 -type f -name "$NAME" 2>/dev/null | head -n1 || true)"
if [[ -n "$found" ]]; then
  echo "$found"
  exit 0
fi

echo "FEHLER: $NAME nicht gefunden." >&2
echo "Auf dem Host im Verzeichnis tools/vm-test ausführen:" >&2
echo "  SSH_KEY=… SSH_GUEST_SPEC=… ./scripts/sync-piinstaller-repo-to-guest.sh" >&2
echo "Dann erscheint das Repo typisch unter ~/piinstaller-src/." >&2
exit 1
