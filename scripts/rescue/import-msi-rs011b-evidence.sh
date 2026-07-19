#!/usr/bin/env bash
# PI-RS-MSI-AUTO-EVIDENCE-001 — Import anonymized MSI boot evidence for workspace + CSE preview.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CSE_ROOT="${SETUPHELFER_CSE_ROOT:-/home/volker/setuphelfer-cloudserver-edition}"
SOURCE="${1:-}"

resolve_source() {
  local candidate="" nested=""
  if [[ -n "$SOURCE" ]]; then
    candidate="$SOURCE"
  else
    for cand in /media/*/SETUP_LOGS /run/media/*/SETUP_LOGS; do
      if [[ -d "${cand}/setuphelfer/evidence/msi-rs011b" ]]; then
        candidate="$cand"
        break
      fi
    done
  fi
  [[ -n "$candidate" ]] || return 1
  if [[ "$(basename "$candidate")" == "msi-rs011b" && -d "$candidate" ]]; then
    printf '%s' "$candidate"
    return 0
  fi
  nested="${candidate}/setuphelfer/evidence/msi-rs011b"
  if [[ -d "$nested" ]]; then
    printf '%s' "$nested"
    return 0
  fi
  return 1
}

EV_SRC="$(resolve_source)" || {
  echo "ERROR: MSI evidence dir not found — pass SETUP_LOGS mount or msi-rs011b path" >&2
  exit 1
}

if [[ "${DRY_RESOLVE:-0}" == "1" ]]; then
  echo "$EV_SRC"
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
IMPORT_WS="${REPO_ROOT}/docs/evidence/pi_rs_msi_auto_evidence_001/imported-setup-logs"
IMPORT_CSE="${CSE_ROOT}/tests/fixtures/rescue_boot_evidence_preview"
mkdir -p "$IMPORT_WS" "$IMPORT_CSE"

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
import re
import shutil
from pathlib import Path

repo = Path(${REPO_ROOT@Q})
ev_src = Path(${EV_SRC@Q})
import_ws = Path(${IMPORT_WS@Q})
import_cse = Path(${IMPORT_CSE@Q})

ALLOWED = (
    "boot-summary.json",
    "boot-timeline.jsonl",
    "lab-auto-result.json",
    "collector-summary.json",
    "api-version.json",
    "rescue-health.json",
    "console-shield-state.json",
)
REDACT_PATTERNS = (
    (re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), "0.0.0.0"),
    (re.compile(r"\b[A-F0-9]{2}(?::[A-F0-9]{2}){5}\b", re.I), "00:00:00:00:00:00"),
    (re.compile(r"\b[a-z0-9-]{20,}\b"), "redacted-id"),
)

def redact_text(text: str) -> str:
    out = text
    for pattern, repl in REDACT_PATTERNS:
        out = pattern.sub(repl, out)
    return out

def redact_json(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    redacted = redact_text(raw)
    return json.loads(redacted)

copied = []
for name in ALLOWED:
    src = ev_src / name
    if not src.is_file():
        continue
    if name.endswith(".json"):
        data = redact_json(src)
        body = json.dumps(data, indent=2, ensure_ascii=False) + "\\n"
    else:
        body = redact_text(src.read_text(encoding="utf-8", errors="replace"))
        if not body.endswith("\\n"):
            body += "\\n"
    (import_ws / name).write_text(body, encoding="utf-8")
    (import_cse / name).write_text(body, encoding="utf-8")
    copied.append(name)

late_files = sorted(ev_src.glob("late-evidence-*.txt"))
if late_files:
    body = redact_text(late_files[-1].read_text(encoding="utf-8", errors="replace"))
    (import_ws / "late-evidence-latest.txt").write_text(body, encoding="utf-8")
    (import_cse / "late-evidence-latest.txt").write_text(body, encoding="utf-8")
    copied.append("late-evidence-latest.txt")

manifest = {
    "schema_version": 1,
    "import_id": "PI-RS-MSI-AUTO-EVIDENCE-001",
    "imported_at": ${STAMP@Q},
    "source_evidence_dir": str(ev_src),
    "files": copied,
    "preview_only": True,
    "raw_log_visible": False,
}
manifest_body = json.dumps(manifest, indent=2, ensure_ascii=False) + "\\n"
(import_ws / "import-manifest.json").write_text(manifest_body, encoding="utf-8")
(import_cse / "import-manifest.json").write_text(manifest_body, encoding="utf-8")
print(json.dumps({"imported_files": copied, "workspace": str(import_ws), "cse_fixture": str(import_cse)}))
PY

echo "Import complete -> ${IMPORT_WS}"
echo "CSE fixture -> ${IMPORT_CSE}"
