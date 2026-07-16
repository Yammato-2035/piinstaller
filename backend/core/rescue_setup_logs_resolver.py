"""Canonical SETUP_LOGS resolution for rescue live + host import (001D7E)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESOLUTION_SCHEMA = "setuphelfer.rescue.setup-logs-resolution.v1"
CANONICAL_MOUNT = Path("/run/setuphelfer-rescue/media/SETUP_LOGS")
STATE_DIR = Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))
RESOLUTION_PATH = STATE_DIR / "setup-logs-resolution.json"
ENV_FILE = STATE_DIR / "environment"
BOOTSTRAP_EVIDENCE = STATE_DIR / "bootstrap-evidence"
LABELS = frozenset({"SETUP_LOGS", "SETUPHELFER_LOGS"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], *, timeout: int = 15) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def _lsblk_json() -> dict[str, Any]:
    rc, out = _run(["lsblk", "-J", "-b", "-o", "NAME,PATH,TYPE,FSTYPE,LABEL,MOUNTPOINT,TRAN,PKNAME,RM"])
    if rc != 0 or not out:
        return {}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _iter_block_nodes(node: dict[str, Any], *, parent_tran: str = "", parent_path: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = str(node.get("path") or "")
    tran = str(node.get("tran") or parent_tran or "")
    row = {
        "name": str(node.get("name") or ""),
        "path": path,
        "type": str(node.get("type") or ""),
        "fstype": str(node.get("fstype") or "").lower(),
        "label": str(node.get("label") or "").strip().upper(),
        "mountpoint": str(node.get("mountpoint") or "").strip(),
        "tran": tran,
        "pkname": str(node.get("pkname") or parent_path),
        "rm": bool(node.get("rm")),
    }
    rows.append(row)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            rows.extend(_iter_block_nodes(child, parent_tran=tran, parent_path=path or row["name"]))
    return rows


def discover_setup_logs_partitions() -> list[dict[str, Any]]:
    """Find SETUP_LOGS partitions by label/fstype (not by directory name)."""
    tree = _lsblk_json()
    devices = tree.get("blockdevices") or []
    flat: list[dict[str, Any]] = []
    for node in devices:
        if isinstance(node, dict):
            flat.extend(_iter_block_nodes(node))

    # Parent USB disk paths that also host SETUPHELFER ESP.
    usb_parents: set[str] = set()
    for row in flat:
        if row["type"] == "disk" and row["tran"] == "usb":
            usb_parents.add(row["path"] or f"/dev/{row['name']}")
        if row["label"] == "SETUPHELFER" and row["type"] == "part":
            parent = row["pkname"]
            if parent:
                usb_parents.add(parent if parent.startswith("/") else f"/dev/{parent}")

    candidates: list[dict[str, Any]] = []
    for row in flat:
        if row["type"] != "part":
            continue
        if row["label"] not in LABELS:
            continue
        if row["fstype"] and row["fstype"] not in {"vfat", "fat", "fat32", "msdos"}:
            continue
        if row["label"] == "SETUPHELFER":
            continue
        parent = row["pkname"]
        parent_path = parent if parent.startswith("/") else (f"/dev/{parent}" if parent else "")
        # Prefer USB stick partitions; allow non-USB only when uniquely labeled in tests.
        on_usb = (row["tran"] == "usb") or (parent_path in usb_parents) or row["rm"]
        candidates.append(
            {
                **row,
                "parent_path": parent_path,
                "on_usb": on_usb,
            }
        )
    # Prefer USB-backed partitions.
    usb = [c for c in candidates if c.get("on_usb")]
    return usb or candidates


def findmnt_source(mountpoint: Path) -> str | None:
    rc, out = _run(["findmnt", "-n", "-o", "SOURCE", "--target", str(mountpoint)])
    if rc != 0 or not out:
        return None
    return out.splitlines()[0].strip() or None


def _path_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".setuphelfer-write-probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def validate_mountpoint(mountpoint: Path, *, expected_device: str | None = None) -> dict[str, Any]:
    """Validate that a path is an active mount of the SETUP_LOGS partition."""
    if not mountpoint.exists() or not mountpoint.is_dir():
        return {
            "ok": False,
            "resolution_status": "not_mounted",
            "mount_source_verified": False,
            "writable": False,
            "actual_mountpoint": str(mountpoint),
        }

    source = findmnt_source(mountpoint)
    if not source:
        # Empty shadow directory: exists but not a mount.
        return {
            "ok": False,
            "resolution_status": "not_mounted",
            "mount_source_verified": False,
            "writable": False,
            "actual_mountpoint": str(mountpoint),
            "shadow_directory": True,
        }

    if expected_device:
        # Accept /dev/sdX2 and /dev/disk/by-label/SETUP_LOGS equivalence via resolve.
        try:
            expected_real = Path(expected_device).resolve()
            source_real = Path(source).resolve()
            if expected_real != source_real and expected_device not in source and source not in expected_device:
                return {
                    "ok": False,
                    "resolution_status": "mounted_wrong_source",
                    "mount_source_verified": False,
                    "writable": False,
                    "actual_mountpoint": str(mountpoint),
                    "source": source,
                }
        except OSError:
            if expected_device not in source:
                return {
                    "ok": False,
                    "resolution_status": "mounted_wrong_source",
                    "mount_source_verified": False,
                    "writable": False,
                    "actual_mountpoint": str(mountpoint),
                    "source": source,
                }

    setuphelfer = mountpoint / "setuphelfer"
    writable = _path_writable(setuphelfer if setuphelfer.exists() else mountpoint)
    if not writable:
        return {
            "ok": False,
            "resolution_status": "unwritable",
            "mount_source_verified": True,
            "writable": False,
            "actual_mountpoint": str(mountpoint),
            "source": source,
        }

    return {
        "ok": True,
        "resolution_status": "mounted_valid",
        "mount_source_verified": True,
        "writable": True,
        "actual_mountpoint": str(mountpoint),
        "source": source,
    }


def _existing_valid_mount(device_path: str) -> Path | None:
    # Scan /proc/mounts for this device.
    try:
        lines = Path("/proc/mounts").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        src, tgt = parts[0], parts[1]
        if device_path in src or src.endswith(Path(device_path).name):
            check = validate_mountpoint(Path(tgt), expected_device=device_path)
            if check.get("ok"):
                return Path(tgt)
    return None


def ensure_canonical_mount(device_path: str) -> dict[str, Any]:
    """Accept existing valid mount or bind/mount onto canonical path."""
    existing = _existing_valid_mount(device_path)
    if existing is not None:
        # Bind to canonical for stable path if different.
        if existing.resolve() != CANONICAL_MOUNT:
            CANONICAL_MOUNT.parent.mkdir(parents=True, exist_ok=True)
            if not findmnt_source(CANONICAL_MOUNT):
                _run(["mount", "--bind", str(existing), str(CANONICAL_MOUNT)])
            check = validate_mountpoint(CANONICAL_MOUNT, expected_device=device_path)
            if check.get("ok"):
                return {
                    **check,
                    "device_path": device_path,
                    "canonical_mountpoint": str(CANONICAL_MOUNT),
                    "bound_from": str(existing),
                }
            # Fall back to existing mount if bind failed.
            return {
                **validate_mountpoint(existing, expected_device=device_path),
                "device_path": device_path,
                "canonical_mountpoint": str(existing),
                "bound_from": None,
            }
        return {
            **validate_mountpoint(existing, expected_device=device_path),
            "device_path": device_path,
            "canonical_mountpoint": str(CANONICAL_MOUNT),
        }

    CANONICAL_MOUNT.parent.mkdir(parents=True, exist_ok=True)
    CANONICAL_MOUNT.mkdir(parents=True, exist_ok=True)
    rc, err = _run(["mount", "-t", "vfat", "-o", "rw,flush,umask=0022", device_path, str(CANONICAL_MOUNT)])
    if rc != 0:
        return {
            "ok": False,
            "resolution_status": "not_mounted",
            "mount_source_verified": False,
            "writable": False,
            "device_path": device_path,
            "canonical_mountpoint": str(CANONICAL_MOUNT),
            "error": err[:200],
        }
    check = validate_mountpoint(CANONICAL_MOUNT, expected_device=device_path)
    return {
        **check,
        "device_path": device_path,
        "canonical_mountpoint": str(CANONICAL_MOUNT),
        "freshly_mounted": True,
    }


def write_resolution_state(payload: dict[str, Any]) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": RESOLUTION_SCHEMA,
        "resolved": bool(payload.get("resolved")),
        "device_path": str(payload.get("device_path") or ""),
        "filesystem_label": str(payload.get("filesystem_label") or "SETUP_LOGS"),
        "filesystem_type": str(payload.get("filesystem_type") or ""),
        "canonical_mountpoint": str(payload.get("canonical_mountpoint") or CANONICAL_MOUNT),
        "actual_mountpoint": str(payload.get("actual_mountpoint") or ""),
        "mount_source_verified": bool(payload.get("mount_source_verified")),
        "writable": bool(payload.get("writable")),
        "resolution_status": str(payload.get("resolution_status") or ""),
        "resolved_at": payload.get("resolved_at") or _utc_now(),
        "runtime_fallback_used": bool(payload.get("runtime_fallback_used")),
        "shadow_mount_ignored": bool(payload.get("shadow_mount_ignored")),
    }
    RESOLUTION_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return RESOLUTION_PATH


def write_environment_file(*, setup_logs_root: Path, evidence_root: Path) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(
        "SETUPHELFER_SETUP_LOGS_ROOT={root}\n"
        "SETUPHELFER_EVIDENCE_ROOT={ev}\n"
        "SETUPHELFER_RESCUE_STATE_DIR={state}\n".format(
            root=setup_logs_root,
            ev=evidence_root,
            state=STATE_DIR,
        ),
        encoding="utf-8",
    )
    return ENV_FILE


def load_resolution_state() -> dict[str, Any] | None:
    if not RESOLUTION_PATH.is_file():
        return None
    try:
        data = json.loads(RESOLUTION_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def evidence_root_from_env() -> Path | None:
    raw = os.environ.get("SETUPHELFER_EVIDENCE_ROOT", "").strip()
    if raw:
        return Path(raw)
    setup = os.environ.get("SETUPHELFER_SETUP_LOGS_ROOT", "").strip()
    if setup:
        return Path(setup) / "setuphelfer" / "evidence"
    state = load_resolution_state()
    if state and state.get("resolved") and state.get("actual_mountpoint"):
        return Path(str(state["actual_mountpoint"])) / "setuphelfer" / "evidence"
    return None


def setup_logs_root_from_env() -> Path | None:
    raw = os.environ.get("SETUPHELFER_SETUP_LOGS_ROOT", "").strip()
    if raw:
        return Path(raw)
    state = load_resolution_state()
    if state and state.get("resolved") and state.get("actual_mountpoint"):
        return Path(str(state["actual_mountpoint"]))
    return None


def migrate_bootstrap_to_persistent(*, boot_id: str, evidence_root: Path) -> bool:
    src = BOOTSTRAP_EVIDENCE / boot_id
    if not src.is_dir():
        return False
    dest = evidence_root / "discovery-boot" / boot_id
    try:
        dest.mkdir(parents=True, exist_ok=True)
        for path in src.iterdir():
            if path.is_file():
                shutil.copy2(path, dest / path.name)
        marker = dest / "fallback_migrated.json"
        marker.write_text(
            json.dumps(
                {
                    "schema": "setuphelfer.rescue.fallback-migrated.v1",
                    "boot_id": boot_id,
                    "migrated_at": _utc_now(),
                    "fallback_migrated": True,
                    "storage_mode": "persistent_setup_logs",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def resolve_setup_logs(*, allow_mount: bool = True) -> dict[str, Any]:
    """Resolve SETUP_LOGS to a verified writable mount; never accept shadow dirs."""
    # Explicit env / already resolved state first (host import + live).
    for candidate in (
        os.environ.get("SETUPHELFER_SETUP_LOGS_ROOT", "").strip(),
        os.environ.get("SETUP_LOGS", "").strip(),
    ):
        if not candidate:
            continue
        path = Path(candidate)
        # Host import may pass an already-verified mount; still require findmnt.
        check = validate_mountpoint(path)
        if check.get("ok"):
            evidence = path / "setuphelfer" / "evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            result = {
                "resolved": True,
                "device_path": str(check.get("source") or ""),
                "filesystem_label": "SETUP_LOGS",
                "filesystem_type": "vfat",
                "canonical_mountpoint": str(CANONICAL_MOUNT),
                "actual_mountpoint": str(path),
                "mount_source_verified": True,
                "writable": True,
                "resolution_status": "mounted_valid",
                "shadow_mount_ignored": False,
                "runtime_fallback_used": False,
                "evidence_root": str(evidence),
            }
            write_resolution_state(result)
            write_environment_file(setup_logs_root=path, evidence_root=evidence)
            return result

    parts = discover_setup_logs_partitions()
    if not parts:
        result = {
            "resolved": False,
            "device_path": "",
            "filesystem_label": "SETUP_LOGS",
            "filesystem_type": "",
            "canonical_mountpoint": str(CANONICAL_MOUNT),
            "actual_mountpoint": "",
            "mount_source_verified": False,
            "writable": False,
            "resolution_status": "not_mounted",
            "shadow_mount_ignored": True,
            "runtime_fallback_used": True,
            "evidence_root": str(BOOTSTRAP_EVIDENCE),
        }
        write_resolution_state(result)
        return result

    if len(parts) > 1:
        # Ambiguous: only OK if exactly one is already mounted valid.
        mounted = []
        for part in parts:
            mp = part.get("mountpoint")
            if mp:
                check = validate_mountpoint(Path(mp), expected_device=part["path"])
                if check.get("ok"):
                    mounted.append((part, check))
        if len(mounted) != 1:
            result = {
                "resolved": False,
                "device_path": "",
                "filesystem_label": "SETUP_LOGS",
                "filesystem_type": "",
                "canonical_mountpoint": str(CANONICAL_MOUNT),
                "actual_mountpoint": "",
                "mount_source_verified": False,
                "writable": False,
                "resolution_status": "ambiguous",
                "shadow_mount_ignored": True,
                "runtime_fallback_used": True,
                "evidence_root": str(BOOTSTRAP_EVIDENCE),
                "candidate_count": len(parts),
            }
            write_resolution_state(result)
            return result
        part, check = mounted[0]
    else:
        part = parts[0]
        check = None

    device = str(part["path"])
    if allow_mount:
        mounted = ensure_canonical_mount(device)
    else:
        existing = _existing_valid_mount(device)
        if existing is None:
            mounted = {
                "ok": False,
                "resolution_status": "not_mounted",
                "mount_source_verified": False,
                "writable": False,
                "device_path": device,
            }
        else:
            mounted = {
                **validate_mountpoint(existing, expected_device=device),
                "device_path": device,
                "canonical_mountpoint": str(existing),
            }

    if not mounted.get("ok"):
        result = {
            "resolved": False,
            "device_path": device,
            "filesystem_label": part.get("label") or "SETUP_LOGS",
            "filesystem_type": part.get("fstype") or "",
            "canonical_mountpoint": str(CANONICAL_MOUNT),
            "actual_mountpoint": str(mounted.get("actual_mountpoint") or ""),
            "mount_source_verified": bool(mounted.get("mount_source_verified")),
            "writable": False,
            "resolution_status": str(mounted.get("resolution_status") or "not_mounted"),
            "shadow_mount_ignored": True,
            "runtime_fallback_used": True,
            "evidence_root": str(BOOTSTRAP_EVIDENCE),
        }
        write_resolution_state(result)
        return result

    actual = Path(str(mounted.get("canonical_mountpoint") or mounted.get("actual_mountpoint")))
    evidence = actual / "setuphelfer" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    result = {
        "resolved": True,
        "device_path": device,
        "filesystem_label": part.get("label") or "SETUP_LOGS",
        "filesystem_type": part.get("fstype") or "vfat",
        "canonical_mountpoint": str(CANONICAL_MOUNT),
        "actual_mountpoint": str(actual),
        "mount_source_verified": True,
        "writable": True,
        "resolution_status": "mounted_valid",
        "shadow_mount_ignored": True,
        "runtime_fallback_used": False,
        "evidence_root": str(evidence),
    }
    write_resolution_state(result)
    write_environment_file(setup_logs_root=actual, evidence_root=evidence)
    return result


def select_setup_logs_for_import(
    *,
    explicit_root: str | Path | None = None,
    env_root: str | Path | None = None,
) -> dict[str, Any]:
    """Host-side selection: never pick empty shadow /media/*/SETUP_LOGS dirs."""
    if explicit_root:
        path = Path(explicit_root)
        check = validate_mountpoint(path)
        if not check.get("ok"):
            # On host, findmnt may work; also accept dir with setuphelfer/ if findmnt ok elsewhere.
            if path.is_dir() and (path / "setuphelfer").is_dir() and findmnt_source(path):
                check = validate_mountpoint(path)
        if check.get("ok") or (path.is_dir() and (path / "setuphelfer").is_dir() and findmnt_source(path)):
            return {
                "ok": True,
                "setup_logs_base": path,
                "source": "explicit",
                "mount_source_verified": bool(check.get("mount_source_verified") or findmnt_source(path)),
            }
        return {"ok": False, "code": "explicit_setup_logs_invalid", "path": str(path)}

    env_val = env_root or os.environ.get("SETUP_LOGS") or os.environ.get("SETUPHELFER_SETUP_LOGS_ROOT")
    if env_val:
        path = Path(str(env_val))
        if path.is_dir() and (path / "setuphelfer").is_dir() and findmnt_source(path):
            return {
                "ok": True,
                "setup_logs_base": path,
                "source": "environment",
                "mount_source_verified": True,
            }
        return {"ok": False, "code": "env_setup_logs_invalid", "path": str(path)}

    # lsblk/findmnt based — ignore shadow dirs without mount source.
    parts = discover_setup_logs_partitions()
    valid: list[Path] = []
    for part in parts:
        mp = part.get("mountpoint")
        if not mp:
            continue
        path = Path(mp)
        if not (path / "setuphelfer").is_dir() and not path.is_dir():
            continue
        if not findmnt_source(path):
            continue
        check = validate_mountpoint(path, expected_device=part.get("path"))
        if check.get("ok") or (path / "setuphelfer").is_dir():
            valid.append(path)

    # Also scan common media mounts but require findmnt + setuphelfer.
    for pattern in ("/media/*/SETUP_LOGS*", "/run/media/*/SETUP_LOGS*"):
        for path in sorted(Path("/").glob(pattern.lstrip("/"))):
            if not path.is_dir():
                continue
            if not findmnt_source(path):
                continue
            if not (path / "setuphelfer").is_dir():
                continue
            if path not in valid:
                valid.append(path)

    # Deduplicate
    uniq: list[Path] = []
    seen: set[str] = set()
    for path in valid:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(path)

    if len(uniq) == 1:
        return {
            "ok": True,
            "setup_logs_base": uniq[0],
            "source": "findmnt_lsblk",
            "mount_source_verified": True,
            "shadow_mount_ignored": True,
        }
    if not uniq:
        return {"ok": False, "code": "setup_logs_not_mounted", "shadow_mount_ignored": True}
    return {
        "ok": False,
        "code": "ambiguous_setup_logs_mounts",
        "candidates": [str(p) for p in uniq],
        "shadow_mount_ignored": True,
    }


def main() -> int:
    result = resolve_setup_logs(allow_mount=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("resolved") else 1


if __name__ == "__main__":
    raise SystemExit(main())
