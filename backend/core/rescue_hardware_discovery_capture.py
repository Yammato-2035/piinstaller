"""Read-only hardware_discovery capture for dual-NVMe ASUS diagnosis (PI-RS-ASUS-PHYSICAL-DIAG-003).

Writes evidence under SETUP_LOGS. Never formats, mounts RW, or flashes firmware.
Device paths (/dev/nvme0n1) are capture-time only — identity uses serial/EUI/NGUID/PCI.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.rescue_machine_identity_profiles import (
    PROFILE_ASUS_ROG_GABRIEL,
    bind_gabriel_operator_profile,
    build_machine_identity,
    hash_serial,
    mask_serial,
    read_dmi_fields,
)
from core.rescue_nvme_install_target import evaluate_nvme_health, normalize_nvme_entry, stable_nvme_identity_key
from core.rescue_payload_version import rescue_payload_version
from core.rescue_run_type_contract import evaluate_run_control
from core.rescue_windows11_install_diag import scan_windows_setup_evidence

CONTRACT_VERSION = 2
SCHEMA_VERSION = "1.1"
RUN_TYPE = "hardware_discovery"
TERMINAL_STATUSES = frozenset({"complete", "partial", "failed", "cancelled"})

# Ordered TUI/progress phases for text hardware_discovery (GUI N/A).
CAPTURE_PHASES: tuple[tuple[str, str], ...] = (
    ("device_binding", "Gerätebindung"),
    ("bios_inventory", "BIOS-Inventar"),
    ("nvme_identity", "NVMe-Identität"),
    ("nvme_smart", "NVMe-SMART"),
    ("nvme_error_logs", "NVMe-Error-Logs"),
    ("kernel_storage", "Kernel-/PCIe-Auswertung"),
    ("partition_inventory", "Partitionen und EFI"),
    ("windows_setup_logs", "Windows-Setup-Logs"),
    ("redaction", "Redaction"),
    ("manifest_checksums", "Manifest und Prüfsummen"),
    ("capture_complete", "Capture abgeschlossen"),
)

PROGRESS_PATH = Path("/run/setuphelfer-rescue/hardware-discovery-progress.json")
SAFE_REMOVE_HINT = "Diagnose abgeschlossen – Stick kann nach dem Herunterfahren entfernt werden."
DO_NOT_REMOVE_HINT = "Stick noch nicht entfernen – Diagnose wird finalisiert."

RunFn = Callable[[Sequence[str], float], tuple[int, str, str]]
ProgressFn = Callable[[str, str, Mapping[str, Any]], None]

_ZERO_EUI_RE = re.compile(r"^0+$")
_KERNEL_TOKENS = (
    "nvme",
    "pcie",
    "aer",
    "timeout",
    "reset",
    "I/O error",
    "blk_update_request",
    "buffer I/O",
    "controller",
    "namespace",
    "amd",
    "iommu",
    "acpi",
    "thermal",
    "mce",
    "machine check",
    "vmd",
    "rst",
    "raid",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_run(cmd: Sequence[str], timeout: float = 60.0) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def _parse_json(text: str) -> Any | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def normalize_hex_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        raw = f"{value:x}"
    else:
        raw = str(value).strip().lower().replace(":", "").replace("-", "").replace(" ", "")
    if not raw or _ZERO_EUI_RE.match(raw):
        return None
    return raw


def redact_text(text: str, secrets: Sequence[str]) -> str:
    out = text or ""
    for secret in secrets:
        s = (secret or "").strip()
        if len(s) < 4:
            continue
        out = out.replace(s, mask_serial(s) if len(s) > 4 else "****")
    # Emails / product keys (best-effort)
    out = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", out)
    out = re.sub(r"\b[A-Z0-9]{5}(?:-[A-Z0-9]{5}){4}\b", "[redacted-product-key]", out)
    return out


def coerce_int(value: Any, default: int = 0) -> int:
    """Best-effort int for nvme-cli JSON (decimal, 0x-hex, single-element lists)."""
    if value is None or value is False:
        return default
    if value is True:
        return 1
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return default
    if isinstance(value, (list, tuple)):
        if not value:
            return default
        return coerce_int(value[0], default=default)
    if isinstance(value, Mapping):
        for key in ("value", "raw", "normalized", "critical_warning", "media_errors"):
            if key in value:
                return coerce_int(value.get(key), default=default)
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        if text.lower().startswith("0x"):
            return int(text, 16)
        return int(text, 10)
    except (TypeError, ValueError):
        try:
            return int(float(text))
        except (TypeError, ValueError, OverflowError):
            return default


def classify_smart_health(smart: Mapping[str, Any], *, kernel_critical: bool = False) -> str:
    if not smart:
        return "UNKNOWN"
    if "critical_warning" not in smart and "media_errors" not in smart:
        return "UNKNOWN"
    cw = coerce_int(smart.get("critical_warning"))
    media = coerce_int(smart.get("media_errors") or smart.get("media_and_data_integrity_errors"))
    if cw != 0 or media > 0 or kernel_critical:
        return "CRITICAL"
    unsafe = coerce_int(smart.get("unsafe_shutdowns"))
    warn_temp = coerce_int(smart.get("warning_temp_time"))
    err_entries = coerce_int(smart.get("num_err_log_entries"))
    if unsafe > 50 or warn_temp > 0 or err_entries > 0:
        return "WARNING"
    return "HEALTHY"


def compute_nvme_identity_hash(fields: Mapping[str, Any]) -> str:
    parts = [
        str(fields.get("model") or "").strip(),
        str(fields.get("serial_hash") or "").strip(),
        str(fields.get("eui64") or "").strip(),
        str(fields.get("nguid") or "").strip(),
        str(fields.get("namespace_id") or "").strip(),
        str(fields.get("pci_address") or "").strip(),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def check_tooling(run: RunFn | None = None) -> dict[str, Any]:
    run = run or _default_run
    tools = (
        "nvme",
        "smartctl",
        "lsblk",
        "blkid",
        "lspci",
        "udevadm",
        "journalctl",
        "dmesg",
        "dmidecode",
        "efibootmgr",
        "mokutil",
        "mount",
        "find",
        "sha256sum",
        "parted",
        "sgdisk",
        "fdisk",
    )
    present: dict[str, bool] = {}
    for name in tools:
        rc, out, _ = run(["bash", "-lc", f"command -v {name}"], 5.0)
        present[name] = rc == 0 and bool(out.strip())
    missing = [k for k, ok in present.items() if not ok]
    return {
        "tools": present,
        "missing": missing,
        "sufficient_for_nvme_capture": all(present.get(t) for t in ("nvme", "lsblk", "lspci")),
    }


def _pci_address_for_nvme(ns_path: str, run: RunFn) -> str:
    name = Path(ns_path).name  # nvme0n1
    link = Path(f"/sys/class/block/{name}/device")
    try:
        resolved = link.resolve()
        # .../0000:04:00.0/nvme/nvme0
        for part in resolved.parts:
            if re.match(r"^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]$", part):
                return part
    except OSError:
        pass
    rc, out, _ = run(["bash", "-lc", f"readlink -f /sys/class/block/{name}/device"], 5.0)
    m = re.search(r"([0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f])", out or "")
    return m.group(1) if m else ""


def _sysfs_path_for_nvme(ns_path: str, run: RunFn) -> str:
    name = Path(ns_path).name
    rc, out, _ = run(["bash", "-lc", f"readlink -f /sys/class/block/{name}/device"], 5.0)
    return (out or "").strip()


def collect_nvme_inventory(*, run: RunFn | None = None) -> dict[str, Any]:
    run = run or _default_run
    raw: dict[str, Any] = {"nvme_list": None, "nvme_list_subsys": None, "controllers": [], "namespaces": []}
    redacted: list[dict[str, Any]] = []
    missing_fields_global: list[str] = []

    rc, out, err = run(["nvme", "list", "-o", "json"], 30.0)
    raw["nvme_list"] = _parse_json(out) if rc == 0 else {"error": err or out, "rc": rc}
    rc2, out2, _ = run(["nvme", "list-subsys", "-o", "json"], 30.0)
    raw["nvme_list_subsys"] = _parse_json(out2) if rc2 == 0 else None

    devices = []
    if isinstance(raw["nvme_list"], dict):
        devices = list(raw["nvme_list"].get("Devices") or [])
    # Fallback: enumerate /dev/nvme*n1
    if not devices:
        rc, out, _ = run(["bash", "-lc", "ls -1 /dev/nvme*n1 2>/dev/null"], 5.0)
        for line in (out or "").splitlines():
            if line.startswith("/dev/"):
                devices.append({"DevicePath": line.strip()})

    for dev in devices:
        if not isinstance(dev, Mapping):
            continue
        ns_path = str(dev.get("DevicePath") or dev.get("device_path") or "")
        if not ns_path:
            continue
        m = re.match(r"(/dev/nvme\d+)", ns_path)
        ctrl = m.group(1) if m else ""
        nsid = 1
        nm = re.search(r"n(\d+)$", ns_path)
        if nm:
            nsid = coerce_int(nm.group(1), default=1)

        ctrl_json = None
        ns_json = None
        serial = str(dev.get("SerialNumber") or "")
        model = str(dev.get("ModelNumber") or dev.get("Model") or "")
        fw = str(dev.get("Firmware") or "")
        size = coerce_int(dev.get("PhysicalSize"))

        if ctrl:
            rc, out, err = run(["nvme", "id-ctrl", ctrl, "-o", "json"], 30.0)
            ctrl_json = _parse_json(out) if rc == 0 else {"error": err or out, "rc": rc}
            raw["controllers"].append({"path": ctrl, "id_ctrl": ctrl_json})
            if isinstance(ctrl_json, dict) and "error" not in ctrl_json:
                serial = serial or str(ctrl_json.get("sn") or "").strip()
                model = model or str(ctrl_json.get("mn") or "").strip()
                fw = fw or str(ctrl_json.get("fr") or "").strip()
                if not size:
                    try:
                        size = coerce_int(ctrl_json.get("tnvmcap"))
                    except Exception:  # noqa: BLE001
                        size = 0

        rc, out, err = run(["nvme", "id-ns", ns_path, "-o", "json"], 30.0)
        ns_json = _parse_json(out) if rc == 0 else {"error": err or out, "rc": rc}
        raw["namespaces"].append({"path": ns_path, "id_ns": ns_json})

        eui = normalize_hex_id(ns_json.get("eui64") if isinstance(ns_json, dict) else None)
        nguid = normalize_hex_id(ns_json.get("nguid") if isinstance(ns_json, dict) else None)
        ns_uuid = None
        if isinstance(ns_json, dict):
            ns_uuid = normalize_hex_id(ns_json.get("uuid")) or (
                str(ns_json.get("uuid")).strip() if ns_json.get("uuid") else None
            )

        pci = _pci_address_for_nvme(ns_path, run)
        sysfs = _sysfs_path_for_nvme(ns_path, run)
        serial_hash = hash_serial(serial)
        missing = []
        if not serial_hash:
            missing.append("serial")
        if not eui:
            missing.append("eui64")
        if not nguid:
            missing.append("nguid")
        if not pci:
            missing.append("pci_address")
        if not model:
            missing.append("model")
        missing_fields_global.extend(missing)

        identity_fields = {
            "model": model.strip(),
            "serial_hash": serial_hash,
            "eui64": eui or "",
            "nguid": nguid or "",
            "namespace_id": nsid,
            "pci_address": pci,
        }
        identity_hash = compute_nvme_identity_hash(identity_fields)
        confidence = "high"
        if not serial_hash:
            confidence = "low"
        elif (not eui and not nguid) or not pci:
            confidence = "medium"

        entry_raw = {
            "device_path": ns_path,
            "controller": ctrl,
            "model": model.strip(),
            "serial": serial,  # protected raw evidence only
            "serial_masked": mask_serial(serial),
            "serial_hash": serial_hash,
            "firmware_revision": fw.strip(),
            "size_bytes": size,
            "namespace_id": nsid,
            "eui64": eui,
            "nguid": nguid,
            "uuid": ns_uuid,
            "pci_address": pci,
            "sysfs_path": sysfs,
            "subnqn": (str(ctrl_json.get("subnqn")).strip() if isinstance(ctrl_json, dict) else ""),
            "pci_device_id": "",
            "missing_identity_fields": missing,
            "identity_confidence": confidence,
            "nvme_identity_hash": identity_hash,
            "write_allowed": False,
        }
        # Enrich via normalize for shared consumers
        normalized = normalize_nvme_entry(entry_raw)
        normalized["eui64"] = eui
        normalized["nguid"] = nguid
        normalized["nvme_identity_hash"] = identity_hash
        normalized["identity_confidence"] = confidence
        normalized["missing_identity_fields"] = missing
        # Recompute shared identity_key for rename stability
        normalized["identity_key"] = stable_nvme_identity_key(normalized)
        redacted.append(
            {
                **{k: v for k, v in normalized.items() if k != "serial"},
                "serial_masked": mask_serial(serial),
                "serial_hash": serial_hash,
                "nvme_identity_hash": identity_hash,
            }
        )
        # Keep serial only in raw structure
        raw.setdefault("identity_raw", []).append(entry_raw)

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "raw": raw,
        "devices_redacted": redacted,
        "device_count": len(redacted),
        "missing_fields_summary": sorted(set(missing_fields_global)),
        "write_allowed": False,
    }


def resolve_live_nvme_paths_by_identity_hash(
    *,
    identity_hash: str,
    run: RunFn | None = None,
) -> dict[str, Any]:
    """Re-resolve Linux device paths via identity hash — never trust a stale /dev/nvme name alone."""
    run = run or _default_run
    target = (identity_hash or "").strip()
    if not target:
        return {"ok": False, "controller": "", "device_path": "", "reason": "empty_identity_hash"}
    fresh = collect_nvme_inventory(run=run)
    for entry in fresh.get("devices_redacted") or []:
        if str(entry.get("nvme_identity_hash") or "") == target:
            return {
                "ok": True,
                "controller": str(entry.get("controller") or ""),
                "device_path": str(entry.get("device_path") or ""),
                "firmware_revision": entry.get("firmware_revision"),
                "reason": "resolved_by_identity_hash",
            }
    return {"ok": False, "controller": "", "device_path": "", "reason": "identity_hash_not_found"}


def _smart_field_bundle(smart: Mapping[str, Any] | None, firmware: Any) -> dict[str, Any]:
    smart = smart if isinstance(smart, dict) else {}
    return {
        "firmware_revision": firmware,
        "critical_warning": coerce_int(smart.get("critical_warning")) if "critical_warning" in smart else None,
        "composite_temperature": coerce_int(smart.get("temperature")) if "temperature" in smart else None,
        "available_spare": coerce_int(smart.get("avail_spare")) if "avail_spare" in smart else None,
        "available_spare_threshold": coerce_int(smart.get("spare_thresh")) if "spare_thresh" in smart else None,
        "percentage_used": coerce_int(smart.get("percent_used")) if "percent_used" in smart else None,
        "data_units_read": coerce_int(smart.get("data_units_read")) if "data_units_read" in smart else None,
        "data_units_written": coerce_int(smart.get("data_units_written")) if "data_units_written" in smart else None,
        "host_read_commands": coerce_int(smart.get("host_read_commands")) if "host_read_commands" in smart else None,
        "host_write_commands": coerce_int(smart.get("host_write_commands")) if "host_write_commands" in smart else None,
        "controller_busy_time": coerce_int(smart.get("controller_busy_time")) if "controller_busy_time" in smart else None,
        "power_cycles": coerce_int(smart.get("power_cycles")) if "power_cycles" in smart else None,
        "power_on_hours": coerce_int(smart.get("power_on_hours")) if "power_on_hours" in smart else None,
        "unsafe_shutdowns": coerce_int(smart.get("unsafe_shutdowns")) if "unsafe_shutdowns" in smart else None,
        "media_errors": coerce_int(smart.get("media_errors")) if "media_errors" in smart else None,
        "num_err_log_entries": coerce_int(smart.get("num_err_log_entries")) if "num_err_log_entries" in smart else None,
        "warning_temp_time": coerce_int(smart.get("warning_temp_time")) if "warning_temp_time" in smart else None,
        "critical_comp_time": coerce_int(smart.get("critical_comp_time")) if "critical_comp_time" in smart else None,
        "temperature_sensors": {
            "sensor_1": coerce_int(smart.get("temperature_sensor_1")) if "temperature_sensor_1" in smart else None,
            "sensor_2": coerce_int(smart.get("temperature_sensor_2")) if "temperature_sensor_2" in smart else None,
        },
    }


def collect_nvme_health(*, inventory: Mapping[str, Any], run: RunFn | None = None) -> dict[str, Any]:
    run = run or _default_run
    devices_out: list[dict[str, Any]] = []
    smart_raw: list[dict[str, Any]] = []
    error_raw: list[dict[str, Any]] = []

    for entry in inventory.get("devices_redacted") or []:
        identity_hash = str(entry.get("nvme_identity_hash") or "")
        try:
            resolved = resolve_live_nvme_paths_by_identity_hash(identity_hash=identity_hash, run=run)
            if resolved.get("ok"):
                ctrl = str(resolved.get("controller") or "")
                ns = str(resolved.get("device_path") or "")
                resolve_status = str(resolved.get("reason") or "resolved_by_identity_hash")
            else:
                # Fall back to inventory paths when live re-scan cannot match (tests / transient sysfs).
                ctrl = str(entry.get("controller") or "")
                ns = str(entry.get("device_path") or "")
                resolve_status = f"fallback_entry_paths:{resolved.get('reason')}"
            smart: Any = {}
            err_log: Any = None
            smartctl: Any = None
            capture_status = "failed"

            if not ctrl and not ns:
                devices_out.append(
                    {
                        "nvme_identity_hash": identity_hash,
                        "device_path": ns,
                        "controller": ctrl,
                        "firmware_revision": entry.get("firmware_revision"),
                        "smart": _smart_field_bundle(None, entry.get("firmware_revision")),
                        "health_label": "UNKNOWN",
                        "capture_status": "failed",
                        "resolve_status": resolve_status,
                        "write_allowed": False,
                    }
                )
                continue

            if ctrl:
                rc, out, err = run(["nvme", "smart-log", ctrl, "-o", "json"], 30.0)
                smart = _parse_json(out) if rc == 0 else {}
                smart_raw.append(
                    {
                        "path": ctrl,
                        "nvme_identity_hash": identity_hash,
                        "rc": rc,
                        "smart": smart,
                        "stderr": err[:500] if err else "",
                    }
                )
                rc_e, out_e, err_e = run(["nvme", "error-log", ctrl, "--log-entries=64", "-o", "json"], 60.0)
                err_log = _parse_json(out_e) if rc_e == 0 else {"rc": rc_e, "error": err_e or out_e}
                error_raw.append({"path": ctrl, "nvme_identity_hash": identity_hash, "error_log": err_log})
            if ns:
                rc, out, err = run(["smartctl", "-x", "-j", ns], 60.0)
                smartctl = _parse_json(out) if rc == 0 else {"rc": rc, "error": err or out[:500]}

            if isinstance(smart, dict) and smart:
                capture_status = "complete"
            elif isinstance(smartctl, dict) and "error" not in smartctl:
                capture_status = "partial"
            elif ctrl or ns:
                capture_status = "failed"

            health_label = classify_smart_health(smart if isinstance(smart, dict) else {})
            eval_in = {
                **entry,
                "smart_status": health_label.lower(),
                "critical_warning": coerce_int((smart or {}).get("critical_warning")) if isinstance(smart, dict) else 0,
                "media_errors": coerce_int((smart or {}).get("media_errors")) if isinstance(smart, dict) else 0,
            }
            health = evaluate_nvme_health(eval_in)
            entries = err_log.get("errors") or err_log.get("Entries") if isinstance(err_log, dict) else None
            devices_out.append(
                {
                    "nvme_identity_hash": identity_hash,
                    "device_path": ns,
                    "controller": ctrl,
                    "firmware_revision": entry.get("firmware_revision") or resolved.get("firmware_revision"),
                    "smart": _smart_field_bundle(
                        smart if isinstance(smart, dict) else None,
                        entry.get("firmware_revision") or resolved.get("firmware_revision"),
                    ),
                    "health_label": health_label,
                    "health_eval": health,
                    "capture_status": capture_status,
                    "resolve_status": resolve_status,
                    "smartctl_present": isinstance(smartctl, dict) and "error" not in smartctl,
                    "error_log_entries": len(entries) if isinstance(entries, (list, tuple)) else 0,
                    "write_allowed": False,
                }
            )
        except Exception as exc:  # noqa: BLE001 — one drive must not abort sibling SMART capture
            devices_out.append(
                {
                    "nvme_identity_hash": identity_hash,
                    "device_path": str(entry.get("device_path") or ""),
                    "controller": str(entry.get("controller") or ""),
                    "firmware_revision": entry.get("firmware_revision"),
                    "smart": _smart_field_bundle(None, entry.get("firmware_revision")),
                    "health_label": "UNKNOWN",
                    "capture_status": "failed",
                    "resolve_status": "device_exception",
                    "error": f"{type(exc).__name__}:{exc}",
                    "write_allowed": False,
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "devices": devices_out,
        "smart_raw": smart_raw,
        "error_logs_raw": error_raw,
        "write_allowed": False,
    }


def collect_kernel_storage_findings(*, run: RunFn | None = None) -> dict[str, Any]:
    run = run or _default_run
    rc, journal, _ = run(["journalctl", "-k", "-b", "--no-pager"], 120.0)
    rc2, dmesg, _ = run(["dmesg"], 60.0)
    blob = f"{journal}\n{dmesg}"
    hits: list[dict[str, Any]] = []
    for token in _KERNEL_TOKENS:
        count = len(re.findall(re.escape(token), blob, flags=re.I))
        if count:
            sample_lines = [ln for ln in blob.splitlines() if token.lower() in ln.lower()][:8]
            hits.append({"token": token, "count": count, "samples": sample_lines})
    critical = any(
        h["token"] in {"I/O error", "blk_update_request", "buffer I/O", "mce", "machine check"} and h["count"] > 0
        for h in hits
    )
    resets = next((h["count"] for h in hits if h["token"] == "reset"), 0)
    return {
        "schema_version": SCHEMA_VERSION,
        "journal_rc": rc,
        "dmesg_rc": rc2,
        "filtered_hits": hits,
        "critical_io_or_mce": critical,
        "reset_mentions": resets,
        "pci_noaer_on_cmdline": "pci=noaer" in Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
        if Path("/proc/cmdline").is_file()
        else False,
        "write_allowed": False,
    }


def collect_partition_and_boot_inventory(*, run: RunFn | None = None) -> dict[str, Any]:
    run = run or _default_run
    rc, lsblk, _ = run(["lsblk", "--json", "-O"], 60.0)
    rc2, blkid, _ = run(["blkid"], 30.0)
    rc3, fdisk, _ = run(["fdisk", "-l"], 60.0)
    rc4, efi, _ = run(["efibootmgr", "-v"], 15.0)
    parted_out: list[dict[str, Any]] = []
    sgdisk_out: list[dict[str, Any]] = []
    for ns in re.findall(r"/dev/nvme\dn1", lsblk or "") or []:
        pass
    # Discover nvme namespaces from lsblk json
    ns_paths: list[str] = []
    parsed = _parse_json(lsblk)
    if isinstance(parsed, dict):
        for block in parsed.get("blockdevices") or []:
            name = str(block.get("name") or "")
            path = str(block.get("path") or (f"/dev/{name}" if name else ""))
            if re.match(r"/dev/nvme\d+n\d+$", path):
                ns_paths.append(path)
    if not ns_paths:
        rc, out, _ = run(["bash", "-lc", "ls -1 /dev/nvme*n1 2>/dev/null"], 5.0)
        ns_paths = [ln.strip() for ln in (out or "").splitlines() if ln.startswith("/dev/")]

    for path in ns_paths:
        rc, out, err = run(["parted", "-s", path, "unit", "s", "print"], 30.0)
        parted_out.append({"path": path, "rc": rc, "out": out, "err": err[:300] if err else ""})
        rc, out, err = run(["sgdisk", "-p", path], 30.0)
        sgdisk_out.append({"path": path, "rc": rc, "out": out, "err": err[:300] if err else ""})

    return {
        "schema_version": SCHEMA_VERSION,
        "lsblk": _parse_json(lsblk) if rc == 0 else None,
        "blkid_text": blkid if rc2 == 0 else "",
        "fdisk_text": fdisk if rc3 == 0 else "",
        "efibootmgr": efi if rc4 == 0 else "",
        "efibootmgr_available": rc4 == 0,
        "parted": parted_out,
        "sgdisk": sgdisk_out,
        "write_allowed": False,
    }


def mount_ntfs_read_only(
    source: str,
    mount_point: Path,
    *,
    run: RunFn | None = None,
    allow_dirty_force_ro: bool = True,
) -> dict[str, Any]:
    """Mount NTFS read-only for Panther/Rollback capture.

    Never mounts read-write. Never clears hibernation files.
    After a hung Windows Setup the volume is often dirty; then a documented
    ``ro,force`` recovery mount may be used (still read-only).
    """
    run = run or _default_run
    mount_point.mkdir(parents=True, exist_ok=True)
    attempts: list[tuple[str, str, str]] = [
        ("ntfs3", "ro,norecover", "mounted_ro"),
        ("ntfs-3g", "ro,norecover", "mounted_ro"),
        ("ntfs-3g", "ro,remove_hiberfile=0", "mounted_ro"),
    ]
    if allow_dirty_force_ro:
        # Last resort after unclean/dirty Stage-A hang — still RO, no write/repair.
        attempts.append(("ntfs-3g", "ro,force", "mounted_ro_force_recovery"))

    last_err = ""
    for fstype, opts, ok_status in attempts:
        rc, out, err = run(["mount", "-t", fstype, "-o", opts, source, str(mount_point)], 30.0)
        combined = f"{out}\n{err}".lower()
        last_err = (err or out or "")[:500]
        if rc == 0:
            _rc_f, findmnt, _err_f = run(["findmnt", "-no", "OPTIONS", str(mount_point)], 5.0)
            ro = "ro" in (findmnt or "") or "ro" in opts.split(",")
            if not ro:
                _umount(mount_point, run)
                return {
                    "source": source,
                    "mountpoint": str(mount_point),
                    "options": opts,
                    "fstype": fstype,
                    "exitcode": 1,
                    "read_only_confirmed": False,
                    "status": "ntfs_read_only_mount_blocked",
                    "error": "mount_not_read_only",
                }
            return {
                "source": source,
                "mountpoint": str(mount_point),
                "options": opts,
                "fstype": fstype,
                "exitcode": 0,
                "read_only_confirmed": True,
                "status": ok_status,
                "dirty_force_used": ok_status == "mounted_ro_force_recovery",
            }
        # Continue trying safer RO options; do not abort the whole chain on dirty.
        if "hiber" in combined and "force" not in opts:
            continue
    return {
        "source": source,
        "mountpoint": str(mount_point),
        "options": "",
        "exitcode": 1,
        "read_only_confirmed": False,
        "status": "ntfs_read_only_mount_blocked",
        "error": last_err or "mount_failed",
    }


def _umount(path: Path, run: RunFn) -> None:
    run(["umount", str(path)], 15.0)


def collect_windows_setup_logs(
    *,
    ntfs_sources: Sequence[str],
    work_root: Path,
    run: RunFn | None = None,
    nvme_hash_by_part: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    run = run or _default_run
    mounts: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    roots: list[Path] = []
    for idx, source in enumerate(ntfs_sources):
        mp = work_root / f"ntfs-ro-{idx}"
        result = mount_ntfs_read_only(source, mp, run=run)
        mounts.append(result)
        status = str(result.get("status") or "")
        if status in {"mounted_ro", "mounted_ro_force_recovery"} and result.get("read_only_confirmed"):
            roots.append(mp)
        elif status.startswith("mounted_ro"):
            _umount(mp, run)
    scan = scan_windows_setup_evidence(roots)
    for item in scan.get("files") or []:
        path = Path(str(item.get("path") or ""))
        try:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            size = path.stat().st_size
        except OSError:
            digest, mtime, size = "", "", 0
        # relative path under mount
        rel = str(path)
        for root in roots:
            try:
                rel = str(path.relative_to(root))
                break
            except ValueError:
                continue
        files.append(
            {
                "source_nvme_hash": (nvme_hash_by_part or {}).get(str(path), ""),
                "partition_uuid": "",
                "relative_path": rel,
                "size_bytes": size,
                "mtime": mtime,
                "sha256": digest,
                "log_type": path.name,
                "copy_status": "indexed_not_copied",
                "redaction_status": "pending",
                "error_classes": item.get("error_classes"),
            }
        )
    for root in roots:
        _umount(root, run)

    panther = any("panther" in (f.get("relative_path") or "").lower() for f in files)
    rollback = any("rollback" in (f.get("relative_path") or "").lower() for f in files)
    return {
        "schema_version": SCHEMA_VERSION,
        "mounts": mounts,
        "files": files,
        "scan_status": scan.get("status"),
        "error_classes": scan.get("error_classes"),
        "panther_found": panther,
        "rollback_found": rollback,
        "windows_files_modified": False,
        "write_allowed": False,
    }


def build_cause_matrix(
    *,
    nvme_health: Mapping[str, Any],
    kernel: Mapping[str, Any],
    windows_logs: Mapping[str, Any],
    bios_status: str = "update_available",
) -> dict[str, Any]:
    any_critical = any(
        (d.get("health_label") == "CRITICAL") for d in (nvme_health.get("devices") or [])
    )
    any_warning = any(
        (d.get("health_label") == "WARNING") for d in (nvme_health.get("devices") or [])
    )
    logs_found = bool(windows_logs.get("panther_found") or windows_logs.get("rollback_found") or windows_logs.get("files"))
    rows = [
        {
            "hypothesis": "NVMe-Hardwarefehler",
            "evidence_for": "critical SMART/media_errors" if any_critical else "",
            "evidence_against": "HEALTHY SMART" if not any_critical and not any_warning else "",
            "rating": "supported" if any_critical else ("unlikely" if not any_warning else "plausible"),
            "next_test": "error-log + controlled retest",
        },
        {
            "hypothesis": "NVMe-Firmware",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "compare firmware vs Samsung release notes",
        },
        {
            "hypothesis": "GPT-/Partitionsfehler",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "read-only sgdisk/parted inventory",
        },
        {
            "hypothesis": "EFI-/Bootloaderfehler",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "efibootmgr -v on Gabriel",
        },
        {
            "hypothesis": "Storage-Treiber",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "Panther/setupapi.dev.log",
        },
        {
            "hypothesis": "BIOS G513QM.331",
            "evidence_for": "official newer 335 available" if bios_status == "update_available" else "",
            "evidence_against": "no changelog-proven Windows-11 abort link in this capture",
            "rating": "plausible",
            "next_test": "review ASUS changelog; optional operator BIOS update outside this ticket",
        },
        {
            "hypothesis": "Installationsmedium",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "media hash + structure check",
        },
        {
            "hypothesis": "RAM-Instabilität",
            "evidence_for": "MCE hits" if kernel.get("critical_io_or_mce") else "",
            "evidence_against": "",
            "rating": "plausible" if kernel.get("critical_io_or_mce") else "insufficient_evidence",
            "next_test": "memtest smoke",
        },
        {
            "hypothesis": "Strom/Temperatur",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "AC-only retest",
        },
        {
            "hypothesis": "Windows-Image",
            "evidence_for": "",
            "evidence_against": "",
            "rating": "insufficient_evidence",
            "next_test": "controlled retest with log collection",
        },
        {
            "hypothesis": "zweite NVMe beeinflusst Setup",
            "evidence_for": "dual internal NVMe present",
            "evidence_against": "",
            "rating": "plausible",
            "next_test": "single-target install planning after identity bind",
        },
    ]
    if logs_found:
        likely = "unknown"
        confidence = "medium"
        classes = list(windows_logs.get("error_classes") or [])
        if classes and classes != ["unknown"]:
            likely = classes[0]
            confidence = "medium"
    else:
        likely = "unknown"
        confidence = "low"
    return {
        "schema_version": SCHEMA_VERSION,
        "rows": rows,
        "likely_cause": likely,
        "confidence": confidence,
        "panther_or_rollback_present": logs_found,
        "write_allowed": False,
    }


def decide_endstatus(
    *,
    binding_ok: bool,
    identity_conflict: bool,
    nvme_health: Mapping[str, Any],
    windows_logs: Mapping[str, Any],
    capture_complete: bool,
) -> str:
    if identity_conflict:
        return "blocked_evidence_identity_conflict"
    if not binding_ok:
        return "blocked_machine_identity"
    if any(d.get("health_label") == "CRITICAL" for d in (nvme_health.get("devices") or [])):
        return "blocked_nvme_health"
    if not capture_complete:
        return "diagnosis_incomplete"
    logs_ok = bool(windows_logs.get("panther_found") or windows_logs.get("rollback_found"))
    if logs_ok:
        return "diagnosis_complete_windows_fix_pending"
    # Healthy hardware, no usable setup logs → controlled retest
    healthy = all(
        d.get("health_label") in {"HEALTHY", "WARNING"} for d in (nvme_health.get("devices") or [])
    ) and bool(nvme_health.get("devices"))
    if healthy:
        return "ready_for_controlled_windows_retest_with_log_collection"
    return "diagnosis_incomplete"



def _default_captures() -> dict[str, str]:
    return {
        "machine_identity": "pending",
        "bios": "pending",
        "nvme_identity": "pending",
        "nvme_smart": "pending",
        "nvme_error_logs": "pending",
        "kernel_storage": "pending",
        "partition_inventory": "pending",
        "windows_setup_logs": "pending",
    }


def build_run_status(
    *,
    profile_id: str,
    machine_fingerprint_hash: str,
    boot_id: str,
    run_id: str,
    payload_version: str,
    status: str = "starting",
    captures: Mapping[str, str] | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_type": RUN_TYPE,
        "profile_id": profile_id,
        "machine_fingerprint_hash": machine_fingerprint_hash,
        "boot_id": boot_id,
        "run_id": run_id,
        "payload_version": payload_version,
        "started_at": started_at or _utc_now(),
        "completed_at": None,
        "status": status,
        "terminal": status in TERMINAL_STATUSES,
        "write_operations_allowed": False,
        "bvr_run_control_required": False,
        "captures": dict(captures or _default_captures()),
        "warnings": [],
        "errors": [],
        "gui_status": "not_applicable_for_text_hardware_discovery",
        "stick_remove_hint": DO_NOT_REMOVE_HINT,
    }


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(dict(data), indent=2, ensure_ascii=False) + "\n")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_progress(
    *,
    phase_id: str,
    phase_label: str,
    status: str,
    run_id: str = "",
    detail: Mapping[str, Any] | None = None,
    progress_path: Path | None = None,
) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_type": RUN_TYPE,
        "run_id": run_id,
        "phase_id": phase_id,
        "phase_label": phase_label,
        "phase_status": status,
        "updated_at": _utc_now(),
        "phases": [{"id": i, "label": l} for i, l in CAPTURE_PHASES],
        "detail": dict(detail or {}),
        "stick_remove_hint": DO_NOT_REMOVE_HINT if phase_id != "capture_complete" else SAFE_REMOVE_HINT,
    }
    target = progress_path or PROGRESS_PATH
    try:
        _write_json(target, payload)
    except OSError:
        pass


def classify_windows_capture_status(win_logs: Mapping[str, Any]) -> str:
    mounts = list(win_logs.get("mounts") or [])
    files = list(win_logs.get("files") or [])
    blocked = any(m.get("status") == "ntfs_read_only_mount_blocked" for m in mounts)
    if files:
        return "complete" if (win_logs.get("panther_found") or win_logs.get("rollback_found")) else "partial"
    if blocked:
        return "partial"
    if not mounts and not files:
        return "not_found"
    return "not_found"


def finalize_capture_artifacts(
    *,
    out_dir: Path,
    status: dict[str, Any],
    tooling: Mapping[str, Any],
    endstatus: str,
    missing_areas: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Write manifest, sha256, capture-summary, and completion marker. Always terminalizes status."""
    run_status = str(status.get("status") or "partial")
    if run_status == "running":
        run_status = "partial"
    if run_status not in TERMINAL_STATUSES:
        run_status = "failed"
    status["status"] = run_status
    status["terminal"] = True
    status["completed_at"] = status.get("completed_at") or _utc_now()
    status["endstatus"] = endstatus
    status["stick_remove_hint"] = SAFE_REMOVE_HINT
    if missing_areas:
        status["missing_areas"] = list(missing_areas)
    _write_json(out_dir / "run-status.json", status)
    _write_json(out_dir / "run_status.json", status)

    hashes: list[str] = []
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"sha256sums.txt", "COMPLETED.TAG", "PARTIAL.TAG", "FAILED.TAG"}:
            continue
        if path.name.endswith(".partial"):
            continue
        rel = path.relative_to(out_dir).as_posix()
        hashes.append(f"{_sha256_file(path)}  {rel}")
    _atomic_write_text(out_dir / "sha256sums.txt", "\n".join(hashes) + "\n")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "run_id": status.get("run_id"),
        "boot_id": status.get("boot_id"),
        "run_type": RUN_TYPE,
        "payload_version": status.get("payload_version"),
        "endstatus": endstatus,
        "status": run_status,
        "terminal": True,
        "profile_id": status.get("profile_id"),
        "files": [h.split("  ", 1)[1] for h in hashes],
        "tooling": tooling,
        "gui_status": "not_applicable_for_text_hardware_discovery",
        "missing_areas": list(missing_areas or []),
    }
    _write_json(out_dir / "manifest.json", manifest)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "run_id": status.get("run_id"),
        "boot_id": status.get("boot_id"),
        "status": run_status,
        "terminal": True,
        "endstatus": endstatus,
        "captures": status.get("captures"),
        "missing_areas": list(missing_areas or []),
        "warnings": status.get("warnings") or [],
        "errors": status.get("errors") or [],
        "gui_status": "not_applicable_for_text_hardware_discovery",
        "stick_remove_hint": SAFE_REMOVE_HINT,
        "completed_at": status.get("completed_at"),
    }
    _write_json(out_dir / "capture-summary.json", summary)

    marker_name = "COMPLETED.TAG" if run_status == "complete" else ("PARTIAL.TAG" if run_status == "partial" else "FAILED.TAG")
    marker_body = (
        f"status={run_status}\nterminal=true\nendstatus={endstatus}\n"
        f"completed_at={status.get('completed_at')}\n"
        f"hint={SAFE_REMOVE_HINT}\n"
    )
    _atomic_write_text(out_dir / marker_name, marker_body)
    return {"manifest": manifest, "summary": summary, "marker": marker_name}


def run_hardware_discovery(
    *,
    evidence_root: Path,
    operator_confirmed_gabriel: bool = False,
    operator_phrase: str | None = None,
    run: RunFn | None = None,
    allow_non_gabriel_diag: bool = False,
    progress_path: Path | None = None,
    progress_cb: ProgressFn | None = None,
) -> dict[str, Any]:
    """Execute full read-only capture into evidence_root/physical_runs/<run_id>/."""
    run = run or _default_run
    boot_id = ""
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:
        boot_id = "unknown"
    run_id = f"hw-discovery-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    payload_ver = rescue_payload_version()
    out_dir = evidence_root / "physical_runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    protected = out_dir / "protected_raw"
    protected.mkdir(parents=True, exist_ok=True)

    def _phase(phase_id: str, phase_status: str, detail: Mapping[str, Any] | None = None) -> None:
        label = dict(CAPTURE_PHASES).get(phase_id, phase_id)
        write_progress(
            phase_id=phase_id,
            phase_label=label,
            status=phase_status,
            run_id=run_id,
            detail=detail,
            progress_path=progress_path,
        )
        if progress_cb is not None:
            progress_cb(phase_id, phase_status, detail or {})

    tooling = check_tooling(run=run)
    identity = build_machine_identity(dmi=read_dmi_fields())
    bind = bind_gabriel_operator_profile(
        identity,
        operator_confirmed=operator_confirmed_gabriel,
        exact_model_confirmed=str(identity.get("product_name") or ""),
        not_developer_host_ack=True,
        operator_phrase=operator_phrase,
    )
    bound_identity = bind.get("identity") if isinstance(bind.get("identity"), dict) else {}
    binding_ok = bool(bind.get("ok")) and bool(bound_identity.get("gabriel_bound"))
    if identity.get("is_developer_workstation") and not allow_non_gabriel_diag:
        binding_ok = False

    fp = str(
        (bound_identity or identity).get("machine_id")
        or identity.get("fingerprint_hash")
        or identity.get("machine_fingerprint_hash")
        or ""
    )
    started_at = _utc_now()
    status = build_run_status(
        profile_id=PROFILE_ASUS_ROG_GABRIEL if binding_ok else str(identity.get("expected_profile") or "unknown"),
        machine_fingerprint_hash=fp,
        boot_id=boot_id,
        run_id=run_id,
        payload_version=payload_ver,
        status="running",
        started_at=started_at,
    )
    rc_eval = evaluate_run_control(declared_run_type=RUN_TYPE, artifact=status)
    status["run_control_eval"] = rc_eval
    _write_json(out_dir / "run_status.json", status)
    _write_json(out_dir / "run-status.json", status)

    captures = dict(status["captures"])
    warnings: list[str] = []
    errors: list[str] = []
    inventory: dict[str, Any] = {"devices_redacted": [], "device_count": 0, "raw": {}}
    health: dict[str, Any] = {"devices": [], "error_logs_raw": []}
    kernel: dict[str, Any] = {}
    parts: dict[str, Any] = {}
    win_logs: dict[str, Any] = {"panther_found": False, "rollback_found": False, "files": [], "mounts": []}
    bios: dict[str, Any] = {}
    cause: dict[str, Any] = {}
    endstatus = "diagnosis_incomplete"
    fatal_exc: BaseException | None = None

    try:
        _phase("device_binding", "running")
        _write_json(
            out_dir / "machine-identity.json",
            {k: v for k, v in identity.items() if "serial" not in k.lower() or "masked" in k.lower() or "hash" in k.lower()},
        )
        _write_json(
            out_dir / "machine_identity.json",
            {k: v for k, v in identity.items() if "serial" not in k.lower() or "masked" in k.lower() or "hash" in k.lower()},
        )
        binding_doc = {
            "ok": binding_ok,
            "profile": PROFILE_ASUS_ROG_GABRIEL if binding_ok else identity.get("expected_profile"),
            "bind_result": {k: v for k, v in bind.items() if k != "machine"},
            "diagnostics_access": binding_ok or allow_non_gabriel_diag,
            "storage_write": False,
            "firmware_write": False,
            "installation": False,
        }
        _write_json(out_dir / "machine-binding.json", binding_doc)
        _write_json(out_dir / "machine_binding.json", binding_doc)
        captures["machine_identity"] = "complete" if binding_ok or allow_non_gabriel_diag else "failed"
        _phase("device_binding", "complete" if captures["machine_identity"] == "complete" else "failed")

        if not binding_ok and not allow_non_gabriel_diag:
            endstatus = "blocked_machine_identity"
            status["status"] = "failed"
            status["captures"] = captures
            status["errors"] = ["machine_binding_failed"]
            raise RuntimeError("machine_binding_failed")

        _phase("bios_inventory", "running")
        bios = {
            "installed": identity.get("bios_version"),
            "bios_date": identity.get("bios_date") if "bios_date" in identity else None,
            "official_available": "G513QM.335",
            "status": "update_available",
            "flash_performed": False,
        }
        _write_json(out_dir / "bios-inventory.json", bios)
        _write_json(out_dir / "bios_inventory.json", bios)
        captures["bios"] = "complete"
        _phase("bios_inventory", "complete")

        _phase("nvme_identity", "running")
        inventory = collect_nvme_inventory(run=run)
        _write_json(protected / "nvme_inventory_raw.json", inventory.get("raw") or {})
        _write_json(
            out_dir / "nvme_inventory_raw.json",
            {
                "note": "Full serials only in protected_raw/",
                "device_count": inventory.get("device_count"),
                "controllers_present": bool((inventory.get("raw") or {}).get("controllers")),
            },
        )
        _write_json(out_dir / "nvme-identity-redacted.json", {"devices": inventory.get("devices_redacted")})
        _write_json(out_dir / "nvme_identity_redacted.json", {"devices": inventory.get("devices_redacted")})
        captures["nvme_identity"] = "complete" if inventory.get("device_count") else "partial"
        # Missing NGUID alone is not a failure when EUI/other identity fields exist.
        for d in inventory.get("devices_redacted") or []:
            missing = set(d.get("missing_identity_fields") or [])
            if missing == {"nguid"} or (missing <= {"nguid"} and d.get("eui64")):
                warnings.append(f"nguid_absent:{d.get('nvme_identity_hash','')[:12]}")
        _phase("nvme_identity", captures["nvme_identity"])

        _phase("nvme_smart", "running")
        health = collect_nvme_health(inventory=inventory, run=run)
        _write_json(out_dir / "nvme-smart.json", {"devices": health.get("devices")})
        _write_json(out_dir / "nvme_smart.json", {"devices": health.get("devices")})
        smart_statuses = [str(d.get("capture_status") or "failed") for d in (health.get("devices") or [])]
        if smart_statuses and all(s == "complete" for s in smart_statuses):
            captures["nvme_smart"] = "complete"
        elif any(s in {"complete", "partial"} for s in smart_statuses):
            captures["nvme_smart"] = "partial"
        else:
            captures["nvme_smart"] = "failed"
            errors.append("nvme_smart_capture_failed")
        _phase("nvme_smart", captures["nvme_smart"])

        _phase("nvme_error_logs", "running")
        _write_json(out_dir / "nvme-error-logs.json", {"error_logs": health.get("error_logs_raw")})
        _write_json(out_dir / "nvme_error_logs.json", {"error_logs": health.get("error_logs_raw")})
        err_ok = bool(health.get("error_logs_raw"))
        captures["nvme_error_logs"] = "complete" if err_ok else ("partial" if health.get("devices") else "failed")
        _phase("nvme_error_logs", captures["nvme_error_logs"])

        _phase("kernel_storage", "running")
        kernel = collect_kernel_storage_findings(run=run)
        _write_json(out_dir / "kernel-storage-findings.json", kernel)
        _write_json(out_dir / "kernel_storage_findings.json", kernel)
        captures["kernel_storage"] = "complete"
        _phase("kernel_storage", "complete")

        _phase("partition_inventory", "running")
        parts = collect_partition_and_boot_inventory(run=run)
        _write_json(out_dir / "partition-inventory.json", parts)
        _write_json(out_dir / "partition_inventory.json", parts)
        _write_json(
            out_dir / "boot_inventory.json",
            {"efibootmgr": parts.get("efibootmgr"), "efibootmgr_available": parts.get("efibootmgr_available")},
        )
        captures["partition_inventory"] = "complete"
        _phase("partition_inventory", "complete")

        _phase("windows_setup_logs", "running")
        ntfs_sources = []
        for line in (parts.get("blkid_text") or "").splitlines():
            if 'TYPE="ntfs"' in line or 'TYPE="NTFS"' in line:
                dev = line.split(":", 1)[0].strip()
                if dev.startswith("/dev/nvme"):
                    ntfs_sources.append(dev)
        win_logs = collect_windows_setup_logs(
            ntfs_sources=ntfs_sources,
            work_root=Path("/run/setuphelfer/hw-discovery-mnt"),
            run=run,
        )
        win_status = classify_windows_capture_status(win_logs)
        win_logs["capture_status"] = win_status
        _write_json(out_dir / "windows-setup-evidence-inventory.json", win_logs)
        _write_json(out_dir / "windows_setup_evidence_inventory.json", win_logs)
        _write_json(
            out_dir / "windows-setup-error-summary.json",
            {
                "panther_found": win_logs.get("panther_found"),
                "rollback_found": win_logs.get("rollback_found"),
                "error_classes": win_logs.get("error_classes"),
                "file_count": len(win_logs.get("files") or []),
                "mounts": win_logs.get("mounts"),
                "capture_status": win_status,
            },
        )
        _write_json(
            out_dir / "windows_setup_error_summary.json",
            {
                "panther_found": win_logs.get("panther_found"),
                "rollback_found": win_logs.get("rollback_found"),
                "error_classes": win_logs.get("error_classes"),
                "file_count": len(win_logs.get("files") or []),
                "mounts": win_logs.get("mounts"),
                "capture_status": win_status,
            },
        )
        captures["windows_setup_logs"] = win_status
        _phase("windows_setup_logs", win_status)

        _phase("redaction", "running")
        # Published artifacts already exclude raw serials; protected_raw stays local-only on stick.
        _phase("redaction", "complete")

        cause = build_cause_matrix(
            nvme_health=health, kernel=kernel, windows_logs=win_logs, bios_status=str(bios.get("status") or "")
        )
        _write_json(out_dir / "cause_matrix.json", cause)

        devices = inventory.get("devices_redacted") or []
        role_binding = {
            "machine_profile": PROFILE_ASUS_ROG_GABRIEL,
            "windows_target": {
                "nvme_identity_hash": devices[0].get("nvme_identity_hash") if devices else "",
                "confirmed": False,
                "write_allowed": False,
            },
            "linux_target": {
                "nvme_identity_hash": devices[1].get("nvme_identity_hash") if len(devices) > 1 else "",
                "confirmed": False,
                "write_allowed": False,
            },
            "same_device": False,
            "created_at": _utc_now(),
        }
        if (
            role_binding["windows_target"]["nvme_identity_hash"]
            and role_binding["windows_target"]["nvme_identity_hash"] == role_binding["linux_target"]["nvme_identity_hash"]
        ):
            role_binding["same_device"] = True
        _write_json(out_dir / "role_binding.json", role_binding)

        required_ok = {
            "machine_identity": captures.get("machine_identity") == "complete",
            "bios": captures.get("bios") == "complete",
            "nvme_identity": captures.get("nvme_identity") == "complete",
            "nvme_smart": captures.get("nvme_smart") == "complete",
            "nvme_error_logs": captures.get("nvme_error_logs") in {"complete", "partial"},
            "kernel_storage": captures.get("kernel_storage") == "complete",
            "partition_inventory": captures.get("partition_inventory") == "complete",
            "windows_setup_logs": captures.get("windows_setup_logs") in {"complete", "partial", "not_found"},
        }
        capture_complete = all(required_ok.values()) and int(inventory.get("device_count") or 0) >= 2
        serials_ok = all(d.get("serial_hash") for d in devices)
        if not serials_ok:
            capture_complete = False
            warnings.append("serial_hash_incomplete")

        endstatus = decide_endstatus(
            binding_ok=True,
            identity_conflict=False,
            nvme_health=health,
            windows_logs=win_logs,
            capture_complete=capture_complete,
        )
        status["status"] = "complete" if capture_complete else "partial"
        status["captures"] = captures
        status["warnings"] = warnings
        status["errors"] = errors

    except BaseException as exc:  # noqa: BLE001 — finalizer must always run
        fatal_exc = exc
        exc_name = type(exc).__name__
        exc_msg = str(exc).replace("\n", " ")[:500]
        errors.append(f"capture_exception:{exc_name}:{exc_msg}")
        status["errors"] = errors
        status["warnings"] = warnings
        status["captures"] = captures
        try:
            _atomic_write_text(
                out_dir / "capture-exception.txt",
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )
        except OSError:
            pass
        if status.get("status") == "running":
            status["status"] = "partial" if any(v != "pending" for v in captures.values()) else "failed"
        if endstatus == "diagnosis_incomplete" and not binding_ok and not allow_non_gabriel_diag:
            endstatus = "blocked_machine_identity"
        elif endstatus == "diagnosis_incomplete":
            endstatus = "diagnosis_incomplete"

    missing = [k for k, v in captures.items() if v in {"pending", "failed"} or (k != "windows_setup_logs" and v == "partial" and k.startswith("nvme_smart"))]
    # Treat windows not_found as terminal-ok, not missing
    missing = [k for k in missing if not (k == "windows_setup_logs" and captures.get(k) == "not_found")]
    if captures.get("windows_setup_logs") == "partial":
        missing = list(dict.fromkeys([*missing, "windows_setup_logs"]))

    try:
        _phase("manifest_checksums", "running")
        fin = finalize_capture_artifacts(
            out_dir=out_dir,
            status=status,
            tooling=tooling,
            endstatus=endstatus,
            missing_areas=missing,
        )
        _phase("manifest_checksums", "complete")
        _phase("capture_complete", status.get("status") or "partial", {"marker": fin.get("marker")})
    except BaseException as fin_exc:  # noqa: BLE001
        errors.append(f"finalizer_exception:{type(fin_exc).__name__}")
        status["errors"] = errors
        status["status"] = "failed"
        status["terminal"] = True
        status["completed_at"] = _utc_now()
        try:
            _write_json(out_dir / "run_status.json", status)
            _write_json(out_dir / "run-status.json", status)
            _atomic_write_text(out_dir / "FAILED.TAG", f"status=failed\nterminal=true\nerror={type(fin_exc).__name__}\n")
        except OSError:
            pass
        raise

    md_lines = [
        "# PHYSICAL_DIAGNOSIS_RESULT",
        "",
        f"- Run-ID: `{run_id}`",
        f"- Boot-ID: `{boot_id}`",
        f"- Endstatus: `{endstatus}`",
        f"- Status: `{status.get('status')}` terminal={status.get('terminal')}",
        f"- Devices: {inventory.get('device_count')}",
        f"- Panther: {win_logs.get('panther_found')}",
        f"- Rollback: {win_logs.get('rollback_found')}",
        f"- Likely cause: {cause.get('likely_cause')} ({cause.get('confidence')})",
        f"- GUI: not_applicable_for_text_hardware_discovery",
        f"- Write operations: false",
        f"- {SAFE_REMOVE_HINT}",
        "",
    ]
    _atomic_write_text(out_dir / "PHYSICAL_DIAGNOSIS_RESULT.md", "\n".join(md_lines))
    result = {
        "run_id": run_id,
        "boot_id": boot_id,
        "endstatus": endstatus,
        "out_dir": str(out_dir),
        "binding_ok": binding_ok or allow_non_gabriel_diag,
        "device_count": inventory.get("device_count"),
        "captures": captures,
        "tooling": tooling,
        "run_control_eval": rc_eval,
        "status": status.get("status"),
        "terminal": True,
        "gui_status": "not_applicable_for_text_hardware_discovery",
        "stick_remove_hint": SAFE_REMOVE_HINT,
    }
    if fatal_exc is not None and not isinstance(fatal_exc, RuntimeError):
        result["exception"] = type(fatal_exc).__name__
    return result
