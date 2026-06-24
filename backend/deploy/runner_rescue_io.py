from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_ROOT = (REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
BUILD_RESCUE_ROOT = (REPO_ROOT / "build" / "rescue").resolve(strict=False)

_RESCUE_SUBDIRS = ("live-build", "output", "evidence", "logs")

ARTIFACT_SCAN_SKIP_TOP = frozenset(
    {"output", "live-build", "archive", "fat32-esp-staging", "temp-runtime", "evidence", "logs"}
)


def scan_build_rescue_for_forbidden_images() -> tuple[bool, list[str]]:
    """True when no unexpected .iso/.img files exist under build/rescue (dev-machine safe)."""
    bad: list[str] = []
    root = BUILD_RESCUE_ROOT
    if not root.is_dir():
        return True, []
    for fp in root.rglob("*"):
        try:
            rel = fp.relative_to(root)
            if rel.parts and (
                rel.parts[0] in ARTIFACT_SCAN_SKIP_TOP or rel.parts[0].startswith(".")
            ):
                continue
        except ValueError:
            continue
        if fp.is_symlink():
            try:
                fp.resolve().relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
            except (OSError, ValueError):
                bad.append(f"SYMLINK_OUTSIDE:{fp.relative_to(REPO_ROOT)}")
                continue
        if fp.is_file():
            low = fp.name.lower()
            if len(rel.parts) == 1 and low.startswith("uefi-fat32-"):
                continue
            if low.endswith(".iso") or low.endswith(".img"):
                bad.append(str(fp.relative_to(REPO_ROOT)).replace("\\", "/"))
    return len(bad) == 0, bad


def ensure_rescue_workspace_dirs() -> Path:
    """Creates ``build/rescue/{live-build,output,evidence,logs}`` if missing."""
    for name in _RESCUE_SUBDIRS:
        (BUILD_RESCUE_ROOT / name).mkdir(parents=True, exist_ok=True)
    return BUILD_RESCUE_ROOT


def resolve_under_build_rescue(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, f"{prefix}_PATH_INVALID"
    unresolved = REPO_ROOT / raw
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(BUILD_RESCUE_ROOT)
    except (OSError, ValueError):
        return None, f"{prefix}_OUTSIDE_BUILD_RESCUE"
    return resolved, None


def resolve_handoff_path(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, f"{prefix}_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, f"{prefix}_PATH_INVALID"
    unresolved = REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, f"{prefix}_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(HANDOFF_ROOT) + os.sep) or str(resolved) == str(HANDOFF_ROOT)):
        return None, f"{prefix}_OUTSIDE_HANDOFF"
    return resolved, None


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def load_json_handoff(rel: str, prefix: str) -> tuple[Any | None, str | None]:
    p, err = resolve_handoff_path(rel, prefix)
    if err or p is None or not p.is_file():
        return None, err or f"{prefix}_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, f"{prefix}_JSON_INVALID"


def guard_handoff_overwrite(path: Path, *, explicit_overwrite: bool, prefix: str) -> str | None:
    if path.exists() and path.is_file() and not explicit_overwrite:
        return f"{prefix}_EXISTS_NO_OVERWRITE"
    return None


def write_json_handoff(path: Path, obj: dict[str, Any], *, max_bytes: int) -> str | None:
    text = json.dumps(obj, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > max_bytes:
        return "RESCUE_HANDOFF_OUTPUT_TOO_LARGE"
    try:
        atomic_write_text(path, text)
    except OSError:
        return "RESCUE_HANDOFF_WRITE_FAILED"
    return None


def under_build_rescue(rel_or_abs: str) -> bool:
    s = str(rel_or_abs or "").replace("\\", "/").strip()
    if not s:
        return False
    if s.startswith("build/rescue/") or s == "build/rescue":
        return True
    if s.startswith("/"):
        try:
            resolved = Path(s).resolve(strict=False)
            root = (REPO_ROOT / "build" / "rescue").resolve(strict=False)
            resolved.relative_to(root)
            return True
        except (OSError, ValueError):
            return False
    return False
