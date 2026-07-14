#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D — reproducible synthetic backup test data (512 MiB – 2 GiB target).
set -euo pipefail

TARGET_ROOT="${1:-/tmp/setuphelfer-e2e-testdata}"
MIN_FILES="${MIN_FILES:-250}"
MIN_DIRS="${MIN_DIRS:-20}"
TARGET_BYTES="${TARGET_BYTES:-536870912}"

mkdir -p "${TARGET_ROOT}"

echo "Erzeuge E2E-Testdaten unter: ${TARGET_ROOT}"
echo "Zielgröße (ca.): ${TARGET_BYTES} Bytes"

dir_count=0
file_count=0
total_bytes=0

_make_dir() {
  local rel="$1"
  mkdir -p "${TARGET_ROOT}/${rel}"
  dir_count=$((dir_count + 1))
}

_make_file() {
  local rel="$1"
  local size="$2"
  local path="${TARGET_ROOT}/${rel}"
  mkdir -p "$(dirname "${path}")"
  if command -v dd >/dev/null 2>&1; then
    dd if=/dev/urandom of="${path}" bs=4096 count=$(( (size + 4095) / 4096 )) status=none 2>/dev/null || true
    truncate -s "${size}" "${path}" 2>/dev/null || true
  else
    python3 - <<PY
from pathlib import Path
p = Path(${path@Q})
p.parent.mkdir(parents=True, exist_ok=True)
p.write_bytes((__import__("os").urandom(${size})))
PY
  fi
  file_count=$((file_count + 1))
  total_bytes=$((total_bytes + size))
}

# Verzeichnisstruktur
for i in $(seq 1 10); do
  _make_dir "level1/group_${i}"
  for j in $(seq 1 3); do
    _make_dir "level1/group_${i}/sub_${j}"
  done
done
_make_dir "unicode/äöü-测试-📁"
_make_dir "empty_dirs/only_empty"
_make_dir "nested/deep/a/b/c"

# Kleine Textdateien
for i in $(seq 1 80); do
  path="${TARGET_ROOT}/text/file_${i}.txt"
  mkdir -p "$(dirname "${path}")"
  printf 'setuphelfer-e2e-test-%s\n' "${i}" > "${path}"
  file_count=$((file_count + 1))
  total_bytes=$((total_bytes + $(stat -c%s "${path}" 2>/dev/null || echo 32)))
done

# Leere Dateien
mkdir -p "${TARGET_ROOT}/empty"
for i in $(seq 1 20); do
  : > "${TARGET_ROOT}/empty/empty_${i}.dat"
  file_count=$((file_count + 1))
done

# Unicode-Dateinamen
_make_file "unicode/äöü-测试-📁/データ_${RANDOM}.bin" 4096

# Mittelgroße Binärdateien bis Zielgröße
idx=0
while [[ "${total_bytes}" -lt "${TARGET_BYTES}" && "${file_count}" -lt 2000 ]]; do
  size=$((8192 + RANDOM * 128))
  _make_file "binary/bin_${idx}.dat" "${size}"
  idx=$((idx + 1))
done

# source-summary via Python (keine PII)
PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)/backend" python3 - <<PY
import json
from pathlib import Path
from core.rescue_physical_e2e_manifest import write_source_artifacts
root = Path(${TARGET_ROOT@Q})
summary = write_source_artifacts(
    root,
    manifest_path=root.parent / "source-manifest.sha256",
    summary_path=root.parent / "source-summary.json",
)
print(json.dumps(summary, indent=2))
PY

if [[ "${file_count}" -lt "${MIN_FILES}" ]]; then
  echo "WARN: file_count=${file_count} < ${MIN_FILES}" >&2
fi
if [[ "${dir_count}" -lt "${MIN_DIRS}" ]]; then
  echo "WARN: dir_count=${dir_count} < ${MIN_DIRS}" >&2
fi

echo "Fertig: files=${file_count} bytes=${total_bytes} dirs=${dir_count}"
