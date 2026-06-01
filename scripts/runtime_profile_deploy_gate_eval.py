#!/usr/bin/env python3
"""Profile-aware runtime deploy gate evaluator (read-only)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

FORBIDDEN_PREFIXES = (
    "/api/fleet",
    "/api/dev-diagnostics",
    "/api/rescue-remote",
    "/api/dev-dashboard",
    "/api/dev-server",
)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _openapi_paths(openapi: dict[str, Any]) -> list[str]:
    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        return []
    return sorted(paths.keys())


def main() -> int:
    p = argparse.ArgumentParser(description="Profile deploy gate evaluator")
    p.add_argument("--api-version-file", type=Path, required=True)
    p.add_argument("--openapi-file", type=Path, default=None)
    p.add_argument("--bind-address", type=str, default="127.0.0.1")
    args = p.parse_args()

    api = _read_json(args.api_version_file)
    if not api:
        print("profile_gate: api version missing", file=sys.stderr)
        return 17

    profile = str(api.get("install_profile") or "").strip().lower()
    manifest_profile = str(api.get("manifest_profile") or profile).strip().lower()
    if not profile:
        print("profile_gate: install_profile_missing", file=sys.stderr)
        return 17
    if manifest_profile and manifest_profile != profile:
        print(f"profile_gate: manifest_profile_mismatch:{manifest_profile}!={profile}", file=sys.stderr)
        return 18

    gate_status = str(api.get("profile_gate_status") or "").lower()
    gate_errors = api.get("profile_gate_errors") or []
    if gate_status == "red" or gate_errors:
        print(f"profile_gate: profile_gate_red:{gate_errors}", file=sys.stderr)
        return 19

    paths: list[str] = []
    if args.openapi_file and args.openapi_file.is_file():
        oa = _read_json(args.openapi_file)
        if oa:
            paths = _openapi_paths(oa)

    if profile in ("release", "production"):
        for prefix in FORBIDDEN_PREFIXES:
            for path in paths:
                if path == prefix or path.startswith(prefix + "/"):
                    print(f"profile_gate: forbidden_api_path_visible:{path}", file=sys.stderr)
                    return 19

    if profile == "local_lab":
        for prefix in ("/api/fleet", "/api/dev-diagnostics", "/api/dev-dashboard"):
            if not any(path == prefix or path.startswith(prefix + "/") for path in paths):
                print(f"profile_gate: required_api_path_missing:{prefix}", file=sys.stderr)
                return 20

    if not api.get("public_exposure_allowed", False):
        bind = (args.bind_address or "").strip()
        if bind in ("0.0.0.0", "::", "[::]"):
            if not os.environ.get("SETUPHELFER_OPERATOR_CONFIRM_PUBLIC_BIND"):
                print("profile_gate: public_exposure_blocked", file=sys.stderr)
                return 21

    fe = str(api.get("frontend_build_profile") or "").strip().lower()
    if fe and fe != profile:
        rel = frozenset({"release", "production"})
        lab = frozenset({"developer", "local_lab", "rescue_lab"})
        if profile in rel and fe in lab:
            print(f"profile_gate: frontend_profile_mismatch:backend={profile},frontend={fe}", file=sys.stderr)
            return 22
        if profile in lab and fe in rel:
            print(f"profile_gate: frontend_profile_mismatch:backend={profile},frontend={fe}", file=sys.stderr)
            return 22

    if gate_status == "yellow":
        print("profile_gate: yellow_warnings", file=sys.stderr)
        return 0

    print("profile_gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
