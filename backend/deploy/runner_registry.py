"""
Deploy runner registry — static metadata and classification only.

Phase C.1: No runner imports, no execution, no runtime writes.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

REGISTRY_VERSION = 1

_DEVICE_WRITE_PATTERNS = (
    re.compile(r"\bdd\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bwipefs\b"),
    re.compile(r"\bsgdisk\b"),
)
_SYSTEM_PATH_PATTERNS = (
    re.compile(r"/etc/"),
    re.compile(r"/opt/"),
    re.compile(r"/usr/"),
)
_FILE_WRITE_PATTERNS = (
    re.compile(r"\.write_text\s*\("),
    re.compile(r"\.write_bytes\s*\("),
    re.compile(r"\bopen\s*\([^)]*['\"]w"),
)
_MOUNT_PATTERNS = (
    re.compile(r"\bmount\b"),
    re.compile(r"\bumount\b"),
)
_PACKAGE_PATTERNS = (
    re.compile(r"\bapt\s+"),
    re.compile(r"\bdpkg\b"),
)


class RunnerCategory(str, Enum):
    RUNTIME = "runtime"
    DEPLOY = "deploy"
    RESCUE = "rescue"
    RESCUE_BUILD = "rescue_build"
    RESCUE_USB = "rescue_usb"
    BACKUP_RELATED = "backup_related"
    RESTORE_RELATED = "restore_related"
    NOTIFICATION = "notification"
    EVIDENCE = "evidence"
    PACKAGING = "packaging"
    DASHBOARD = "dashboard"
    DIAGNOSTICS = "diagnostics"
    UNKNOWN = "unknown"


class RunnerRiskLevel(str, Enum):
    READ_ONLY = "read_only"
    TEMPLATE_WRITE = "template_write"
    EVIDENCE_WRITE = "evidence_write"
    LOCAL_RUNTIME_CHANGE = "local_runtime_change"
    SYSTEM_CHANGE = "system_change"
    DEVICE_WRITE = "device_write"
    DESTRUCTIVE = "destructive"


class RunnerExecutionPolicy(str, Enum):
    NEVER_AUTO = "never_auto"
    MANUAL_ONLY = "manual_only"
    OPERATOR_CONFIRMED = "operator_confirmed"
    LAB_ONLY = "lab_only"
    DISABLED = "disabled"


@dataclass(frozen=True)
class RunnerCapability:
    writes_files: bool = False
    touches_system_paths: bool = False
    uses_sudo: bool = False
    uses_device_write: bool = False
    requires_operator: bool = False


@dataclass
class RunnerRegistryEntry:
    runner_id: str
    path: str
    category: RunnerCategory
    risk_level: RunnerRiskLevel
    execution_policy: RunnerExecutionPolicy
    writes_files: bool
    touches_system_paths: bool
    uses_sudo: bool
    uses_device_write: bool
    requires_operator: bool
    has_tests: bool
    notes: list[str] = field(default_factory=list)
    lines: int = 0
    facade_version: int = REGISTRY_VERSION


@dataclass
class RunnerRegistrySummary:
    total: int
    by_category: dict[str, int]
    by_risk: dict[str, int]
    by_policy: dict[str, int]
    largest: list[dict[str, Any]]
    device_write_count: int
    destructive_count: int
    sudo_count: int
    unknown_count: int
    facade_version: int = REGISTRY_VERSION


def runner_id_from_path(path: str | Path) -> str:
    """Stable runner_id from filename stem (e.g. runner_foo -> runner_foo)."""
    return Path(path).stem


def _repo_root_from_deploy(deploy_root: Path) -> Path:
    if deploy_root.name == "deploy" and deploy_root.parent.name == "backend":
        return deploy_root.parent.parent
    return deploy_root


def _has_tests_for_runner(runner_id: str, repo_root: Path) -> bool:
    tests_dir = repo_root / "backend" / "tests"
    if not tests_dir.is_dir():
        return False
    needles = {runner_id, runner_id.removeprefix("runner_")}
    for tf in tests_dir.glob("*.py"):
        try:
            text = tf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(n in text for n in needles):
            return True
    return False


def _scan_capabilities(text: str, name: str) -> tuple[RunnerCapability, list[str]]:
    notes: list[str] = []
    lower_name = name.lower()
    lower = text.lower()

    uses_sudo = "sudo" in lower
    if uses_sudo:
        notes.append("subprocess_or_sudo")

    uses_device_write = any(p.search(lower) for p in _DEVICE_WRITE_PATTERNS)
    if uses_device_write:
        notes.append("device_write_tokens")

    if any(k in lower_name for k in ("fat32", "esp_usb", "usb_write")) or (
        "usb" in lower_name and any(k in lower for k in ("write", "dd ", "mkfs", "wipefs"))
    ):
        uses_device_write = True
        notes.append("rescue_usb_heuristic")

    touches_system_paths = any(p.search(text) for p in _SYSTEM_PATH_PATTERNS)
    writes_files = any(p.search(text) for p in _FILE_WRITE_PATTERNS)
    if "json.dumps" in text and "write_text" in text:
        writes_files = True

    if "subprocess" in lower:
        notes.append("subprocess")

    if any(p.search(lower) for p in _MOUNT_PATTERNS):
        notes.append("mount_umount")
        touches_system_paths = True

    if any(p.search(lower) for p in _PACKAGE_PATTERNS):
        notes.append("package_manager")
        touches_system_paths = True

    requires_operator = uses_sudo or uses_device_write or "operator" in lower_name or "manual_" in lower_name

    return RunnerCapability(
        writes_files=writes_files,
        touches_system_paths=touches_system_paths,
        uses_sudo=uses_sudo,
        uses_device_write=uses_device_write,
        requires_operator=requires_operator,
    ), notes


def _classify_category(name: str, text: str) -> RunnerCategory:
    n = name.lower()
    if any(k in n for k in ("fat32", "esp_usb", "usb_write", "rescue_stick")) or (
        "usb" in n and "rescue" in n
    ):
        return RunnerCategory.RESCUE_USB
    if any(k in n for k in ("iso", "live_build", "debian_live", "sandbox_controlled_copy")):
        return RunnerCategory.RESCUE_BUILD
    if "notification" in n or "email" in n or "alert" in n:
        return RunnerCategory.NOTIFICATION
    if "evidence" in n or "summary" in n or "timeline" in n or "snapshot" in n:
        return RunnerCategory.EVIDENCE
    if "backup" in n:
        return RunnerCategory.BACKUP_RELATED
    if "restore" in n:
        return RunnerCategory.RESTORE_RELATED
    if "dashboard" in n or "dcc" in n or "dev_dashboard" in n:
        return RunnerCategory.DASHBOARD
    if "diagnostic" in n or "inspect" in n:
        return RunnerCategory.DIAGNOSTICS
    if "package" in n or "packaging" in n or "deb" in n:
        return RunnerCategory.PACKAGING
    if any(k in n for k in ("runtime", "version", "gate", "identifier")):
        return RunnerCategory.RUNTIME
    if "deploy" in n or "install" in n:
        return RunnerCategory.DEPLOY
    if "rescue" in n:
        return RunnerCategory.RESCUE
    if "rescue" in text.lower()[:500]:
        return RunnerCategory.RESCUE
    return RunnerCategory.UNKNOWN


def _classify_risk(
    category: RunnerCategory,
    caps: RunnerCapability,
    notes: list[str],
    text: str,
) -> RunnerRiskLevel:
    lower = text.lower()
    if caps.uses_device_write:
        if re.search(r"\bdd\b", lower) or any(k in lower for k in ("mkfs", "wipefs", "sgdisk")):
            return RunnerRiskLevel.DESTRUCTIVE
        return RunnerRiskLevel.DEVICE_WRITE

    if category == RunnerCategory.EVIDENCE:
        return RunnerRiskLevel.EVIDENCE_WRITE
    if caps.writes_files and category in (RunnerCategory.RESCUE_BUILD, RunnerCategory.PACKAGING):
        return RunnerRiskLevel.TEMPLATE_WRITE
    if caps.writes_files:
        return RunnerRiskLevel.EVIDENCE_WRITE
    if "mount_umount" in notes or "package_manager" in notes:
        return RunnerRiskLevel.SYSTEM_CHANGE
    if caps.touches_system_paths or caps.uses_sudo:
        return RunnerRiskLevel.LOCAL_RUNTIME_CHANGE
    if category == RunnerCategory.UNKNOWN:
        return RunnerRiskLevel.LOCAL_RUNTIME_CHANGE
    return RunnerRiskLevel.READ_ONLY


def _infer_execution_policy(risk: RunnerRiskLevel, caps: RunnerCapability) -> RunnerExecutionPolicy:
    if risk == RunnerRiskLevel.DESTRUCTIVE:
        return RunnerExecutionPolicy.NEVER_AUTO
    if risk in (RunnerRiskLevel.DEVICE_WRITE, RunnerRiskLevel.SYSTEM_CHANGE):
        return RunnerExecutionPolicy.MANUAL_ONLY if caps.requires_operator else RunnerExecutionPolicy.OPERATOR_CONFIRMED
    if risk == RunnerRiskLevel.EVIDENCE_WRITE:
        return RunnerExecutionPolicy.LAB_ONLY
    if caps.uses_sudo:
        return RunnerExecutionPolicy.OPERATOR_CONFIRMED
    return RunnerExecutionPolicy.NEVER_AUTO


def classify_runner_file(
    path: str | Path,
    *,
    text: str | None = None,
    repo_root: str | Path | None = None,
) -> RunnerRegistryEntry:
    """Classify a single runner file from path and optional pre-read text."""
    p = Path(path)
    raw = text if text is not None else p.read_text(encoding="utf-8", errors="replace")
    lines = raw.count("\n") + 1
    rid = runner_id_from_path(p)
    caps, notes = _scan_capabilities(raw, p.name)
    category = _classify_category(p.name, raw)
    if category == RunnerCategory.UNKNOWN:
        notes.append("category_unknown_conservative")
    risk = _classify_risk(category, caps, notes, raw)
    policy = _infer_execution_policy(risk, caps)

    root = Path(repo_root) if repo_root else _repo_root_from_deploy(p.parent)
    has_tests = _has_tests_for_runner(rid, root)

    return RunnerRegistryEntry(
        runner_id=rid,
        path=str(p).replace("\\", "/"),
        category=category,
        risk_level=risk,
        execution_policy=policy,
        writes_files=caps.writes_files,
        touches_system_paths=caps.touches_system_paths,
        uses_sudo=caps.uses_sudo,
        uses_device_write=caps.uses_device_write,
        requires_operator=caps.requires_operator,
        has_tests=has_tests,
        notes=list(dict.fromkeys(notes)),
        lines=lines,
    )


_REGISTRY_MODULE_NAME = "runner_registry.py"


def build_runner_registry_from_files(root: str | Path = "backend/deploy") -> list[RunnerRegistryEntry]:
    """Build registry from runner_*.py files (read-only, no imports)."""
    deploy_root = Path(root)
    repo_root = _repo_root_from_deploy(deploy_root.resolve())
    entries: list[RunnerRegistryEntry] = []
    for p in sorted(deploy_root.glob("runner_*.py")):
        if not p.is_file() or p.name == _REGISTRY_MODULE_NAME:
            continue
        entries.append(classify_runner_file(p, repo_root=repo_root))
    return entries


def entry_to_dict(entry: RunnerRegistryEntry) -> dict[str, Any]:
    d = asdict(entry)
    d["category"] = entry.category.value
    d["risk_level"] = entry.risk_level.value
    d["execution_policy"] = entry.execution_policy.value
    return d


def build_runner_registry_summary(entries: list[RunnerRegistryEntry]) -> RunnerRegistrySummary:
    by_category: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    by_policy: dict[str, int] = {}
    for e in entries:
        by_category[e.category.value] = by_category.get(e.category.value, 0) + 1
        by_risk[e.risk_level.value] = by_risk.get(e.risk_level.value, 0) + 1
        by_policy[e.execution_policy.value] = by_policy.get(e.execution_policy.value, 0) + 1

    largest = sorted(
        [{"runner_id": e.runner_id, "path": e.path, "lines": e.lines} for e in entries],
        key=lambda x: x["lines"],
        reverse=True,
    )[:15]

    return RunnerRegistrySummary(
        total=len(entries),
        by_category=by_category,
        by_risk=by_risk,
        by_policy=by_policy,
        largest=largest,
        device_write_count=sum(1 for e in entries if e.uses_device_write),
        destructive_count=sum(1 for e in entries if e.risk_level == RunnerRiskLevel.DESTRUCTIVE),
        sudo_count=sum(1 for e in entries if e.uses_sudo),
        unknown_count=sum(1 for e in entries if e.category == RunnerCategory.UNKNOWN),
    )


def find_runner_by_id(runner_id: str, entries: list[RunnerRegistryEntry]) -> RunnerRegistryEntry | None:
    for e in entries:
        if e.runner_id == runner_id:
            return e
    return None


def list_runners_by_category(category: RunnerCategory | str, entries: list[RunnerRegistryEntry]) -> list[RunnerRegistryEntry]:
    cat = category.value if isinstance(category, RunnerCategory) else str(category)
    return [e for e in entries if e.category.value == cat]


def list_runners_by_risk(risk_level: RunnerRiskLevel | str, entries: list[RunnerRegistryEntry]) -> list[RunnerRegistryEntry]:
    risk = risk_level.value if isinstance(risk_level, RunnerRiskLevel) else str(risk_level)
    return [e for e in entries if e.risk_level.value == risk]


def registry_policy_warnings(entries: list[RunnerRegistryEntry]) -> list[str]:
    """Boundary helper: policy mismatches (warn-only)."""
    warns: list[str] = []
    ids = {e.runner_id for e in entries}
    for e in entries:
        if e.uses_device_write and e.execution_policy not in {
            RunnerExecutionPolicy.NEVER_AUTO,
            RunnerExecutionPolicy.MANUAL_ONLY,
            RunnerExecutionPolicy.OPERATOR_CONFIRMED,
        }:
            warns.append(f"runner_device_write_without_manual_policy:{e.runner_id}")
        if e.uses_sudo and e.execution_policy not in {
            RunnerExecutionPolicy.OPERATOR_CONFIRMED,
            RunnerExecutionPolicy.MANUAL_ONLY,
            RunnerExecutionPolicy.NEVER_AUTO,
        }:
            warns.append(f"runner_sudo_without_operator_policy:{e.runner_id}")
        if e.risk_level == RunnerRiskLevel.DESTRUCTIVE and e.execution_policy != RunnerExecutionPolicy.NEVER_AUTO:
            warns.append(f"runner_destructive_without_never_auto:{e.runner_id}")
    return warns
