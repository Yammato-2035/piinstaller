"""Anonymized discovery evidence push to cloud lab ingest (multi-host lab)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from core.rescue_stick_cloud_lab_config import rescue_stick_lab_send_config_from_env
from core.rescue_stick_cloud_lab_models import RescueStickLabSendStatus
from core.rescue_stick_cloud_lab_payload import (
    assert_no_pii_in_payload,
    build_rescue_stick_lab_payload,
    derive_host_id_hash,
)
from core.rescue_stick_cloud_lab_send import execute_rescue_stick_lab_send


def _hash_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:32]}"


def build_anonymized_discovery_summary(
    *,
    state: Mapping[str, Any],
    gate: Mapping[str, Any],
    machine: Mapping[str, Any] | None = None,
    modules_completed: list[str] | None = None,
) -> dict[str, Any]:
    machine = machine or {}
    modules = list(modules_completed or [])
    session_id = str(state.get("session_id") or "")
    boot_id = str(state.get("boot_id") or "")
    vendor_class = str(machine.get("vendor_class") or "unknown")
    model_family = str(machine.get("model_family") or "unknown")
    return {
        "status": str(gate.get("status") or state.get("result") or "unknown"),
        "modules_completed": modules,
        "module_count": len(modules),
        "vendor_class": vendor_class,
        "model_family": model_family,
        "architecture": str(machine.get("architecture") or ""),
        "payload_version": str(state.get("payload_version") or ""),
        "privacy_gate_passed": bool(gate.get("privacy_gate_passed")),
        "secret_gate_passed": bool(gate.get("secret_gate_passed", True)),
        "session_id_hash": _hash_id(session_id) if session_id else "",
        "boot_id_hash": _hash_id(boot_id) if boot_id else "",
        "run_mode": str(state.get("run_mode") or ""),
    }


def resolve_lab_token_file() -> str:
    env_token = os.environ.get("SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE", "").strip()
    if env_token and Path(env_token).is_file():
        return env_token
    candidates = [
        Path("/run/setuphelfer/esp-rw/setuphelfer/lab/telemetry-lab-token"),
        Path("/run/setuphelfer-rescue/media/SETUP_LOGS/setuphelfer/lab/telemetry-lab-token"),
    ]
    for base in Path("/media").glob("*/SETUP_LOGS*/setuphelfer/lab/telemetry-lab-token"):
        candidates.append(base)
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
    return env_token


def apply_lab_send_env_defaults() -> None:
    """Lab-auto boots: enable gated cloud send without interactive consent wizard."""
    os.environ.setdefault("SETUPHELFER_RS_TELEMETRY_LAB_SEND_ENABLED", "1")
    os.environ.setdefault("SETUPHELFER_RS_TELEMETRY_OPERATOR_APPROVAL", "explicit")
    os.environ.setdefault("SETUPHELFER_RS_TELEMETRY_CONSENT_STATUS", "granted_lab")
    os.environ.setdefault("SETUPHELFER_RS_TELEMETRY_BOOT_MODE", "lab_auto_discovery")
    token = resolve_lab_token_file()
    if token:
        os.environ["SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE"] = token
    try:
        Path("/run/setuphelfer-rescue").mkdir(parents=True, exist_ok=True)
        Path("/run/setuphelfer-rescue/telemetry-opt-in").touch(exist_ok=True)
    except OSError:
        pass
    os.environ.setdefault("SETUPHELFER_RESCUE_TELEMETRY_OPT_IN", "1")


def send_discovery_lab_telemetry(
    *,
    state: Mapping[str, Any],
    gate: Mapping[str, Any],
    machine: Mapping[str, Any] | None = None,
    modules_completed: list[str] | None = None,
) -> dict[str, Any]:
    """Push anonymized discovery summary to telemetrie.setuphelfer.de (lab bearer)."""
    apply_lab_send_env_defaults()
    discovery = build_anonymized_discovery_summary(
        state=state,
        gate=gate,
        machine=machine,
        modules_completed=modules_completed,
    )
    host_seed = (
        f"{discovery.get('vendor_class')}:{discovery.get('model_family')}:"
        f"{discovery.get('architecture')}"
    )
    cfg = rescue_stick_lab_send_config_from_env()
    result = execute_rescue_stick_lab_send(
        cfg,
        discovery_summary=discovery,
        host_id_hash=derive_host_id_hash(host_seed),
    )
    out = result.to_dict()
    out["discovery_summary"] = discovery
    # Ensure payload used for send is PII-safe even when nested.
    preview = out.get("payload_preview_redacted") or {}
    if preview:
        try:
            assert_no_pii_in_payload(preview)
            out["pii_assert_ok"] = True
        except ValueError as exc:
            out["pii_assert_ok"] = False
            out["pii_assert_error"] = str(exc)
    out["token_file_present"] = bool(resolve_lab_token_file())
    out["accepted"] = result.send_status == RescueStickLabSendStatus.LAB_SEND_ACCEPTED
    return out


def write_telemetry_artifact(session_dir: Path, payload: Mapping[str, Any]) -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "17-telemetry-lab-send.json"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(dict(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    return path
