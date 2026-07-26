#!/usr/bin/env bash
# Download + verify official Linux Mint control ISOs (A=22.1, B=22.3).
# Never remasters. Blocks on signature_failed / checksum_failed / source_untrusted.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CTRL="${1:-}"
MIRROR_BASE="${MINT_MIRROR_BASE:-https://mirrors.edge.kernel.org/linuxmint/stable}"
GPG_FPR="27DEB15644C6B3CF3BD7D291300F846BA25BAE09"

usage() {
  echo "Usage: $0 <control-a|control-b> [--download-iso]" >&2
  exit 2
}

[[ -n "$CTRL" ]] || usage
case "$CTRL" in
  control-a) REL=22.1; ISO=linuxmint-22.1-cinnamon-64bit.iso ;;
  control-b) REL=22.3; ISO=linuxmint-22.3-cinnamon-64bit.iso ;;
  *) usage ;;
esac

OUT="$ROOT/build/rescue/reference-images/$CTRL"
mkdir -p "$OUT"
cd "$OUT"

echo "SOURCE=$MIRROR_BASE/$REL/"
curl -fsSL -o sha256sum.txt "$MIRROR_BASE/$REL/sha256sum.txt"
curl -fsSL -o sha256sum.txt.gpg "$MIRROR_BASE/$REL/sha256sum.txt.gpg"

# Official mirrors only (override must still be kernel.org/linuxmint.com family).
case "$MIRROR_BASE" in
  https://mirrors.edge.kernel.org/linuxmint/stable|https://mirrors.kernel.org/linuxmint/stable|https://linuxmint-isos.mirrorservice.org/stable)
    ;;
  *)
    echo "BLOCKED: source_untrusted mirror=$MIRROR_BASE" >&2
    exit 16
    ;;
esac

STATUS="checksum_only"
SIG_OK=false
if command -v gpg >/dev/null 2>&1; then
  gpg --list-keys "$GPG_FPR" >/dev/null 2>&1 || \
    gpg --keyserver keyserver.ubuntu.com --recv-keys "$GPG_FPR"
  if gpg --verify sha256sum.txt.gpg sha256sum.txt 2>/tmp/gpg-verify-$$.txt; then
    if grep -q "Korrekte Signatur\|Good signature" /tmp/gpg-verify-$$.txt; then
      SIG_OK=true
      STATUS="verified_checksum_file"
    fi
  else
    STATUS="signature_failed"
    echo "BLOCKED: signature_failed" >&2
    cat /tmp/gpg-verify-$$.txt >&2 || true
    rm -f /tmp/gpg-verify-$$.txt
    exit 17
  fi
  rm -f /tmp/gpg-verify-$$.txt
fi

EXPECTED="$(awk -v f="$ISO" '$2 ~ f {print $1; exit}' sha256sum.txt)"
[[ -n "$EXPECTED" ]] || { echo "BLOCKED: ISO name not in sha256sum.txt" >&2; exit 18; }

ISO_STATUS="not_available"
if [[ "${2:-}" == "--download-iso" ]]; then
  curl -fL --continue-at - -o "$ISO" "$MIRROR_BASE/$REL/$ISO"
  GOT="$(sha256sum -b "$ISO" | awk '{print $1}')"
  if [[ "$GOT" != "$EXPECTED" ]]; then
    echo "BLOCKED: checksum_failed expected=$EXPECTED got=$GOT" >&2
    exit 19
  fi
  ISO_STATUS="verified"
  STATUS="verified"
else
  if [[ -f "$ISO" ]]; then
    GOT="$(sha256sum -b "$ISO" | awk '{print $1}')"
    if [[ "$GOT" != "$EXPECTED" ]]; then
      echo "BLOCKED: checksum_failed expected=$EXPECTED got=$GOT" >&2
      exit 19
    fi
    ISO_STATUS="verified"
    STATUS="verified"
  fi
fi

python3 - <<PY
import json, pathlib
p = pathlib.Path("verification.json")
data = {
  "control": "$CTRL",
  "release": "$REL",
  "iso": "$ISO",
  "expected_sha256": "$EXPECTED",
  "signature_verified": $( [[ "$SIG_OK" == "true" ]] && echo True || echo False ),
  "gpg_fingerprint": "$GPG_FPR",
  "mirror": "$MIRROR_BASE/$REL/",
  "iso_status": "$ISO_STATUS",
  "status": "$STATUS",
  "modified": False,
}
p.write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps(data, indent=2))
PY
