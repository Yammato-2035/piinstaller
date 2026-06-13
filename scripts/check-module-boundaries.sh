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

# Phase D.3: risk-gate router extraction (warn-only)
risk_gate_mod = root / "backend" / "deploy" / "routes_risk_gate.py"
if not risk_gate_mod.is_file():
    print("deploy_routes_risk_gate_missing:backend/deploy/routes_risk_gate.py")
else:
    rg = risk_gate_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", rg, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_risk_gate_has_runner_import:{m}")
    if re.search(r"@router\.(post|put|delete|patch)\(", rg):
        print("deploy_routes_risk_gate_has_non_get_route:backend/deploy/routes_risk_gate.py")
    for ep in (
        '@router.get("/risk-gate/summary")',
        '@router.get("/risk-gate/operator-required")',
        '@router.get("/risk-gate/never-auto")',
        '@router.get("/risk-gate/plan-allowed")',
        '@router.get("/{runner_id}/risk-gate")',
    ):
        if ep not in rg:
            print(f"deploy_routes_risk_gate_path_changed:missing_{ep}")
    if "allowed_to_execute = True" in rg.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_risk_gate_execute_enabled:backend/deploy/routes_risk_gate.py")
    if "routes_risk_gate" not in text or "include_router(deploy_risk_gate_router)" not in text:
        print("deploy_routes_risk_gate_not_included:backend/deploy/routes.py")
    if '@router.get("/runners/risk-gate/summary")' in text:
        print("deploy_routes_risk_gate_duplicate_in_routes:backend/deploy/routes.py")

# Phase D.4: evidence router extraction (warn-only)
evidence_mod = root / "backend" / "deploy" / "routes_evidence.py"
if not evidence_mod.is_file():
    print("deploy_routes_evidence_missing:backend/deploy/routes_evidence.py")
else:
    ev = evidence_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", ev, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_evidence_has_runner_import:{m}")
    if re.search(r'@router\.post\("[^"]*(execute|apply|write|install|delete)', ev):
        print("deploy_routes_evidence_has_execute_route:backend/deploy/routes_evidence.py")
    if "allowed_to_execute = True" in ev.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_evidence_allowed_execute_true:backend/deploy/routes_evidence.py")
    for ep in (
        '@router.post("/legacy-identifier-inventory")',
        '@router.post("/legacy-identifier-hotspot-analysis")',
        '@router.post("/setuphelfer-identifier-consistency-check")',
        '@router.post("/runner/manual-runtime/result-validator-seal-index")',
        '@router.post("/runner/manual-runtime/evidence-timeline")',
        '@router.post("/runner/manual-runtime/evidence-final-snapshot")',
        '@router.post("/legacy-identifier-cleanup-classification")',
        '@router.post("/legacy-runtime-compatibility-inventory")',
        '@router.post("/legacy-runtime-coexistence-analysis")',
        '@router.post("/runner/manual-runtime/failure-test-results")',
        '@router.post("/runner/manual-runtime/failure-result-evaluation")',
        '@router.post("/runner/manual-runtime/result-validator-seal-consistency-audit")',
    ):
        if ep not in ev:
            print(f"deploy_routes_evidence_path_changed:missing_{ep}")
    if "routes_evidence" not in text or "include_router(deploy_evidence_router)" not in text:
        print("deploy_routes_evidence_not_included:backend/deploy/routes.py")
    for dup in (
        '@router.post("/legacy-identifier-inventory")',
        '@router.post("/legacy-identifier-cleanup-classification")',
        '@router.post("/legacy-runtime-compatibility-inventory")',
        '@router.post("/runner/manual-runtime/failure-test-results")',
    ):
        if dup in text:
            print("deploy_routes_evidence_duplicate_in_routes:backend/deploy/routes.py")
            break

# Phase D.5: governance router extraction (warn-only)
governance_mod = root / "backend" / "deploy" / "routes_governance.py"
if not governance_mod.is_file():
    print("deploy_routes_governance_missing:backend/deploy/routes_governance.py")
else:
    gv = governance_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", gv, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_governance_has_runner_import:{m}")
    if re.search(r'@router\.post\("[^"]*(execute|apply|write|install|delete)', gv):
        print("deploy_routes_governance_has_execute_route:backend/deploy/routes_governance.py")
    if "allowed_to_execute = True" in gv.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_governance_allowed_execute_true:backend/deploy/routes_governance.py")
    for ep in (
        '@router.post("/runner/next-phase/gate")',
        '@router.post("/version-governance/state")',
        '@router.post("/version-source-of-truth-check")',
    ):
        if ep not in gv:
            print(f"deploy_routes_governance_path_changed:missing_{ep}")
    if "routes_governance" not in text or "include_router(deploy_governance_router)" not in text:
        print("deploy_routes_governance_not_included:backend/deploy/routes.py")
    if '@router.post("/runner/next-phase/gate")' in text and "build_plan_only_response" in text:
        print("deploy_routes_governance_duplicate_in_routes:backend/deploy/routes.py")

# Phase D.8: diagnostics router extraction (warn-only)
diagnostics_mod = root / "backend" / "deploy" / "routes_diagnostics.py"
if not diagnostics_mod.is_file():
    print("deploy_routes_diagnostics_missing:backend/deploy/routes_diagnostics.py")
else:
    dg = diagnostics_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", dg, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_diagnostics_has_runner_import:{m}")
    if re.search(r'@router\.post\("[^"]*(execute|apply|write|install|delete)', dg):
        print("deploy_routes_diagnostics_has_execute_route:backend/deploy/routes_diagnostics.py")
    if "allowed_to_execute = True" in dg.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_diagnostics_allowed_execute_true:backend/deploy/routes_diagnostics.py")
    for ep in (
        '@router.post("/runner/manual-runtime/failure-injection-matrix")',
        '@router.post("/runner/manual-runtime/failure-execution-preview")',
        '@router.post("/runner/manual-runtime/failure-operator-checklists")',
        '@router.post("/runner/manual-runtime/failure-test-sessions")',
        '@router.post("/runner/manual-runtime/failure-readiness-gate")',
        '@router.post("/runtime-identifier-zero-state-verification")',
    ):
        if ep not in dg:
            print(f"deploy_routes_diagnostics_path_changed:missing_{ep}")
    if "routes_diagnostics" not in text or "include_router(deploy_diagnostics_router)" not in text:
        print("deploy_routes_diagnostics_not_included:backend/deploy/routes.py")
    for dup in (
        '@router.post("/runner/manual-runtime/failure-readiness-gate")',
        '@router.post("/runtime-identifier-zero-state-verification")',
    ):
        if dup in text:
            print("deploy_routes_diagnostics_duplicate_in_routes:backend/deploy/routes.py")
            break

# Phase D.9: notifications router evaluation (warn-only)
notifications_mod = root / "backend" / "deploy" / "routes_notifications.py"
if notifications_mod.is_file():
    nt = notifications_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", nt, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_notifications_has_runner_import:{m}")
    if re.search(r"\b(smtp|send_mail|sendmail|smtplib)\b", nt, flags=re.I):
        print("deploy_routes_notifications_sends_email:backend/deploy/routes_notifications.py")
    if re.search(r"\b(emit_event|publish_event|trigger_queue|enqueue)\b", nt, flags=re.I):
        print("deploy_routes_notifications_emits_event:backend/deploy/routes_notifications.py")
    if re.search(r"\b(queue\.put|celery|rq\.enqueue)\b", nt, flags=re.I):
        print("deploy_routes_notifications_triggers_queue:backend/deploy/routes_notifications.py")
    if re.search(r'@router\.post\("[^"]*(execute|apply|write|install|delete)', nt):
        print("deploy_routes_notifications_has_execute_route:backend/deploy/routes_notifications.py")
    if "allowed_to_execute = True" in nt.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_notifications_allowed_execute_true:backend/deploy/routes_notifications.py")
else:
    print("deploy_routes_notifications_skipped_d9:no_safe_slice")

# Phase D.10: versioning router (warn-only)
versioning_mod = root / "backend" / "deploy" / "routes_versioning.py"
if not versioning_mod.is_file():
    print("deploy_routes_versioning_missing:backend/deploy/routes_versioning.py")
else:
    vg = versioning_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", vg, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_versioning_has_runner_import:{m}")
    if re.search(r'@router\.post\("[^"]*apply', vg):
        print("deploy_routes_versioning_has_apply_route:backend/deploy/routes_versioning.py")
    if re.search(r'@router\.post\("[^"]*rewrite-apply', vg) or re.search(
        r'@router\.post\("[^"]*controlled-rewrite', vg
    ):
        print("deploy_routes_versioning_has_rewrite_route:backend/deploy/routes_versioning.py")
    unsafe_vg = re.findall(r'@router\.post\("([^"]+)"\)', vg)
    for p in unsafe_vg:
        pl = p.lower()
        if pl == "/setuphelfer-safe-rewrite-plan":
            continue
        if any(x in pl for x in ("execute", "apply", "install", "delete")):
            print("deploy_routes_versioning_has_execute_route:backend/deploy/routes_versioning.py")
            break
        if "/write" in pl or pl.endswith("-write"):
            print("deploy_routes_versioning_has_execute_route:backend/deploy/routes_versioning.py")
            break
    if "allowed_to_execute = True" in vg.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_versioning_allowed_execute_true:backend/deploy/routes_versioning.py")
    for ep in (
        '@router.post("/setuphelfer-runtime-identifier-migration")',
        '@router.post("/setuphelfer-safe-rewrite-plan")',
        '@router.post("/runtime-identifier-elimination-targets")',
        '@router.post("/legacy-upgrade-path-matrix")',
    ):
        if ep not in vg:
            print(f"deploy_routes_versioning_path_changed:missing_{ep}")
    if "routes_versioning" not in text or "include_router(deploy_versioning_router)" not in text:
        print("deploy_routes_versioning_not_included:backend/deploy/routes.py")
    for dup in (
        '@router.post("/setuphelfer-runtime-identifier-migration")',
        '@router.post("/legacy-upgrade-path-matrix")',
    ):
        if dup in text:
            print("deploy_routes_versioning_duplicate_in_routes:backend/deploy/routes.py")
            break

# Phase D.11: runtime router (warn-only)
runtime_mod = root / "backend" / "deploy" / "routes_runtime.py"
if not runtime_mod.is_file():
    print("deploy_routes_runtime_missing:backend/deploy/routes_runtime.py")
else:
    rt = runtime_mod.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r"^from (deploy\.runner_[^\s]+) import", rt, flags=re.M):
        if m != "deploy.runner_api_facade":
            print(f"deploy_routes_runtime_has_runner_import:{m}")
    if re.search(r"\bsystemctl\b", rt):
        print("deploy_routes_runtime_uses_systemctl:backend/deploy/routes_runtime.py")
    if re.search(r"\bsudo\b", rt, flags=re.I):
        print("deploy_routes_runtime_uses_sudo:backend/deploy/routes_runtime.py")
    if re.search(r'@router\.post\("[^"]*apply', rt):
        print("deploy_routes_runtime_has_apply_route:backend/deploy/routes_runtime.py")
    if re.search(r'@router\.post\("[^"]*restart', rt):
        print("deploy_routes_runtime_has_restart_route:backend/deploy/routes_runtime.py")
    unsafe_rt = re.findall(r'@router\.post\("([^"]+)"\)', rt)
    for p in unsafe_rt:
        pl = p.lower()
        if any(x in pl for x in ("execute", "apply", "install", "delete", "restart", "deploy-to")):
            print("deploy_routes_runtime_has_execute_route:backend/deploy/routes_runtime.py")
            break
        if "/write" in pl or pl.endswith("-write"):
            print("deploy_routes_runtime_has_execute_route:backend/deploy/routes_runtime.py")
            break
    if "allowed_to_execute = True" in rt.replace("_C4_EXECUTE_ALLOWED", ""):
        print("deploy_routes_runtime_allowed_execute_true:backend/deploy/routes_runtime.py")
    for ep in (
        '@router.post("/runner/lab-readiness/status")',
        '@router.post("/runner/runtime-runbook/bundle")',
        '@router.post("/runner/lab-phase/consolidation")',
    ):
        if ep not in rt:
            print(f"deploy_routes_runtime_path_changed:missing_{ep}")
    if "routes_runtime" not in text or "include_router(deploy_runtime_router)" not in text:
        print("deploy_routes_runtime_not_included:backend/deploy/routes.py")
    for dup in (
        '@router.post("/runner/lab-readiness/status")',
        '@router.post("/runner/runtime-runbook/bundle")',
    ):
        if dup in text:
            print("deploy_routes_runtime_duplicate_in_routes:backend/deploy/routes.py")
            break

# Phase D.6: thin orchestrator guard (warn-only)
deploy_routes = root / "backend" / "deploy" / "routes.py"
if deploy_routes.is_file():
    dr_text = deploy_routes.read_text(encoding="utf-8", errors="replace")
    dr_lines = dr_text.count("\n") + (1 if dr_text and not dr_text.endswith("\n") else 0)
    dr_runner_imports = len(re.findall(r"^from deploy\.runner_", dr_text, flags=re.M))
    baseline_d6_lines = 4821
    baseline_d6_imports = 103
    baseline_d7_lines = 4671
    baseline_d7_imports = 99
    baseline_d8_lines = 4523
    baseline_d8_imports = 93
    baseline_d10_lines = 4324
    baseline_d10_imports = 89
    baseline_d11_lines = 4120
    baseline_d11_imports = 81
    if dr_lines > 2000:
        print(f"deploy_routes_py_too_large:{dr_lines}")
    print(f"deploy_routes_direct_runner_import_count:{dr_runner_imports}")
    if dr_runner_imports > baseline_d6_imports:
        print(f"deploy_routes_new_runner_import_detected:{baseline_d6_imports}_to_{dr_runner_imports}")
    if dr_runner_imports < baseline_d6_imports:
        print(f"deploy_routes_direct_runner_import_reduced_d7:{baseline_d6_imports}_to_{dr_runner_imports}")
    if dr_lines < baseline_d6_lines:
        print(f"deploy_routes_line_count_reduced_d7:{baseline_d6_lines}_to_{dr_lines}")
    if dr_runner_imports < baseline_d7_imports:
        print(f"deploy_routes_direct_runner_import_reduced_d8:{baseline_d7_imports}_to_{dr_runner_imports}")
    if dr_lines < baseline_d7_lines:
        print(f"deploy_routes_line_count_reduced_d8:{baseline_d7_lines}_to_{dr_lines}")
    for sub in (
        "routes_registry.py",
        "routes_risk_gate.py",
        "routes_evidence.py",
        "routes_governance.py",
        "routes_diagnostics.py",
        "routes_versioning.py",
        "routes_runtime.py",
    ):
        if not (root / "backend" / "deploy" / sub).is_file():
            print(f"deploy_routes_subrouter_missing:{sub}")
    if "include_router(deploy_registry_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_registry")
    if "include_router(deploy_risk_gate_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_risk_gate")
    if "include_router(deploy_evidence_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_evidence")
    if "include_router(deploy_governance_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_governance")
    if "include_router(deploy_diagnostics_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_diagnostics")
    if "include_router(deploy_versioning_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_versioning")
    if dr_runner_imports < baseline_d10_imports:
        print(f"deploy_routes_direct_runner_import_reduced_d10:{baseline_d10_imports}_to_{dr_runner_imports}")
    if dr_lines < baseline_d10_lines:
        print(f"deploy_routes_line_count_reduced_d10:{baseline_d10_lines}_to_{dr_lines}")
    if "include_router(deploy_runtime_router)" not in dr_text:
        print("deploy_routes_subrouter_missing:include_runtime")
    if dr_runner_imports < baseline_d11_imports:
        print(f"deploy_routes_direct_runner_import_reduced_d11:{baseline_d11_imports}_to_{dr_runner_imports}")
    if dr_lines < baseline_d11_lines:
        print(f"deploy_routes_line_count_reduced_d11:{baseline_d11_lines}_to_{dr_lines}")
    if re.search(r"\bsubprocess\b", dr_text) or re.search(r"\bos\.system\b", dr_text):
        print("deploy_routes_business_logic_new:subprocess_or_os_system")
    if re.search(r'@router\.post\("/runners/[^"]*(execute|apply|write|install|delete)', dr_text):
        print("deploy_routes_execute_without_risk_gate:unsafe_runners_post")
    if "build_plan_only_response" in dr_text:
        print("deploy_routes_business_logic_new:facade_in_main_routes")

# Phase M.1: module catalog guard (warn-only)
catalog_docs = (
    root / "docs" / "architecture" / "MODULE_CATALOG.md",
    root / "docs" / "architecture" / "FUNCTION_OWNERSHIP_MATRIX.md",
    root / "docs" / "architecture" / "DO_NOT_DUPLICATE_RULES.md",
)
for doc in catalog_docs:
    if not doc.is_file():
        print(f"module_catalog_missing:{doc.relative_to(root).as_posix()}")

backend = root / "backend"
if backend.is_dir():
    lsblk_allow = {
        "backend/core/storage_facade.py",
        "backend/core/safe_device.py",
        "backend/modules/storage_detection.py",
        "backend/core/device_identity.py",
        "backend/core/rescue_hardstop.py",
        "backend/debug/support_bundle.py",
    }
    findmnt_allow = lsblk_allow | {
        "backend/core/mount_facade.py",
        "backend/core/backup_target_auto_prepare.py",
        "backend/modules/inspect_storage.py",
        "backend/modules/rescue_restore_execute.py",
    }
    blkid_allow = lsblk_allow | {
        "backend/core/rescue_fat32_esp_usb_verify.py",
        "backend/core/rescue_fat32_esp_usb_writer.py",
    }
    safety_allow = {
        "backend/core/safety_facade.py",
        "backend/core/safe_device.py",
        "backend/safety/write_guard.py",
        "backend/modules/storage_detection.py",
    }
    mount_allow = {
        "backend/core/mount_facade.py",
        "backend/core/backup_target_auto_prepare.py",
    }
    risk_allow = {
        "backend/deploy/runner_risk_gate.py",
        "backend/deploy/runner_api_facade.py",
        "backend/deploy/runner_registry.py",
    }
    status_allow = {
        "backend/deploy/runner_result_contract.py",
        "backend/deploy/runner_registry.py",
    }
    storage_discovery_hits: list[str] = []
    lsblk_hits: list[str] = []
    findmnt_hits: list[str] = []
    blkid_hits: list[str] = []
    write_val_hits: list[str] = []
    mount_hits: list[str] = []
    status_hits: list[str] = []
    risk_hits: list[str] = []
    for path in sorted(backend.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if "/tests/" in rel or "/venv/" in rel or "/.venv/" in rel:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if rel not in lsblk_allow and re.search(r"\blsblk\b", text) and "subprocess" in text:
            lsblk_hits.append(rel)
        if rel not in findmnt_allow and re.search(r"\bfindmnt\b", text) and "subprocess" in text:
            findmnt_hits.append(rel)
        if rel not in blkid_allow and re.search(r"\bblkid\b", text) and "subprocess" in text:
            blkid_hits.append(rel)
        if rel not in safety_allow and "validate_write_target" in text and "safety_facade" not in text:
            if "from core.safety_facade" not in text and rel != "backend/core/safety_facade.py":
                write_val_hits.append(rel)
        if rel not in mount_allow and "build_readonly_mount_plan" in text and rel != "backend/core/mount_facade.py":
            mount_hits.append(rel)
        if rel not in status_allow and re.search(r'["\']status["\']\s*:\s*["\']', text) and rel.startswith("backend/deploy/runner_"):
            if "runner_result_contract" not in text:
                status_hits.append(rel)
        if rel not in risk_allow and "allowed_to_execute" in text and rel.startswith("backend/deploy/runner_"):
            if "runner_risk_gate" not in text and "runner_api_facade" not in text:
                risk_hits.append(rel)
        if rel not in lsblk_allow and "collect_inspect_storage_bundle" not in text:
            if "storage_detection" in rel or ("detect_block_devices" in text and "storage_facade" not in text):
                if rel not in {"backend/modules/storage_detection.py"}:
                    storage_discovery_hits.append(rel)
    if storage_discovery_hits:
        print(f"duplicate_storage_discovery_detected:{len(storage_discovery_hits)}")
    if lsblk_hits:
        print(f"duplicate_lsblk_usage_detected:{len(lsblk_hits)}")
    if findmnt_hits:
        print(f"duplicate_findmnt_usage_detected:{len(findmnt_hits)}")
    if blkid_hits:
        print(f"duplicate_blkid_usage_detected:{len(blkid_hits)}")
    if write_val_hits:
        print(f"duplicate_write_target_validation_detected:{len(write_val_hits)}")
    if mount_hits:
        print(f"duplicate_mount_logic_detected:{len(mount_hits)}")
    if status_hits[:5]:
        print(f"duplicate_runner_result_status_detected:{len(status_hits)}")
    if risk_hits[:5]:
        print(f"duplicate_runner_risk_logic_detected:{len(risk_hits)}")

# Phase E.1–E.6: app.py router slices (warn-only)
app_py_path = root / "backend" / "app.py"
app_router_modules = {
    "health.py": root / "backend" / "api" / "routes" / "health.py",
    "version.py": root / "backend" / "api" / "routes" / "version.py",
    "settings.py": root / "backend" / "api" / "routes" / "settings.py",
    "status.py": root / "backend" / "api" / "routes" / "status.py",
    "capabilities.py": root / "backend" / "api" / "routes" / "capabilities.py",
    "catalog.py": root / "backend" / "api" / "routes" / "catalog.py",
    "dev_dashboard_readonly.py": root / "backend" / "api" / "routes" / "dev_dashboard_readonly.py",
    "dev_dashboard_roadmap.py": root / "backend" / "api" / "routes" / "dev_dashboard_roadmap.py",
}
e1_slice_endpoints = {
    "health.py": (
        '@router.get("/health")',
        '@router.get("/api/init/status")',
        '@router.get("/api/logs/path")',
    ),
    "version.py": ('@router.get("/api/version")',),
}
e2_slice_endpoints = {
    "settings.py": (
        '@router.get("/api/settings")',
        '@router.get("/api/settings/notifications/email")',
    ),
    "status.py": (
        '@router.get("/api/presets/list")',
        '@router.get("/api/debug/routes")',
        '@router.get("/api/user-profile")',
    ),
}
e3_slice_endpoints = {
    "health.py": ('@router.get("/api/logs/tail")',),
    "status.py": ('@router.get("/api/self-update/status")',),
    "catalog.py": ('@router.get("/api/apps")',),
    "capabilities.py": (
        '@router.get("/api/dev-dashboard/capability-status")',
        '@router.get("/api/dev-dashboard/compact-status")',
    ),
}
e4_slice_endpoints = {
    "dev_dashboard_readonly.py": (
        '@router.get("/api/dev-dashboard/modules")',
        '@router.get("/api/dev-dashboard/modules/{module_id}")',
        '@router.get("/api/dev-dashboard/evidence-index")',
        '@router.get("/api/dev-dashboard/manual-command-runs")',
        '@router.get("/api/dev-dashboard/recent-evidence")',
    ),
}
e5_slice_endpoints = {
    "dev_dashboard_roadmap.py": (
        '@router.get("/api/dev-dashboard/roadmap/areas")',
        '@router.get("/api/dev-dashboard/roadmap/milestones")',
        '@router.get("/api/dev-dashboard/roadmap/blockers")',
        '@router.get("/api/dev-dashboard/roadmap/decisions")',
        '@router.get("/api/dev-dashboard/roadmap/next-prompt")',
    ),
}
e6_slice_endpoints = {
    "dev_dashboard_roadmap.py": (
        '@router.get("/api/dev-dashboard/roadmap/next-prompts")',
        '@router.get("/api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}")',
    ),
}
e8_slice_endpoints = {
    "dev_dashboard_readonly.py": (
        '@router.get("/api/dev-dashboard/backend-health")',
        '@router.get("/api/dev-dashboard/notifications/status")',
        '@router.get("/api/dev-dashboard/notifications/events")',
    ),
}
for sub, mod in app_router_modules.items():
    if not mod.is_file():
        print(f"app_router_slice_missing:backend/api/routes/{sub}")
for mod in app_router_modules.values():
    if not mod.is_file():
        continue
    mt = mod.read_text(encoding="utf-8", errors="replace")
    rel = mod.relative_to(root).as_posix()
    if re.search(r"\bsubprocess\b", mt) or re.search(r"\bsystemctl\b", mt):
        print(f"app_py_new_subprocess:{rel}")
    if re.search(r"\bsudo\b", mt, flags=re.I):
        print(f"app_router_slice_uses_sudo:{rel}")
    if re.search(r"\blsblk\b|\bblkid\b", mt) and "storage_facade" not in mt:
        print(f"app_py_new_storage_duplicate:{rel}")
    if re.search(r"validate_write_target|write_guard", mt) and "safety_facade" not in mt:
        print(f"app_py_new_safety_duplicate:{rel}")
    if re.search(r"\bfindmnt\b", mt) and "mount_facade" not in mt:
        print(f"app_py_new_mount_duplicate:{rel}")
    if re.search(r"\bos\.walk\b|\.rglob\(", mt) and "dev_dashboard" not in mt and "core." not in mt:
        print(f"app_new_file_scanner_without_core_owner:{rel}")
    if (
        rel.endswith("dev_dashboard_roadmap.py")
        and "load_roadmap_registry_bundle" not in mt
    ) or (
        "dev_dashboard_roadmap" not in mt
        and re.search(r"setuphelfer_roadmap\.json|ROADMAP_FILE", mt)
        and "load_roadmap_registry_bundle" not in mt
    ):
        print(f"app_new_roadmap_parser_without_core_owner:{rel}")
    if "dev_dashboard_roadmap.py" in rel and re.search(r"build_dashboard_status", mt):
        print(f"app_roadmap_router_uses_dashboard_aggregation:{rel}")
    if rel.endswith("dev_dashboard_readonly.py"):
        if re.search(r"def build_notification_summary|def list_notification_events", mt):
            print(f"app_notification_router_new_state_logic:{rel}")
        if re.search(r"emit_notification_event", mt):
            print(f"app_notification_router_new_state_logic:{rel}")
if app_py_path.is_file():
    ap = app_py_path.read_text(encoding="utf-8", errors="replace")
    ap_lines = ap.count("\n") + (1 if ap and not ap.endswith("\n") else 0)
    baseline_e1_lines = 17857
    baseline_e2_lines = 17779
    baseline_e3_lines = 17699
    baseline_e4_lines = 17617
    baseline_e5_lines = 17568
    baseline_e6_lines = 17499
    baseline_e7_lines = 17472
    route_decorators = len(re.findall(r"@app\.(get|post|put|delete|patch)\(", ap))
    baseline_e1_routes = 213
    baseline_e2_routes = 209
    baseline_e3_routes = 204
    baseline_e4_routes = 199
    baseline_e5_routes = 194
    baseline_e6_routes = 189
    baseline_e7_routes = 187
    if ap_lines > 3000:
        print(f"app_py_too_large:{ap_lines}")
    print(f"app_py_route_count:{route_decorators}")
    if route_decorators >= baseline_e1_routes:
        print(f"app_py_route_count_not_reduced:{baseline_e1_routes}_still_{route_decorators}")
    if ap_lines >= baseline_e1_lines:
        print(f"app_py_line_count_not_reduced_e1:{baseline_e1_lines}_still_{ap_lines}")
    else:
        print(f"app_py_line_count_reduced_e1:{baseline_e1_lines}_to_{ap_lines}")
    if route_decorators < baseline_e2_routes:
        print(f"app_py_route_count_reduced_e2:{baseline_e2_routes}_to_{route_decorators}")
    if ap_lines < baseline_e2_lines:
        print(f"app_py_line_count_reduced_e2:{baseline_e2_lines}_to_{ap_lines}")
    if route_decorators < baseline_e3_routes:
        print(f"app_py_route_count_reduced_e3:{baseline_e3_routes}_to_{route_decorators}")
    if ap_lines < baseline_e3_lines:
        print(f"app_py_line_count_reduced_e3:{baseline_e3_lines}_to_{ap_lines}")
    if route_decorators < baseline_e4_routes:
        print(f"app_py_route_count_reduced_e4:{baseline_e4_routes}_to_{route_decorators}")
    if ap_lines < baseline_e4_lines:
        print(f"app_py_line_count_reduced_e4:{baseline_e4_lines}_to_{ap_lines}")
    if route_decorators < baseline_e5_routes:
        print(f"app_py_route_count_reduced_e5:{baseline_e5_routes}_to_{route_decorators}")
    if ap_lines < baseline_e5_lines:
        print(f"app_py_line_count_reduced_e5:{baseline_e5_lines}_to_{ap_lines}")
    if route_decorators < baseline_e6_routes:
        print(f"app_py_route_count_reduced_e6:{baseline_e6_routes}_to_{route_decorators}")
    if ap_lines < baseline_e6_lines:
        print(f"app_py_line_count_reduced_e6:{baseline_e6_lines}_to_{ap_lines}")
    if route_decorators < baseline_e7_routes:
        print(f"app_py_route_count_reduced_e7:{baseline_e7_routes}_to_{route_decorators}")
    if ap_lines < baseline_e7_lines:
        print(f"app_py_line_count_reduced_e7:{baseline_e7_lines}_to_{ap_lines}")
    if "include_router(health_router)" not in ap or "include_router(version_router)" not in ap:
        print("app_router_slice_e1_not_included:backend/app.py")
    if "include_router(settings_router)" not in ap or "include_router(status_router)" not in ap:
        print("app_router_slice_e2_not_included:backend/app.py")
    if "include_router(capabilities_router)" not in ap or "include_router(catalog_router)" not in ap:
        print("app_router_slice_e3_not_included:backend/app.py")
    if "include_router(dev_dashboard_readonly_router)" not in ap:
        print("app_router_slice_e4_not_included:backend/app.py")
    if "include_router(dev_dashboard_roadmap_router)" not in ap:
        print("app_router_slice_e5_not_included:backend/app.py")
    for dup in (
        '@app.get("/health")',
        '@app.get("/api/version")',
        '@app.get("/api/init/status")',
        '@app.get("/api/logs/path")',
        '@app.get("/api/settings")',
        '@app.get("/api/settings/notifications/email")',
        '@app.get("/api/presets/list")',
        '@app.get("/api/debug/routes")',
        '@app.get("/api/user-profile")',
        '@app.get("/api/logs/tail")',
        '@app.get("/api/self-update/status")',
        '@app.get("/api/apps")',
        '@app.get("/api/dev-dashboard/capability-status")',
        '@app.get("/api/dev-dashboard/compact-status")',
        '@app.get("/api/dev-dashboard/modules")',
        '@app.get("/api/dev-dashboard/modules/{module_id}")',
        '@app.get("/api/dev-dashboard/evidence-index")',
        '@app.get("/api/dev-dashboard/manual-command-runs")',
        '@app.get("/api/dev-dashboard/recent-evidence")',
        '@app.get("/api/dev-dashboard/roadmap/areas")',
        '@app.get("/api/dev-dashboard/roadmap/milestones")',
        '@app.get("/api/dev-dashboard/roadmap/blockers")',
        '@app.get("/api/dev-dashboard/roadmap/decisions")',
        '@app.get("/api/dev-dashboard/roadmap/next-prompt")',
        '@app.get("/api/dev-dashboard/roadmap/next-prompts")',
        '@app.get("/api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}")',
        '@app.get("/api/dev-dashboard/backend-health")',
        '@app.get("/api/dev-dashboard/notifications/status")',
        '@app.get("/api/dev-dashboard/notifications/events")',
    ):
        if dup in ap:
            print(f"app_router_slice_duplicate_in_app:{dup}")
    for sub, eps in {
        **e1_slice_endpoints,
        **e2_slice_endpoints,
        **e3_slice_endpoints,
        **e4_slice_endpoints,
        **e5_slice_endpoints,
        **e6_slice_endpoints,
        **e8_slice_endpoints,
    }.items():
        mod = app_router_modules.get(sub)
        if mod and mod.is_file():
            mt = mod.read_text(encoding="utf-8", errors="replace")
            for ep in eps:
                if ep not in mt:
                    print(f"app_router_slice_endpoint_missing:{ep}")
    # Phase E.7: blocked route extraction guards (warn-only)
    if '@app.get("/api/status")' in ap or '@app.get("/api/status",' in ap:
        print("app_status_route_requires_system_status_facade:backend/app.py")
    if re.search(r'@app\.get\("/api/system/network"', ap):
        print("app_network_route_requires_network_facade:backend/app.py")
    if re.search(r'@app\.get\("/api/dev-dashboard/status"', ap):
        if "dcc_status_facade" not in ap and "build_dev_dashboard_status" not in ap:
            print("app_dcc_status_requires_dcc_status_facade:backend/app.py")
    if re.search(r'@app\.get\("/api/dev-dashboard/roadmap"\)', ap):
        if "build_dcc_roadmap_api_bundle" not in ap and "dcc_status_facade" not in ap:
            print("app_roadmap_route_uses_dashboard_aggregation:backend/app.py")
    if "build_dashboard_status" in ap:
        print("dcc_status_direct_build_dashboard_status_in_app:backend/app.py")
    if "load_roadmap_registry_bundle" in ap:
        print("dcc_status_direct_roadmap_bundle_in_app:backend/app.py")
    blocked_extraction_paths = (
        "/api/status",
        "/api/system/network",
        "/api/dev-dashboard/status",
        "/api/dev-dashboard/roadmap",
    )
    for mod in app_router_modules.values():
        if not mod.is_file():
            continue
        mt = mod.read_text(encoding="utf-8", errors="replace")
        rel = mod.relative_to(root).as_posix()
        for bp in blocked_extraction_paths:
            if f'@router.get("{bp}"' in mt:
                print(f"app_blocked_route_extraction_attempt:{rel}:{bp}")
        if "build_dashboard_status" in mt and "dev_dashboard_roadmap.py" in rel:
            print(f"app_roadmap_route_uses_dashboard_aggregation:{rel}")

# Phase F.1: DCC status facade warnings (warn-only)
dcc_facade_path = root / "backend" / "core" / "dcc_status_facade.py"
if not dcc_facade_path.is_file():
    print("dcc_status_facade_missing:backend/core/dcc_status_facade.py")
else:
    dcc_mt = dcc_facade_path.read_text(encoding="utf-8", errors="replace")
    if "FACADE_VERSION" not in dcc_mt or "build_dcc_status_overview" not in dcc_mt:
        print("dcc_status_facade_incomplete:backend/core/dcc_status_facade.py")
    if re.search(r"\bsubprocess\b|\bsystemctl\b", dcc_mt):
        print("dcc_status_facade_uses_subprocess:backend/core/dcc_status_facade.py")
    for route_mod in sorted((root / "backend" / "api" / "routes").glob("*.py")):
        rel = route_mod.relative_to(root).as_posix()
        if rel.endswith("dcc_status_facade.py"):
            continue
        rt = route_mod.read_text(encoding="utf-8", errors="replace")
        if "build_dashboard_status" in rt:
            print(f"dcc_status_direct_build_dashboard_status_in_routes:{rel}")
        if re.search(r"def _normalize_ampel|def normalize_ampel", rt):
            print(f"dcc_status_duplicate_status_mapping:{rel}")
        if re.search(r'"green"\s*:\s*"red"|ampel_mapping\s*=', rt):
            print(f"dcc_status_new_ampel_logic_outside_facade:{rel}")
        if "build_dashboard_status" in rt or "load_roadmap_registry_bundle" in rt:
            if "dcc_status_facade" not in rt:
                print(f"dcc_status_router_bypasses_facade:{rel}")
    status_service = root / "backend" / "core" / "dev_dashboard_status_service.py"
    if status_service.is_file():
        st = status_service.read_text(encoding="utf-8", errors="replace")
        if "build_dashboard_status" in st and "dcc_status_facade" not in st:
            print("dcc_status_direct_build_dashboard_status_in_routes:backend/core/dev_dashboard_status_service.py")

# Phase F.3: DCC aggregation audit guards (warn-only)
DCC_FACADE_ALLOW = {
    "backend/core/dcc_status_facade.py",
    "backend/core/dev_dashboard.py",
}
DCC_BUILD_DASHBOARD_ALLOW = DCC_FACADE_ALLOW | {
    "backend/core/deploy_job_state.py",
}
for path in sorted(backend.rglob("*.py")):
    rel = path.relative_to(root).as_posix()
    if "/tests/" in rel or "/venv/" in rel or "/.venv/" in rel:
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    if "build_dashboard_status" in text and rel not in DCC_BUILD_DASHBOARD_ALLOW:
        if "build_dashboard_status_body" not in text:
            print(f"dcc_direct_build_dashboard_status_outside_facade:{rel}")
    if rel.startswith("backend/api/routes/") and "load_roadmap_registry_bundle" in text:
        if "dcc_status_facade" not in text:
            print(f"dcc_direct_roadmap_bundle_in_router:{rel}")
    if re.search(r"def _normalize_ampel|def normalize_ampel|_LEGACY_STATUS_MAP", text):
        if rel not in DCC_FACADE_ALLOW and "dev_dashboard_cockpit" not in rel and "project_overview" not in rel:
            print(f"dcc_duplicate_ampel_status_mapping:{rel}")
if app_py_path.is_file():
    ap_f3 = app_py_path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"def ai_prompt_generate_stub", ap_f3) and "build_dashboard_status" in ap_f3:
        print("dcc_prompt_generate_uses_dashboard_status:backend/app.py")
deploy_job = root / "backend" / "core" / "deploy_job_state.py"
if deploy_job.is_file():
    dj = deploy_job.read_text(encoding="utf-8", errors="replace")
    if "build_dashboard_status" in dj and "dcc_status_facade" not in dj:
        print("dcc_deploy_core_cross_coupling:backend/core/deploy_job_state.py")
frontend_vm = root / "frontend" / "src" / "trafficLight" / "trafficLightModel.ts"
frontend_status_vm = root / "frontend" / "src" / "viewmodels" / "statusViewModel.ts"
frontend_status_vm_test = root / "frontend" / "src" / "viewmodels" / "statusViewModel.test.ts"
if not frontend_status_vm.is_file():
    print("frontend_status_viewmodel_missing:frontend/src/viewmodels/statusViewModel.ts")
else:
    svm = frontend_status_vm.read_text(encoding="utf-8", errors="replace")
    if "normalizeStatusKind" not in svm or "buildStatusViewModel" not in svm:
        print("frontend_status_viewmodel_incomplete:frontend/src/viewmodels/statusViewModel.ts")
    if re.search(r"\bfetch\s*\(|fetchApi|axios", svm):
        print("frontend_status_viewmodel_has_api_fetch:frontend/src/viewmodels/statusViewModel.ts")
if not frontend_status_vm_test.is_file():
    print("frontend_status_viewmodel_missing_tests:frontend/src/viewmodels/statusViewModel.test.ts")
if frontend_vm.is_file() and frontend_status_vm.is_file():
    tl = frontend_vm.read_text(encoding="utf-8", errors="replace")
    if "statusViewModel" not in tl:
        print("frontend_traffic_light_bypasses_status_viewmodel:frontend/src/trafficLight/trafficLightModel.ts")
    elif "LAMP_RANK" in tl:
        print("frontend_duplicate_traffic_light_mapping:frontend/src/trafficLight/trafficLightModel.ts")
dcc_compact = root / "frontend" / "src" / "lib" / "devDashboard" / "dccCompactStatus.ts"
dcc_filters = root / "frontend" / "src" / "pages" / "devDashboardFilters.ts"
if dcc_compact.is_file() and frontend_status_vm.is_file():
    dc = dcc_compact.read_text(encoding="utf-8", errors="replace")
    if "deployDriftTone" in dc and "statusViewModel" not in dc:
        print("frontend_dcc_compact_status_bypasses_status_viewmodel:frontend/src/lib/devDashboard/dccCompactStatus.ts")
if dcc_filters.is_file() and frontend_status_vm.is_file():
    df = dcc_filters.read_text(encoding="utf-8", errors="replace")
    if "toneClass" in df and "statusViewModel" not in df:
        print("frontend_dev_dashboard_filters_bypasses_status_viewmodel:frontend/src/pages/devDashboardFilters.ts")
if frontend_status_vm.is_file():
    frontend_src = root / "frontend" / "src"
    local_mapping_hits = 0
    for path in sorted(frontend_src.rglob("*.ts*")):
        rel = path.relative_to(root).as_posix()
        if "/viewmodels/" in rel or ".test." in rel:
            continue
        try:
            pt = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"===\s*['\"]green['\"]|===\s*['\"]red['\"]|===\s*['\"]yellow['\"]", pt):
            local_mapping_hits += 1
            if local_mapping_hits <= 5:
                print(f"frontend_component_local_status_mapping:{rel}")
    if local_mapping_hits > 5:
        print(f"frontend_component_local_status_mapping:count_{local_mapping_hits}")
    if local_mapping_hits < 28:
        print(f"frontend_component_status_mapping_reduced_h3:count_{local_mapping_hits}")
h3_migrated = (
    root / "frontend" / "src" / "components" / "dev-dashboard" / "RescueDeveloperPipelineCard.tsx",
    root / "frontend" / "src" / "components" / "dev-dashboard" / "ControlCenterOverviewHeader.tsx",
    root / "frontend" / "src" / "components" / "dev-dashboard" / "ManualCommandRunsPanel.tsx",
)
for path in h3_migrated:
    if path.is_file():
        pt = path.read_text(encoding="utf-8", errors="replace")
        if "statusViewModel" not in pt:
            rel = path.relative_to(root).as_posix()
            print(f"frontend_component_bypasses_status_viewmodel:{rel}")
large_pages = (
    root / "frontend" / "src" / "pages" / "BackupRestore.tsx",
    root / "frontend" / "src" / "pages" / "Dashboard.tsx",
)
for path in large_pages:
    if path.is_file():
        pt = path.read_text(encoding="utf-8", errors="replace")
        if "dashboardLegacyToneFromInput" in pt or "buildTrafficLightViewModel" in pt:
            rel = path.relative_to(root).as_posix()
            print(f"frontend_large_page_status_migration_attempt:{rel}")

# Phase F.4: DCC facade delegation guards (warn-only)
readonly_mod = root / "backend" / "api" / "routes" / "dev_dashboard_readonly.py"
if readonly_mod.is_file():
    ro = readonly_mod.read_text(encoding="utf-8", errors="replace")
    e8_facade_apis = (
        "build_dcc_backend_health_api",
        "build_dcc_notifications_status_api",
        "build_dcc_notifications_events_api",
        "build_dcc_evidence_index_api",
    )
    if "dcc_status_facade" not in ro:
        print("dcc_readonly_router_bypasses_facade:backend/api/routes/dev_dashboard_readonly.py")
    for api in e8_facade_apis:
        if api not in ro:
            print(f"dcc_readonly_router_bypasses_facade:missing_{api}")
    if "load_backend_health_snapshot" in ro:
        print("dcc_backend_health_duplicate_logic:backend/api/routes/dev_dashboard_readonly.py")
    if "build_notification_summary" in ro or "list_notification_events" in ro:
        print("dcc_notification_duplicate_logic:backend/api/routes/dev_dashboard_readonly.py")
    if re.search(r"dev_dashboard_core\.build_evidence_index|build_evidence_index\s*\(", ro):
        if "build_dcc_evidence_index_api" not in ro:
            print("dcc_evidence_duplicate_logic:backend/api/routes/dev_dashboard_readonly.py")
if app_py_path.is_file():
    ap_f4 = app_py_path.read_text(encoding="utf-8", errors="replace")
    stub_m = re.search(r"async def ai_prompt_generate_stub[\s\S]{0,900}", ap_f4)
    if stub_m:
        block = stub_m.group(0)
        if "build_dcc_cursor_meta_prompt_api" not in block:
            print("dcc_ai_prompt_bypasses_facade:backend/app.py")
        if "build_dashboard_status" in block:
            print("dcc_ai_prompt_bypasses_facade:uses_build_dashboard_status")

# Phase G.1: System Status Facade guards (warn-only)
system_facade_mod = root / "backend" / "core" / "system_status_facade.py"
if not system_facade_mod.is_file():
    print("system_status_facade_missing:backend/core/system_status_facade.py")
else:
    sf = system_facade_mod.read_text(encoding="utf-8", errors="replace")
    if "FACADE_VERSION" not in sf or "build_system_status" not in sf:
        print("system_status_facade_incomplete:backend/core/system_status_facade.py")
    if re.search(r"^import subprocess|from subprocess|subprocess\.(run|Popen)", sf, re.M):
        print("system_status_facade_uses_subprocess:backend/core/system_status_facade.py")
    if re.search(r"run_command\([^)]*systemctl|systemctl is-active|systemctl status", sf):
        print("system_status_facade_uses_systemctl:backend/core/system_status_facade.py")
    if re.search(r"\bget_network_info\b|\b_demo_network\b", sf):
        if "excluded_g2" not in sf:
            print("system_status_facade_uses_network_probe:backend/core/system_status_facade.py")
    if re.search(r"def _normalize_ampel|def normalize_ampel|_LEGACY_AMPEL_MAP", sf):
        if "normalize_legacy_system_status" not in sf:
            print(f"system_status_duplicate_status_mapping:backend/core/system_status_facade.py")
if app_py_path.is_file():
    ap_g1 = app_py_path.read_text(encoding="utf-8", errors="replace")
    if '@app.get("/api/status")' in ap_g1 or '@app.get("/api/status",' in ap_g1:
        if "system_status_facade" not in ap_g1:
            print("app_status_route_requires_system_status_facade:backend/app.py")
    sys_status_m = re.search(
        r'@app\.get\("/api/system/status"\)\s*\nasync def system_status\(\):[\s\S]{0,500}',
        ap_g1,
    )
    if sys_status_m:
        block = sys_status_m.group(0)
        if "build_system_status" not in block:
            print("app_system_status_route_bypasses_facade:backend/app.py")
        if "_compute_system_status" in block or "APP_SETTINGS" in block:
            print("app_system_status_route_bypasses_facade:direct_ampel_in_handler")
    if re.search(r"def get_network_info|def _demo_network", ap_g1):
        if "network_info_facade" not in ap_g1:
            print("system_status_new_network_logic_outside_network_facade:backend/app.py")

# Phase G.2: Network Info Facade guards (warn-only)
network_facade_mod = root / "backend" / "core" / "network_info_facade.py"
if not network_facade_mod.is_file():
    print("network_info_facade_missing:backend/core/network_info_facade.py")
else:
    nf = network_facade_mod.read_text(encoding="utf-8", errors="replace")
    if "FACADE_VERSION" not in nf or "build_network_info" not in nf:
        print("network_info_facade_incomplete:backend/core/network_info_facade.py")
    if re.search(r"nmcli\s+(con|device)\s+(modify|connect|disconnect|down|up)", nf, re.I):
        print("network_info_facade_uses_network_write:backend/core/network_info_facade.py")
    if re.search(r"ip\s+link\s+set|netplan\s+apply", nf, re.I):
        print("network_info_new_nmcli_write_detected:backend/core/network_info_facade.py")
    if re.search(r"def _normalize_network|NETWORK_STATUS_MAP\s*=", nf):
        if "normalize_legacy_network_info" not in nf:
            print(f"network_info_duplicate_network_mapping:backend/core/network_info_facade.py")
if app_py_path.is_file():
    ap_g2 = app_py_path.read_text(encoding="utf-8", errors="replace")
    status_m = re.search(
        r'@app\.get\("/api/status"\)\s*\nasync def get_status\([^)]*\):[\s\S]{0,400}',
        ap_g2,
    )
    if status_m and "network_info_facade" not in status_m.group(0):
        print("app_status_network_block_requires_network_facade:backend/app.py")
    sys_net_m = re.search(
        r'@app\.get\("/api/system/network"\)\s*\nasync def get_system_network\([^)]*\):[\s\S]{0,500}',
        ap_g2,
    )
    if sys_net_m:
        block = sys_net_m.group(0)
        if "network_info_facade" not in block:
            print("app_system_network_route_requires_network_facade:backend/app.py")
        elif re.search(r"\bget_network_info\s*\(|\b_demo_network\s*\(", block):
            print("app_system_network_route_bypasses_facade:backend/app.py")
    if status_m:
        block = status_m.group(0)
        if re.search(r"\bget_network_info\s*\(|\b_demo_network\s*\(", block):
            print("app_status_network_block_bypasses_facade:backend/app.py")
    # Phase G.3: remaining app.py handler cleanup guards (warn-only)
    sys_info_m = re.search(
        r'@app\.get\("/api/system-info"\)\s*\nasync def get_system_info\([^)]*\):[\s\S]{0,15000}',
        ap_g2,
    )
    if sys_info_m:
        block = sys_info_m.group(0)
        if "network_info_facade" not in block:
            print("app_system_info_requires_network_facade:backend/app.py")
        elif re.search(r"\bget_network_info\s*\(|\b_demo_network\s*\(", block):
            print("app_direct_demo_network_usage_outside_legacy:backend/app.py:get_system_info")
    web_m = re.search(
        r'@app\.get\("/api/webserver/status"\)\s*\nasync def webserver_status\(\):[\s\S]{0,2500}',
        ap_g2,
    )
    if web_m:
        block = web_m.group(0)
        if "network_info_facade" not in block:
            print("app_webserver_status_requires_network_facade:backend/app.py")
        elif re.search(r"\bget_network_info\s*\(", block):
            print("app_direct_network_info_usage_outside_legacy:backend/app.py:webserver_status")
    for line in ap_g2.splitlines():
        stripped = line.strip()
        if "_demo_network(" in line and not stripped.startswith("def _demo_network"):
            print("app_direct_demo_network_usage_outside_legacy:backend/app.py")
            break
    else:
        pass
    for line in ap_g2.splitlines():
        stripped = line.strip()
        if "get_network_info(" in line and not stripped.startswith("def get_network_info"):
            print("app_direct_network_info_usage_outside_legacy:backend/app.py")
            break
    for path in sorted(backend.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if "/tests/" in rel or "/venv/" in rel or rel.endswith("network_info_facade.py"):
            continue
        if rel.startswith("backend/api/routes/") or rel == "backend/app.py":
            try:
                pt = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "get_network_info(" in pt and "network_info_facade" not in pt:
                if rel == "backend/app.py" and "def get_network_info" in pt:
                    continue
                print(f"network_info_new_network_logic_outside_facade:{rel}")

if deploy_routes.is_file():
    subrouter_markers = (
        "build_plan_only_response",
        'tags=["deploy-evidence"]',
        'tags=["deploy-governance"]',
        'tags=["deploy-diagnostics"]',
    )
    if any(m in dr_text for m in subrouter_markers):
        if re.search(r'@router\.(post|get)\("/runners/', dr_text):
            print("new_runner_route_in_routes_py_detected:runners_path")
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
