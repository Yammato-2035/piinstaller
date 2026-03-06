"""
Support-Bundle: Zip mit Debug-Logs, System-Logs, system_snapshot.json, debug.config.effective.yaml, manifest.json.
Keine Secrets; Sanitizing/Redaction aktiv.
"""

import json
import platform
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

from .config import load_debug_config, get_effective_config_cached
from .logger import get_run_id, set_run_id, _app_info
from .redaction import get_redact_patterns, redact_recursive, redact_string
from .sink import get_sink

BUNDLE_VERSION = "1"
SYSTEM_LOG_DIR = Path("/var/log/pi-installer")
MAX_SYSTEM_LOG_LINES = 2000
MAX_SYSTEM_LOG_FILES = 10


def _run(cmd: List[str], timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _read(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return default


def collect_system_snapshot() -> Dict[str, Any]:
    """
    Minimaler System-Snapshot ohne Secrets: OS, kernel, cpu model, memory, block devices (lsblk),
    mountpoints, boot config checks, network interfaces (ohne WLAN-Keys), app version, run_id.
    """
    out: Dict[str, Any] = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "kernel": _run(["uname", "-r"]),
        "hostname": _read(Path("/etc/hostname")) or _run(["hostname"]),
        "cpu_model": "",
        "memory": {},
        "storage": [],
        "mountpoints": [],
        "boot_config_checks": {},
        "network_interfaces": [],
        "app": _app_info(),
        "run_id": get_run_id() or "",
    }
    # /proc/cpuinfo model name
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.strip().startswith("model name") or line.strip().startswith("Model name"):
                out["cpu_model"] = line.split(":", 1)[-1].strip()
                break
            if "Hardware" in line and not out["cpu_model"]:
                out["cpu_model"] = line.split(":", 1)[-1].strip()
    except Exception:
        pass
    # Memory (MemTotal, MemAvailable)
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:") or line.startswith("MemAvailable:"):
                k, v = line.split(":", 1)
                out["memory"][k.strip()] = v.strip()
    except Exception:
        pass
    # Block devices: lsblk -l -o NAME,SIZE,TYPE,MOUNTPOINT (ohne Serials/Keys)
    try:
        raw = _run(["lsblk", "-l", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"], timeout=5)
        if raw:
            out["lsblk_lines"] = raw.splitlines()[:200]
    except Exception:
        pass
    # Mountpoints (ohne Passwörter): nur mountpoint und device
    try:
        for line in Path("/proc/mounts").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                out["mountpoints"].append({"device": parts[0], "mountpoint": parts[1]})
    except Exception:
        pass
    # Block devices (names only) Fallback
    if not out.get("storage"):
        try:
            for p in Path("/sys/block").iterdir():
                if p.name.startswith("loop") or p.name.startswith("ram"):
                    continue
                out["storage"].append({"name": p.name})
        except Exception:
            pass
    # Boot config: path, exists, hash (no raw content)
    import hashlib
    for name, p in [
        ("boot_firmware_config", Path("/boot/firmware/config.txt")),
        ("boot_config_legacy", Path("/boot/config.txt")),
        ("cmdline", Path("/boot/firmware/cmdline.txt")),
    ]:
        entry: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
        if p.exists():
            try:
                b = p.read_bytes()
                entry["content_hash"] = hashlib.sha256(b).hexdigest()[:16]
            except Exception:
                pass
        out["boot_config_checks"][name] = entry
    try:
        fstab = Path("/etc/fstab")
        if fstab.exists():
            out["fstab_hash"] = hashlib.sha256(fstab.read_bytes()).hexdigest()[:16]
    except Exception:
        pass
    try:
        osr = Path("/etc/os-release")
        if osr.exists():
            out["os_release"] = _read(osr).splitlines()[:30]
    except Exception:
        pass
    out["uname_a"] = _run(["uname", "-a"])
    out["python_version"] = platform.python_version()
    # Network interfaces (name only, no keys)
    try:
        for p in Path("/sys/class/net").iterdir():
            if p.name == "lo":
                continue
            out["network_interfaces"].append({"name": p.name})
    except Exception:
        pass
    return out


def _redact_text_line_by_line(text: str, patterns: List[Any]) -> str:
    """Redaktion zeilenweise (spart RAM bei großen Logs)."""
    if not text or not patterns:
        return text
    compiled = compile_patterns(patterns) if patterns and isinstance(patterns[0], str) else patterns
    return "\n".join(redact_string(line, compiled) for line in text.splitlines())


def _collect_system_logs(max_lines: int = MAX_SYSTEM_LOG_LINES, max_files: int = MAX_SYSTEM_LOG_FILES) -> str:
    """Liest letzte Zeilen aus /var/log/pi-installer/* (begrenzt)."""
    if not SYSTEM_LOG_DIR.is_dir():
        return ""
    lines: List[str] = []
    try:
        files = sorted(SYSTEM_LOG_DIR.iterdir(), key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True)
        for fp in files[:max_files]:
            if not fp.is_file():
                continue
            try:
                for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
                    lines.append(line)
                    if len(lines) >= max_lines:
                        break
            except Exception:
                continue
            if len(lines) >= max_lines:
                break
    except Exception:
        pass
    return "\n".join(lines[-max_lines:]) if lines else ""


def create_support_bundle(
    output_dir: Optional[Path] = None,
    run_id_override: Optional[str] = None,
    max_log_lines: Optional[int] = None,
    include_system_logs: Optional[bool] = None,
    include_debug_logs: Optional[bool] = None,
    include_snapshot: Optional[bool] = None,
) -> Path:
    """
    Erzeugt output_dir/piinstaller-support-<timestamp>-<run_id>.zip mit:
    - Debug-Logs (redigiert), System-Logs /var/log/pi-installer (begrenzt)
    - system_snapshot.json (redigiert)
    - debug.config.effective.yaml
    - manifest.json (bundle_version, created_at, run_id, file list, redaction_enabled)
    """
    cfg = load_debug_config()
    export_cfg = (cfg.get("global") or {}).get("export") or {}
    if not export_cfg.get("enabled", True):
        raise RuntimeError("Export is disabled in debug.config")
    out_dir = Path(output_dir or export_cfg.get("output_dir") or ".")
    out_dir.mkdir(parents=True, exist_ok=True)
    rid = run_id_override or get_run_id() or set_run_id()
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    zip_name = f"piinstaller-support-{ts}-{rid[:8] if len(rid) >= 8 else rid}.zip"
    zip_path = out_dir / zip_name
    max_log_lines = int(max_log_lines if max_log_lines is not None else export_cfg.get("max_log_lines", 5000))
    include_snapshot = include_snapshot if include_snapshot is not None else export_cfg.get("include_system_snapshot", True)
    include_logs = include_debug_logs if include_debug_logs is not None else export_cfg.get("include_recent_logs", True)
    include_syslogs = include_system_logs if include_system_logs is not None else True
    patterns = get_redact_patterns()
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "bundle_version": BUNDLE_VERSION,
            "created_at": created_at,
            "timestamp": ts,
            "run_id": rid,
            "redaction_enabled": bool(patterns),
            "config_summary": {
                "max_log_lines": max_log_lines,
                "include_snapshot": include_snapshot,
                "include_debug_logs": include_logs,
                "include_system_logs": include_syslogs,
            },
            "files": [],
        }

        if include_snapshot:
            snapshot = collect_system_snapshot()
            if patterns:
                snapshot = redact_recursive(snapshot, patterns)
            zf.writestr("system_snapshot.json", json.dumps(snapshot, indent=2, ensure_ascii=False))
            manifest["files"].append("system_snapshot.json")

        effective = get_effective_config_cached()
        effective_export = {k: v for k, v in effective.items() if not str(k).startswith("_")}
        if yaml:
            eff_str = yaml.dump(effective_export, default_flow_style=False, allow_unicode=True)
        else:
            eff_str = json.dumps(effective_export, indent=2, ensure_ascii=False)
        zf.writestr("debug.config.effective.yaml", eff_str)
        manifest["files"].append("debug.config.effective.yaml")

        if include_logs:
            sink = get_sink()
            if sink:
                log_files = sink.list_log_files()
                all_lines: List[str] = []
                for fp in log_files:
                    try:
                        for line in fp.read_text(encoding="utf-8").splitlines():
                            all_lines.append(line)
                    except Exception:
                        continue
                tail = all_lines[-max_log_lines:] if len(all_lines) > max_log_lines else all_lines
                if tail and patterns:
                    redacted_lines = []
                    for line in tail:
                        try:
                            obj = json.loads(line)
                            obj = redact_recursive(obj, patterns)
                            redacted_lines.append(json.dumps(obj, ensure_ascii=False))
                        except Exception:
                            redacted_lines.append(line)
                    tail = redacted_lines
                if tail:
                    zf.writestr("logs/debug_recent.jsonl", "\n".join(tail))
                    manifest["files"].append("logs/debug_recent.jsonl")

        if include_syslogs:
            system_log_content = _collect_system_logs(max_lines=MAX_SYSTEM_LOG_LINES, max_files=MAX_SYSTEM_LOG_FILES)
            if system_log_content and patterns:
                system_log_content = _redact_text_line_by_line(system_log_content, patterns)
            if system_log_content:
                zf.writestr("logs/system_pi_installer.txt", system_log_content)
                manifest["files"].append("logs/system_pi_installer.txt")

        manifest["files"].append("manifest.json")
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return zip_path
