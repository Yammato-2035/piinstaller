"""PI-RS-TEL-003 cross-repo harness — local diagnostics subprocess only."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.error import URLError
from urllib.request import urlopen

from core.rescue_lab_telemetry_cross_repo_preview import (
    CSE_TARGET_COMPATIBILITY,
    DIAGNOSTICS_CONTRACT_REFERENCE,
    assert_diagnostics_base_url_allowed,
    build_diagnostics_cloudserver_payload_from_rescue,
    build_rescue_cross_repo_telemetry_payload,
    post_diagnostics_json,
    verify_diagnostics_findings_preview,
    verify_diagnostics_validate_preview,
)


def locate_monorepo_root() -> Path | None:
    candidates = [
        Path("/home/volker/setuphelfer-private"),
        Path(__file__).resolve().parents[3].parent / "setuphelfer-private",
    ]
    for candidate in candidates:
        if (candidate / "diagnostics-server" / "app" / "main.py").is_file():
            return candidate
    return None


def locate_cse_root() -> Path | None:
    candidate = Path("/home/volker/setuphelfer-cloudserver-edition")
    if (candidate / "setuphelfer_cse").is_dir():
        return candidate
    return None


def read_cross_repo_reference_pins() -> dict[str, str]:
    monorepo = locate_monorepo_root()
    diag_head = "unknown"
    if monorepo is not None:
        import subprocess as sp

        try:
            diag_head = sp.check_output(
                ["git", "-C", str(monorepo), "rev-parse", "HEAD"],
                text=True,
            ).strip()
        except (sp.CalledProcessError, FileNotFoundError):
            pass
    return {
        "monorepo_root": str(monorepo) if monorepo else "",
        "diagnostics_head": diag_head,
        "diagnostics_contract_reference": DIAGNOSTICS_CONTRACT_REFERENCE,
        "cse_target_compatibility": CSE_TARGET_COMPATIBILITY,
        "cse_root": str(locate_cse_root() or ""),
    }


def diagnostics_repo_available() -> bool:
    monorepo = locate_monorepo_root()
    if monorepo is None:
        return False
    python_bin = monorepo / "diagnostics-server" / ".venv" / "bin" / "python"
    return python_bin.is_file()


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def local_diagnostics_server() -> Iterator[str]:
    monorepo = locate_monorepo_root()
    if monorepo is None:
        raise RuntimeError("monorepo_missing")
    diagnostics_path = monorepo / "diagnostics-server"
    python_bin = diagnostics_path / ".venv" / "bin" / "python"
    if not python_bin.is_file():
        raise RuntimeError("diagnostics_venv_missing")

    port = _pick_free_port()
    env = dict(os.environ)
    env["DS_REQUIRE_DATABASE"] = "false"
    env["SETUPHELFER_DIAGNOSTICS_LAB_RECEIVER_ENABLED"] = "false"
    process = subprocess.Popen(
        [
            str(python_bin),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(diagnostics_path),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 30.0
        while time.time() < deadline:
            if process.poll() is not None:
                raise RuntimeError("diagnostics_server_exited_early")
            try:
                with urlopen(f"{base_url}/health", timeout=2.0) as response:
                    if response.status == 200:
                        break
            except URLError:
                time.sleep(0.3)
        else:
            raise RuntimeError("diagnostics_server_start_timeout")
        yield base_url
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            process.terminate()
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                process.kill()
            process.wait(timeout=5.0)


def run_cross_repo_preview_verification(
    *,
    rescue_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full PI-RS-TEL-003 verification against local diagnostics server."""
    rescue = rescue_payload or build_rescue_cross_repo_telemetry_payload()
    cloudserver_payload = build_diagnostics_cloudserver_payload_from_rescue(rescue)

    with local_diagnostics_server() as base_url:
        validate_result = verify_diagnostics_validate_preview(
            base_url=base_url,
            cloudserver_payload=cloudserver_payload,
        )
        findings_result = verify_diagnostics_findings_preview(
            base_url=base_url,
            cloudserver_payload=cloudserver_payload,
        )

    return {
        "preview_only": True,
        "production_ready": False,
        "external_calls": True,
        "diagnostics_host": "127.0.0.1",
        "validate_accepted": validate_result.get("accepted_for_diagnostics"),
        "validate_status": validate_result.get("validation_status"),
        "finding_rules_preview_present": "finding_rules_preview" in validate_result,
        "findings_count": findings_result.get("finding_count", 0),
        "findings_preview_only": findings_result.get("preview_only"),
        "finding_ids": [
            item.get("finding_id")
            for item in findings_result.get("findings", [])
            if isinstance(item, dict)
        ],
        "reference_pins": read_cross_repo_reference_pins(),
    }


def assert_no_authorization_header_used(base_url: str, payload: dict[str, Any]) -> None:
    """Ensure post_diagnostics_json does not attach Authorization."""
    import inspect

    source = inspect.getsource(post_diagnostics_json)
    assert "Authorization" not in source
    assert_diagnostics_base_url_allowed(base_url)
    serialized = json.dumps(payload)
    assert "Bearer" not in serialized
