"""
Rescue UI screenshot capture — writes PNG + JSON metadata to SETUP_LOGS only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_setup_logs_persistence import detect_setup_logs_mount

SCREENSHOT_TOOLS = (
    "grim",
    "scrot",
    "import",
    "maim",
    "gnome-screenshot",
    "xwd",
)

LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,48}$", re.IGNORECASE)


def _read_version() -> str:
    try:
        from pathlib import Path as P

        root = P(__file__).resolve().parents[2]
        data = json.loads((root / "config" / "version.json").read_text(encoding="utf-8"))
        return str(data.get("project_version") or "")
    except (OSError, json.JSONDecodeError, ValueError):
        return ""


def _active_vt() -> str | None:
    try:
        out = subprocess.check_output(["fgconsole"], text=True, stderr=subprocess.DEVNULL).strip()
        return out if out.isdigit() else None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _display_resolution() -> str | None:
    display = os.environ.get("DISPLAY", ":0")
    try:
        out = subprocess.check_output(["xrandr", "--current"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if " connected" in line and "+" in line:
                parts = line.split()
                for p in parts:
                    if "x" in p and p[0].isdigit():
                        return p.split("+")[0]
        return None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _pick_tool() -> tuple[str | None, list[str]]:
    for name in SCREENSHOT_TOOLS:
        path = shutil.which(name)
        if not path:
            continue
        if name == "grim":
            return name, [path]
        if name == "scrot":
            return name, [path, "-z"]
        if name == "import":
            return name, [path, "-window", "root"]
        if name == "maim":
            return name, [path, "-u"]
        if name == "gnome-screenshot":
            return name, [path, "-f"]
        if name == "xwd":
            return name, [path, "-root"]
    return None, []


def _screenshot_dir() -> tuple[Path | None, str | None]:
    info = detect_setup_logs_mount()
    mount = info.get("mount_point")
    if not mount or not info.get("persistent"):
        return None, "setup_logs_not_writable"
    base = Path(str(mount)) / "screenshots"
    try:
        base.mkdir(parents=True, exist_ok=True)
        test = base / ".write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
    except OSError as exc:
        return None, f"setup_logs_not_writable:{exc}"
    return base, None


def build_screenshot_capabilities() -> dict[str, Any]:
    tool, _ = _pick_tool()
    dest, block = _screenshot_dir()
    status = "ok" if tool and dest else "blocked"
    errors: list[str] = []
    if not tool:
        errors.append("screenshot_tool_missing")
    if block:
        errors.append(block)
    return {
        "status": status,
        "tool": tool,
        "destination_root": str(dest) if dest else None,
        "display": os.environ.get("DISPLAY"),
        "errors": errors,
        "allowed_tools": [t for t in SCREENSHOT_TOOLS if shutil.which(t)],
    }


def capture_rescue_screenshot(label: str = "ui") -> dict[str, Any]:
    safe_label = (label or "ui").strip().lower().replace(" ", "-")
    if not LABEL_RE.match(safe_label):
        return {"status": "failed", "errors": ["invalid_label"], "path": None, "sha256": None, "tool": None}

    tool, base_cmd = _pick_tool()
    dest_dir, block = _screenshot_dir()
    if not tool or not dest_dir:
        return {
            "status": "blocked",
            "errors": [block or "screenshot_tool_missing"],
            "path": None,
            "sha256": None,
            "tool": tool,
        }

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    png = dest_dir / f"rescue-ui-{ts}-{safe_label}.png"
    meta = dest_dir / f"rescue-ui-{ts}-{safe_label}.json"

    cmd = list(base_cmd)
    if tool == "xwd":
        raw = png.with_suffix(".xwd")
        cmd = [cmd[0], "-root", "-out", str(raw)]
        try:
            subprocess.run(cmd, check=True, timeout=30, env=os.environ.copy())
            convert = shutil.which("convert")
            if not convert:
                return {"status": "failed", "errors": ["xwd_without_convert"], "path": None, "sha256": None, "tool": tool}
            subprocess.run([convert, str(raw), str(png)], check=True, timeout=30)
            raw.unlink(missing_ok=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            return {"status": "failed", "errors": [str(exc)], "path": None, "sha256": None, "tool": tool}
    elif tool == "gnome-screenshot":
        cmd = [cmd[0], "-f", str(png)]
        try:
            subprocess.run(cmd, check=True, timeout=30, env=os.environ.copy())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            return {"status": "failed", "errors": [str(exc)], "path": None, "sha256": None, "tool": tool}
    else:
        cmd.append(str(png))
        try:
            subprocess.run(cmd, check=True, timeout=30, env=os.environ.copy())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            return {"status": "failed", "errors": [str(exc)], "path": None, "sha256": None, "tool": tool}

    if not png.is_file() or png.stat().st_size <= 0:
        return {"status": "failed", "errors": ["empty_screenshot"], "path": None, "sha256": None, "tool": tool}

    digest = hashlib.sha256(png.read_bytes()).hexdigest()
    payload = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "label": safe_label,
        "display": os.environ.get("DISPLAY"),
        "resolution": _display_resolution(),
        "active_vt": _active_vt(),
        "screenshot_tool": tool,
        "file_sha256": digest,
        "version": _read_version(),
        "hostname": os.environ.get("HOSTNAME") or os.uname().nodename,
        "path": str(png),
    }
    meta.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "ok",
        "path": str(png),
        "sha256": digest,
        "tool": tool,
        "metadata_path": str(meta),
        "errors": [],
    }
