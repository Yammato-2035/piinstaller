#!/usr/bin/env python3
"""Profile-aware runtime deploy gate evaluator (read-only, independent of dev-dashboard)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

VALID_PROFILES = frozenset({"release", "developer", "local_lab", "rescue_lab", "production"})

FORBIDDEN_PREFIXES = (
    "/api/fleet",
    "/api/dev-diagnostics",
    "/api/rescue-remote",
    "/api/dev-dashboard",
    "/api/dev-server",
)

PROBE_BY_PREFIX: dict[str, str] = {
    "/api/fleet": "/api/fleet/sessions",
    "/api/dev-diagnostics": "/api/dev-diagnostics/latest",
    "/api/rescue-remote": "/api/rescue-remote/jobs",
    "/api/dev-dashboard": "/api/dev-dashboard/status",
    "/api/dev-server": "/api/dev-server/health",
}

REQUIRED_LOCAL_LAB = (
    "/api/fleet",
    "/api/dev-diagnostics",
    "/api/dev-dashboard",
)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _normalize_profile(raw: str) -> tuple[str | None, str | None]:
    """Return (profile, legacy_note)."""
    p = (raw or "").strip().lower()
    if not p:
        return None, None
    if p == "opt":
        return "release", "legacy_profile_opt_mapped_to_release"
    if p in VALID_PROFILES:
        return p, None
    return None, f"invalid_install_profile:{p}"


def _http_status(base_url: str, path: str, *, timeout: float = 5.0) -> int | None:
    url = base_url.rstrip("/") + path
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _prefix_http_accessible(base_url: str, prefix: str) -> bool:
    probe = PROBE_BY_PREFIX.get(prefix, prefix)
    code = _http_status(base_url, probe)
    if code is None:
        return False
    return 200 <= code < 300


def _openapi_paths(openapi: dict[str, Any]) -> list[str]:
    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        return []
    return sorted(paths.keys())


def _openapi_has_prefix(paths: list[str], prefix: str) -> bool:
    return any(p == prefix or p.startswith(prefix + "/") for p in paths)


def main() -> int:
    p = argparse.ArgumentParser(description="Profile deploy gate evaluator")
    p.add_argument("--api-version-file", type=Path, required=True)
    p.add_argument("--openapi-file", type=Path, default=None)
    p.add_argument("--base-url", type=str, default=None)
    p.add_argument("--bind-address", type=str, default="127.0.0.1")
    p.add_argument(
        "--http-probe",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Probe HTTP for route visibility (default: on when --base-url set)",
    )
    p.add_argument("--workspace-version-file", type=Path, default=None)
    args = p.parse_args()

    api = _read_json(args.api_version_file)
    if not api:
        print("profile_gate: version_endpoint_failed", file=sys.stderr)
        return 24

    raw_profile = str(api.get("install_profile") or "")
    profile, legacy_note = _normalize_profile(raw_profile)
    if not profile:
        print(f"profile_gate: install_profile_missing_or_invalid:{raw_profile!r}", file=sys.stderr)
        return 17

    manifest_profile_raw = str(api.get("manifest_profile") or profile).strip().lower()
    manifest_profile, _ = _normalize_profile(manifest_profile_raw)
    if not manifest_profile:
        manifest_profile = profile
    if manifest_profile != profile:
        print(
            f"profile_gate: profile_manifest_mismatch:{manifest_profile}!={profile}",
            file=sys.stderr,
        )
        return 18

    if args.workspace_version_file and args.workspace_version_file.is_file():
        ws = _read_json(args.workspace_version_file)
        if ws:
            ws_pv = str(ws.get("project_version") or "").strip()
            api_pv = str(api.get("project_version") or api.get("version") or "").strip()
            if ws_pv and api_pv and ws_pv != api_pv:
                print(f"profile_gate: project_version_mismatch:{api_pv}!={ws_pv}", file=sys.stderr)
                return 12

    brp = str(api.get("backend_runtime_path") or "").strip().rstrip("/")
    if (
        profile in ("release", "production")
        and brp
        and brp != "/opt/setuphelfer/backend"
    ):
        print(f"profile_gate: backend_runtime_path_unexpected:{brp}", file=sys.stderr)
        return 13

    gate_status = str(api.get("profile_gate_status") or "").lower()
    gate_errors = list(api.get("profile_gate_errors") or [])
    if legacy_note:
        gate_errors = gate_errors + [legacy_note] if legacy_note.startswith("invalid") else gate_errors

    base_url = (args.base_url or "").strip() or None
    http_probe = args.http_probe if args.http_probe is not None else bool(base_url)

    paths: list[str] = []
    if args.openapi_file and args.openapi_file.is_file():
        oa = _read_json(args.openapi_file)
        if oa:
            paths = _openapi_paths(oa)
        elif http_probe and base_url:
            print("profile_gate: openapi_failed", file=sys.stderr)
            return 25

    def _cap_enabled(prefix: str) -> bool:
        if prefix.startswith("/api/fleet"):
            return bool(api.get("fleet_sessions_enabled"))
        if prefix.startswith("/api/dev-diagnostics"):
            return bool(api.get("dev_diagnostics_enabled"))
        if prefix.startswith("/api/rescue-remote"):
            return bool(api.get("rescue_remote_enabled"))
        if prefix.startswith("/api/dev-dashboard"):
            return bool(api.get("dev_control_enabled"))
        if prefix.startswith("/api/dev-server"):
            return bool(api.get("dev_server_enabled"))
        return False

    def forbidden_visible(prefix: str) -> bool:
        if http_probe and base_url:
            return _prefix_http_accessible(base_url, prefix)
        if profile in ("release", "production") and not _cap_enabled(prefix):
            return False
        return _openapi_has_prefix(paths, prefix)

    def required_visible(prefix: str) -> bool:
        if http_probe and base_url:
            return _prefix_http_accessible(base_url, prefix)
        if profile == "local_lab" and _cap_enabled(prefix):
            return _openapi_has_prefix(paths, prefix)
        return _openapi_has_prefix(paths, prefix)

    if profile in ("release", "production"):
        for prefix in FORBIDDEN_PREFIXES:
            if forbidden_visible(prefix):
                print(f"profile_gate: forbidden_api_path_visible:{prefix}", file=sys.stderr)
                return 19
        if http_probe and base_url:
            dd_code = _http_status(base_url, "/api/dev-dashboard/status")
            if dd_code is not None and dd_code != 404 and not (200 <= dd_code < 300):
                print(f"profile_gate: dev_dashboard_unexpected_http:{dd_code}", file=sys.stderr)
                return 19
    elif profile == "local_lab":
        for prefix in REQUIRED_LOCAL_LAB:
            if not required_visible(prefix):
                print(f"profile_gate: required_api_path_missing:{prefix}", file=sys.stderr)
                return 20

    if gate_status == "red" or (gate_errors and not legacy_note):
        print(f"profile_gate: profile_gate_red:{gate_errors}", file=sys.stderr)
        return 19

    if not api.get("public_exposure_allowed", False):
        bind = (args.bind_address or "").strip()
        if bind in ("0.0.0.0", "::", "[::]"):
            if not os.environ.get("SETUPHELFER_OPERATOR_CONFIRM_PUBLIC_BIND"):
                print("profile_gate: public_exposure_blocked", file=sys.stderr)
                return 21

    fe = str(api.get("frontend_build_profile") or "").strip().lower()
    if fe:
        fe_norm, _ = _normalize_profile(fe)
        if fe_norm and fe_norm != profile:
            rel = frozenset({"release", "production"})
            lab = frozenset({"developer", "local_lab", "rescue_lab"})
            if profile in rel and fe_norm in lab:
                print(
                    f"profile_gate: frontend_profile_mismatch:backend={profile},frontend={fe_norm}",
                    file=sys.stderr,
                )
                return 22
            if profile in lab and fe_norm in rel:
                print(
                    f"profile_gate: frontend_profile_mismatch:backend={profile},frontend={fe_norm}",
                    file=sys.stderr,
                )
                return 22

    if gate_status == "yellow":
        print("profile_gate: yellow_warnings", file=sys.stderr)

    print("profile_gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
