"""Live-build tree permission preflight for controlled rescue ISO builds."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

BUILD_TREE_REL = "build/rescue/live-build/setuphelfer-rescue-live"

# Paths relative to build tree that may be removed by clean helper.
CLEAN_RELATIVE_DIRS = (".build", "binary", "chroot", "cache", "local")
CLEAN_RELATIVE_FILE_GLOBS = (
    "binary.contents",
    "binary.packages",
    "binary.iso",
    "binary.hybrid.iso",
    "binary.img",
    "binary*.zsync*",
    "chroot.headers",
    "chroot.packages.*",
    "wget-log*",
)


def default_build_tree(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    return (root / BUILD_TREE_REL).resolve(strict=False)


def _is_writable(path: Path) -> bool:
    if not path.exists():
        return True
    return os.access(path, os.W_OK)


def _find_root_owned(build_root: Path, *, max_depth: int = 6) -> list[str]:
    found: list[str] = []
    if not build_root.is_dir():
        return found
    base_parts = len(build_root.resolve().parts)
    for dirpath, dirnames, filenames in os.walk(build_root):
        depth = len(Path(dirpath).resolve().parts) - base_parts
        if depth > max_depth:
            dirnames.clear()
            continue
        p = Path(dirpath)
        try:
            st = p.lstat()
            if st.st_uid == 0:
                found.append(str(p))
        except OSError:
            continue
        for name in filenames:
            fp = p / name
            try:
                if fp.lstat().st_uid == 0:
                    found.append(str(fp))
            except OSError:
                continue
    return sorted(set(found))


def assess_build_tree_permissions(build_root: str | Path) -> dict[str, Any]:
    """Return permission preflight for live-build working tree."""
    root = Path(build_root).resolve(strict=False)
    dot_build = root / ".build"
    dot_build_config = dot_build / "config"
    root_owned = _find_root_owned(root)

    tree_writable = _is_writable(root)
    dot_build_writable = _is_writable(dot_build) if dot_build.exists() else True
    dot_build_config_writable = _is_writable(dot_build_config) if dot_build_config.exists() else True

    active_areas = {".build", "binary", "chroot", "cache", "local"}
    root_owned_active = [
        p for p in root_owned
        if any(f"/{area}/" in p or p.endswith(f"/{area}") for area in active_areas)
        or "/.build/" in p or p.endswith("/.build")
    ]
    # Also root-owned files directly under tree root from prior lb runs
    root_owned_top = [
        p for p in root_owned
        if Path(p).parent.resolve() == root.resolve()
    ]

    permission_blockers: list[str] = []
    if dot_build.exists() and not dot_build_writable:
        permission_blockers.append("dot_build_not_writable")
    if dot_build_config.exists() and not dot_build_config_writable:
        permission_blockers.append("dot_build_config_not_writable")
    if root_owned_active:
        permission_blockers.append("root_owned_active_work_areas")
    if root_owned_top:
        permission_blockers.append("root_owned_top_level_artifacts")

    operator_fix_required = bool(permission_blockers)
    recommended_fix = ""
    if operator_fix_required:
        recommended_fix = (
            "Run: sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh "
            "--operator-confirm-clean"
        )

    status = "ready"
    if permission_blockers:
        status = "blocked"
    elif root_owned and not root_owned_active:
        status = "review_required"

    return {
        "build_tree": str(root),
        "tree_writable": tree_writable,
        "dot_build_exists": dot_build.exists(),
        "dot_build_writable": dot_build_writable,
        "dot_build_config_exists": dot_build_config.exists(),
        "dot_build_config_writable": dot_build_config_writable,
        "root_owned_count": len(root_owned),
        "root_owned_active_count": len(root_owned_active),
        "root_owned_paths_sample": root_owned[:20],
        "root_owned_active_sample": root_owned_active[:20],
        "operator_fix_required": operator_fix_required,
        "recommended_fix": recommended_fix,
        "permission_blockers": permission_blockers,
        "permission_status": status,
        "error_code": "rescue_iso_build.permission_denied_dot_build" if permission_blockers else None,
    }


def validate_clean_target(path: Path, build_root: Path) -> bool:
    """True if path is allowed for clean helper removal."""
    try:
        resolved = path.resolve(strict=False)
        build_resolved = build_root.resolve(strict=False)
        if not str(resolved).startswith(str(build_resolved) + os.sep) and resolved != build_resolved:
            return False
        rel = resolved.relative_to(build_resolved)
    except (OSError, ValueError):
        return False
    rel_posix = rel.as_posix()
    if rel_posix in CLEAN_RELATIVE_DIRS:
        return True
    if rel_posix == ".build" or rel_posix.startswith(".build/"):
        return True
    top = rel.parts[0] if rel.parts else ""
    if top in CLEAN_RELATIVE_DIRS:
        return True
    if len(rel.parts) == 1:
        name = rel.parts[0]
        for pattern in ("binary.", "chroot.", "wget-log"):
            if name.startswith(pattern):
                return True
        if name.startswith("binary") and (name.endswith(".iso") or name.endswith(".img")):
            return True
    return False


def list_clean_targets(build_root: Path) -> list[Path]:
    """List paths under build tree eligible for controlled clean."""
    targets: list[Path] = []
    if not build_root.is_dir():
        return targets
    for name in CLEAN_RELATIVE_DIRS:
        p = build_root / name
        if p.exists():
            targets.append(p)
    for item in build_root.iterdir():
        if not item.exists():
            continue
        if validate_clean_target(item, build_root) and item not in targets:
            targets.append(item)
    return sorted(set(targets), key=lambda p: str(p))
