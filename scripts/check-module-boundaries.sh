#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
APP_FILE="${ROOT}/backend/app.py"

status="ok"
warnings=()

if [[ ! -f "${APP_FILE}" ]]; then
  echo '{"status":"blocked","error":"app.py_missing"}'
  exit 0
fi

line_count="$(wc -l < "${APP_FILE}" | tr -d ' ')"
include_router_count="$(python3 - <<'PY'
from pathlib import Path
txt = Path("backend/app.py").read_text(encoding="utf-8", errors="ignore")
print(txt.count("include_router("))
PY
)"

for token in "mkfs" " dd " "lb build" "debootstrap"; do
  if python3 - <<PY
from pathlib import Path
t = Path("${APP_FILE}").read_text(encoding="utf-8", errors="ignore").lower()
print("1" if "${token}".strip().lower() in t else "0")
PY
  then :; fi >/tmp/.boundary_tmp
  if [[ "$(cat /tmp/.boundary_tmp)" == "1" ]]; then
    warnings+=("token_in_app:${token}")
  fi
done
rm -f /tmp/.boundary_tmp

if [[ "${include_router_count}" -gt 25 ]]; then
  warnings+=("app_include_router_still_high:${include_router_count}")
fi
if [[ "${line_count}" -gt 3000 ]]; then
  warnings+=("app_line_count_high:${line_count}")
fi

if [[ -d "${ROOT}/backend/runtime_governance" ]]; then
  if rg -l 'backend\.app|from app import|import app' "${ROOT}/backend/runtime_governance" --glob '*.py' 2>/dev/null | grep -q .; then
    warnings+=("runtime_governance_imports_app")
  fi
fi

# Phase A.1: facade boundary warnings (warn-only, no block)
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  warnings+=("${line}")
done < <(python3 - "${ROOT}" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
backend = root / "backend"
if not backend.is_dir():
    raise SystemExit

LSBLK_ALLOW = {
    "backend/core/storage_facade.py",
    "backend/core/safe_device.py",
    "backend/modules/storage_detection.py",
    "backend/core/device_identity.py",
    "backend/core/rescue_hardstop.py",
    "backend/debug/support_bundle.py",
}
FINDMNT_ALLOW = {
    "backend/core/mount_facade.py",
    "backend/core/safe_device.py",
    "backend/modules/storage_detection.py",
    "backend/core/backup_target_auto_prepare.py",
    "backend/modules/inspect_storage.py",
    "backend/modules/rescue_restore_execute.py",
    "backend/core/rescue_hardstop.py",
}
BLKID_ALLOW = LSBLK_ALLOW | {
    "backend/core/rescue_fat32_esp_usb_verify.py",
    "backend/core/rescue_fat32_esp_usb_writer.py",
}
SAFETY_ALLOW = {
    "backend/core/safety_facade.py",
    "backend/core/safe_device.py",
    "backend/safety/write_guard.py",
    "backend/modules/storage_detection.py",
}
MIGRATED_SAFETY_CALLERS = {
    "backend/preflight/backup.py",
    "backend/modules/backup_engine.py",
    "backend/modules/restore_engine.py",
    "backend/core/partition_storage_facade.py",
    "backend/inspect/collector.py",
}
MIGRATED_STORAGE_CALLERS = {
    "backend/core/backup_target_auto_prepare.py",
    "backend/inspect/collector.py",
}

patterns = [
    (re.compile(r"subprocess\.(run|Popen)\([^)]*\blsblk\b", re.S), "facade_boundary_lsblk", LSBLK_ALLOW),
    (re.compile(r"subprocess\.(run|Popen)\([^)]*\bfindmnt\b", re.S), "facade_boundary_findmnt", FINDMNT_ALLOW),
    (re.compile(r"subprocess\.(run|Popen)\([^)]*\bblkid\b", re.S), "facade_boundary_blkid", BLKID_ALLOW),
    (re.compile(r"from core\.safe_device import .*validate_write_target|from core import safe_device"), "facade_boundary_safe_device", SAFETY_ALLOW),
    (re.compile(r"from safety\.write_guard import|from safety import write_guard"), "facade_boundary_write_guard", SAFETY_ALLOW),
]

warns: list[str] = []
for path in sorted(backend.rglob("*.py")):
    rel = path.relative_to(root).as_posix()
    if "/tests/" in rel or "/venv/" in rel or "/.venv/" in rel:
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for rx, label, allow in patterns:
        if rel in allow:
            continue
        if rx.search(text):
            if rel in MIGRATED_SAFETY_CALLERS and label in {
                "facade_boundary_safe_device",
                "facade_boundary_write_guard",
            }:
                warns.append(f"facade_boundary_migrated_caller_blocked:{rel}")
            elif rel in MIGRATED_STORAGE_CALLERS and label in {
                "facade_boundary_lsblk",
                "facade_boundary_findmnt",
                "facade_boundary_blkid",
            }:
                warns.append(f"facade_boundary_migrated_storage_blocked:{rel}")
            else:
                warns.append(f"{label}:{rel}")

for w in warns[:40]:
    print(w)
if len(warns) > 40:
    print(f"facade_boundary_truncated:{len(warns) - 40}_more")
PY
)

# Phase C.1: deploy runner registry warnings (warn-only)
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  warnings+=("${line}")
done < <(python3 - "${ROOT}" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
deploy = root / "backend" / "deploy"
registry_mod = deploy / "runner_registry.py"
runners = sorted(
    p for p in deploy.glob("runner_*.py")
    if p.name not in {
        "runner_registry.py",
        "runner_result_contract.py",
        "runner_api_facade.py",
        "runner_risk_gate.py",
    }
)
if runners and not registry_mod.is_file():
    print("runner_registry_missing:backend/deploy/runner_registry.py")
    raise SystemExit
if not registry_mod.is_file():
    raise SystemExit
sys.path.insert(0, str(root / "backend"))
from deploy.runner_registry import build_runner_registry_from_files, registry_policy_warnings

entries = build_runner_registry_from_files(root=deploy)
ids = {e.runner_id for e in entries}
for p in runners:
    if p.stem not in ids:
        print(f"runner_registry_missing:{p.relative_to(root).as_posix()}")
for w in registry_policy_warnings(entries)[:20]:
    print(w)
PY
)

# Phase C.2: runner result contract warnings (warn-only)
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  warnings+=("${line}")
done < <(python3 - "${ROOT}" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
deploy = root / "backend" / "deploy"
contract_mod = deploy / "runner_result_contract.py"
registry_mod = deploy / "runner_registry.py"
runners = sorted(
    p for p in deploy.glob("runner_*.py")
    if p.name not in {
        "runner_registry.py",
        "runner_result_contract.py",
        "runner_api_facade.py",
        "runner_risk_gate.py",
    }
)
if registry_mod.is_file() and not contract_mod.is_file():
    print("runner_result_contract_missing:backend/deploy/runner_result_contract.py")
    raise SystemExit
if not contract_mod.is_file():
    raise SystemExit
sys.path.insert(0, str(root / "backend"))
from deploy.runner_result_contract import scan_runner_file_result_warnings

seen: set[str] = set()
for p in runners:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for w in scan_runner_file_result_warnings(p, text):
        if w not in seen:
            seen.add(w)
            print(w)
        if len(seen) >= 40:
            break
    if len(seen) >= 40:
        break
PY
)

# Phase C.3: runner API facade warnings (warn-only)
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  warnings+=("${line}")
done < <(python3 - "${ROOT}" <<'PY'
import ast
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
deploy = root / "backend" / "deploy"
facade_mod = deploy / "runner_api_facade.py"
routes_mod = deploy / "routes.py"
allowed_facade_imports = {
    "deploy.runner_registry",
    "deploy.runner_result_contract",
    "deploy.runner_risk_gate",
}

if not facade_mod.is_file():
    print("runner_api_facade_missing:backend/deploy/runner_api_facade.py")
    raise SystemExit

tree = ast.parse(facade_mod.read_text(encoding="utf-8", errors="replace"))
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        if node.module.startswith("deploy.runner_") and node.module not in allowed_facade_imports:
            print(f"runner_api_facade_imports_runner_module:{node.module}")

if routes_mod.is_file():
    text = routes_mod.read_text(encoding="utf-8", errors="replace")
    if "runner_api_facade" not in text:
        print("runner_api_route_without_contract:backend/deploy/routes.py")
    for m in re.finditer(r'@router\.(get|post|put|patch|delete)\("(/runners[^"]*)"\)', text):
        verb, path = m.group(1), m.group(2)
        if verb != "get":
            print(f"runner_api_route_unsafe_verb_or_name:{verb}:{path}")
        lower = path.lower()
        for frag in ("execute", "apply", "install", "write", "delete"):
            if frag in lower:
                print(f"runner_api_route_unsafe_verb_or_name:{verb}:{path}")
PY
)

# Phase C.4: runner risk gate warnings (warn-only)
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  warnings+=("${line}")
done < <(python3 - "${ROOT}" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
deploy = root / "backend" / "deploy"
gate_mod = deploy / "runner_risk_gate.py"
facade_mod = deploy / "runner_api_facade.py"
allowed = {"deploy.runner_registry", "deploy.runner_result_contract"}

if facade_mod.is_file() and not gate_mod.is_file():
    print("runner_risk_gate_missing:backend/deploy/runner_risk_gate.py")
    raise SystemExit
if not gate_mod.is_file():
    raise SystemExit

tree = ast.parse(gate_mod.read_text(encoding="utf-8", errors="replace"))
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        if node.module.startswith("deploy.runner_") and node.module not in allowed:
            print(f"runner_risk_gate_imports_runner_module:{node.module}")

facade_text = facade_mod.read_text(encoding="utf-8", errors="replace")
if "runner_risk_gate" not in facade_text:
    print("runner_api_facade_missing_risk_gate:backend/deploy/runner_api_facade.py")
gate_src = gate_mod.read_text(encoding="utf-8", errors="replace")
if "allowed_to_execute = True" in gate_src.replace("_C4_EXECUTE_ALLOWED", ""):
    print("runner_risk_gate_execute_allowed_true:backend/deploy/runner_risk_gate.py")
PY
)

# Phase C.5: routes decoupling (warn-only)
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  warnings+=("${line}")
done < <(python3 - "${ROOT}" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
routes = root / "backend" / "deploy" / "routes.py"
if not routes.is_file():
    raise SystemExit
text = routes.read_text(encoding="utf-8", errors="replace")
imports = re.findall(r"^from deploy\.runner_[^\s]+ import", text, flags=re.M)
count = len(imports)
baseline_c5 = 113
baseline_c6 = 109
print(f"routes_direct_runner_import_count:{count}")
if count < baseline_c5:
    print(f"routes_direct_runner_import_reduced:{baseline_c5}_to_{count}")
if count < baseline_c6:
    print(f"routes_direct_runner_import_reduced_c6:{baseline_c6}_to_{count}")

decoupled = {
    "runner_next_phase_gate": "/runner/next-phase/gate",
    "runner_version_governance": "/version-governance/state",
    "runner_version_source_of_truth_check": "/version-source-of-truth-check",
    "runner_legacy_identifier_inventory": "/legacy-identifier-inventory",
    "runner_legacy_identifier_hotspot_analysis": "/legacy-identifier-hotspot-analysis",
    "runner_setuphelfer_identifier_consistency_check": "/setuphelfer-identifier-consistency-check",
    "runner_manual_runtime_evidence_timeline": "/runner/manual-runtime/evidence-timeline",
    "runner_manual_runtime_evidence_final_snapshot": "/runner/manual-runtime/evidence-final-snapshot",
    "runner_manual_runtime_validator_seal_index": "/runner/manual-runtime/result-validator-seal-index",
}
for rid, path_fragment in decoupled.items():
    if f"from deploy.{rid} import" in text:
        print(f"routes_runner_plan_only_without_facade:{rid}")
    if path_fragment in text and "build_plan_only_response" not in text:
        print(f"routes_runner_plan_only_without_facade:route{path_fragment}")

if re.search(r'@router\.post\("/runners/[^"]*(execute|apply|write|install|delete)', text):
    print("routes_runner_execute_without_risk_gate:unsafe_runners_post")

# Phase D.2: registry router extraction (warn-only)
registry_mod = root / "backend" / "deploy" / "routes_registry.py"
if not registry_mod.is_file():
    print("deploy_routes_registry_missing:backend/deploy/routes_registry.py")
else:
    reg = registry_mod.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^from deploy\.runner_[^\s]+ import", reg, flags=re.M):
        if "runner_api_facade" not in reg:
            print("deploy_routes_registry_has_runner_import:backend/deploy/routes_registry.py")
        for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", reg, flags=re.M):
            if m != "deploy.runner_api_facade":
                print(f"deploy_routes_registry_has_runner_import:{m}")
    if re.search(r"@router\.(post|put|delete|patch)\(", reg):
        print("deploy_routes_registry_has_non_get_route:backend/deploy/routes_registry.py")
    expected_paths = (
        '"/catalog"',
        '"/summary"',
        '"/policy-warnings"',
        '"/{runner_id}"',
        '"/{runner_id}/empty-result"',
    )
    for ep in expected_paths:
        if f"@router.get({ep})" not in reg.replace(" ", ""):
            if f'@router.get({ep})' not in reg:
                pass
    for ep in ('@router.get("/catalog")', '@router.get("/summary")', '@router.get("/policy-warnings")',
               '@router.get("/{runner_id}/empty-result")', '@router.get("/{runner_id}")'):
        if ep not in reg:
            print(f"deploy_routes_registry_path_changed:missing_{ep}")
    if "routes_registry" not in text or "include_router(deploy_registry_router)" not in text:
        print("deploy_routes_registry_not_included:backend/deploy/routes.py")
    if '@router.get("/runners/catalog")' in text:
        print("deploy_routes_registry_duplicate_in_routes:backend/deploy/routes.py")
PY
)

if [[ "${#warnings[@]}" -gt 0 ]]; then
  status="review_required"
fi

printf '{"status":"%s","line_count":%s,"include_router_count":%s,"warnings":[' "${status}" "${line_count}" "${include_router_count}"
for i in "${!warnings[@]}"; do
  [[ "${i}" -gt 0 ]] && printf ','
  printf '"%s"' "${warnings[$i]}"
done
printf ']}\n'
exit 0

# Legacy deep scan (optional): scripts/check-module-boundaries-deep.sh
#!/usr/bin/env bash
# Warn-only guard: duplicate module patterns before rescue stick growth.
# Exit 0 = no warnings; 1 = warnings (CI may enable later).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

warn=0
warn_msg() {
  echo "check-module-boundaries: WARNING: $*" >&2
  warn=1
}

# --- Canonical backup runner ---
while IFS= read -r -d '' f; do
  case "$f" in
    */tools/backup_runner.py) continue ;;
    */backup_runner.py) warn_msg "unexpected backup_runner: $f" ;;
  esac
done < <(find backend -path '*/venv/*' -prune -o -path '*/.venv/*' -prune -o -name 'backup_runner.py' -print0 2>/dev/null)

# --- Forbidden subprocess tar in rescue package (deploy runners exempt legacy) ---
if [[ -d backend/rescue ]]; then
  if rg -l 'subprocess\.(run|Popen).*\btar\b' backend/rescue --glob '*.py' 2>/dev/null | grep -q .; then
    warn_msg "subprocess tar in backend/rescue (use tools/backup_runner.py)"
  fi
fi

# --- lsblk/findmnt allowlist (core + legacy); warn on new usage elsewhere ---
LSBLK_ALLOW=(
  "backend/core/storage_facade.py"
  "backend/core/safe_device.py"
  "backend/modules/storage_detection.py"
  "backend/core/device_identity.py"
  "backend/core/rescue_hardstop.py"
  "backend/debug/support_bundle.py"
)
FINDMNT_ALLOW=(
  "backend/core/mount_facade.py"
  "backend/core/safe_device.py"
  "backend/modules/storage_detection.py"
  "backend/core/backup_target_auto_prepare.py"
  "backend/modules/inspect_storage.py"
  "backend/modules/rescue_restore_execute.py"
  "backend/core/rescue_hardstop.py"
)

is_allowed() {
  local file="$1"
  shift
  local allowed
  for allowed in "$@"; do
    if [[ "$file" == "$allowed" ]]; then
      return 0
    fi
  done
  return 1
}

scan_pattern() {
  local pattern="$1"
  local label="$2"
  shift 2
  local allow=("$@")
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if is_allowed "$f" "${allow[@]}"; then
      continue
    fi
    if rg -q "$pattern" "$f" 2>/dev/null; then
      warn_msg "$label in $f (use core.storage_facade / core.mount_facade)"
    fi
  done < <(
    rg -l "$pattern" backend/app.py backend/deploy backend/rescue backend/inspect --glob '*.py' 2>/dev/null || true
  )
}

scan_pattern 'subprocess\.(run|Popen).*\blsblk\b' "direct lsblk subprocess" "${LSBLK_ALLOW[@]}"
scan_pattern 'subprocess\.(run|Popen).*\bfindmnt\b' "direct findmnt subprocess" "${FINDMNT_ALLOW[@]}"

# mount/umount execution outside allowlist
MOUNT_EXEC_ALLOW=(
  "backend/core/mount_facade.py"
  "backend/core/backup_target_auto_prepare.py"
)
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if is_allowed "$f" "${MOUNT_EXEC_ALLOW[@]}"; then
    continue
  fi
  if rg -q "subprocess\.(run|Popen).*\b(mount|umount)\b" "$f" 2>/dev/null; then
    warn_msg "mount/umount subprocess in $f"
  fi
done < <(
  rg -l "subprocess\.(run|Popen).*\b(mount|umount)\b" backend/app.py backend/deploy backend/rescue --glob '*.py' 2>/dev/null || true
)

# Required architecture docs
for doc in \
  docs/architecture/MONOLITH_BOUNDARY_AUDIT_2026-05-20.md \
  docs/architecture/MODULE_BOUNDARIES_TARGET_2026-05-20.md \
  docs/architecture/NO_DUPLICATE_MODULE_RULES.md \
  docs/architecture/MODULE_FREEZE_REGISTER_2026-05-20.md \
  docs/architecture/CORE_STORAGE_MOUNT_FACADES_2026-05-20.md \
  docs/rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md; do
  if [[ ! -f "$ROOT/$doc" ]]; then
    warn_msg "missing required doc: $doc"
  fi
done

for mod in backend/core/storage_facade.py backend/core/mount_facade.py; do
  if [[ ! -f "$ROOT/$mod" ]]; then
    warn_msg "missing facade module: $mod"
  fi
done

if [[ "$warn" -ne 0 ]]; then
  echo "check-module-boundaries: finished with warnings (see docs/architecture/NO_DUPLICATE_MODULE_RULES.md)" >&2
  exit 1
fi

echo "check-module-boundaries: OK"
exit 0
