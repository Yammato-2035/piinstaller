#!/usr/bin/env python3
"""
Read-only Auswertung fuer check-runtime-deploy-gate.sh.
Exit-Codes (Shell-Konvention):
  0 OK
 11 API-Version nicht lesbar / HTTP-Body ungueltig
 12 Workspace vs. API project_version mismatch
 13 backend_runtime_path unplausibel fuer opt/release
 14 deploy_drift: Backend-Dateien deployen noetig
 15 deploy_drift: manueller Backend-Restart empfohlen
 16 Deploy-Manifest-Mismatch
 20 Unklar / deploy_drift gray ohne Freigabe / Dashboard fehlt
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

EXPECTED_OPT_BACKEND = "/opt/setuphelfer/backend"


def _read_json_file(path: Path) -> Any | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            return None
        return json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None


def evaluate_version_payload(api: dict[str, Any], workspace_version_file: Path) -> int:
    api_pv = str(api.get("project_version") or api.get("version") or "").strip()
    if not api_pv:
        return 11
    ws = _read_json_file(workspace_version_file)
    if not isinstance(ws, dict):
        return 11
    ws_pv = str(ws.get("project_version") or "").strip()
    if not ws_pv:
        return 11
    if api_pv != ws_pv:
        return 12
    brp = str(api.get("backend_runtime_path") or "").strip().rstrip("/")
    install_profile = str(api.get("install_profile") or "").strip().lower()
    app_edition = str(api.get("app_edition") or "").strip().lower()
    if install_profile == "opt" or app_edition == "release":
        if brp != EXPECTED_OPT_BACKEND.rstrip("/"):
            return 13
    return 0


def evaluate_deploy_drift(dashboard_body: dict[str, Any] | None, *, allow_gray: bool) -> int:
    if not isinstance(dashboard_body, dict):
        return 20
    dd = dashboard_body.get("deploy_drift")
    if not isinstance(dd, dict):
        return 20
    mm = dd.get("manifest_match")
    profile_aware = dd.get("profile_aware") is True
    profile_mm = dd.get("profile_manifest_match")
    if profile_aware and profile_mm is True:
        pass
    elif mm is False:
        return 16
    status = str(dd.get("status") or "").lower()
    sug = dd.get("suggested_actions")
    if not isinstance(sug, list):
        sug = []
    sug_set = {str(x).strip() for x in sug if str(x).strip()}
    if status == "yellow":
        if "deploy_backend_files" in sug_set:
            return 14
        if "restart_backend_manual" in sug_set:
            return 15
    if status == "gray":
        if allow_gray or os.environ.get("RUNTIME_GATE_ALLOW_DEPLOY_DRIFT_GRAY") == "1":
            return 0
        return 20
    if status == "green":
        return 0
    # yellow ohne deploy/restart: keine harte Backend-Blockade laut Gate-Regelwerk
    if status == "yellow":
        return 0
    return 20


def main() -> int:
    p = argparse.ArgumentParser(description="Runtime deploy gate evaluator (read-only)")
    p.add_argument("--api-version-file", type=Path, required=True)
    p.add_argument("--workspace-version-file", type=Path, required=True)
    p.add_argument("--dev-dashboard-file", type=Path, default=None)
    p.add_argument("--skip-deploy-drift", action="store_true")
    p.add_argument("--allow-gray", action="store_true")
    args = p.parse_args()

    api_raw = _read_json_file(args.api_version_file)
    if not isinstance(api_raw, dict):
        print("runtime_deploy_gate_eval: API-Version-JSON ungueltig oder leer", file=sys.stderr)
        return 11
    if str(api_raw.get("status") or "") != "success":
        # HTTP war 200, aber Payload nicht success — konservativ wie Gate-Skript
        if "project_version" not in api_raw and "version" not in api_raw:
            print("runtime_deploy_gate_eval: API-Payload ohne project_version", file=sys.stderr)
            return 11

    v = evaluate_version_payload(api_raw, args.workspace_version_file)
    if v != 0:
        return v

    if args.skip_deploy_drift or os.environ.get("RUNTIME_GATE_SKIP_DEPLOY_DRIFT") == "1":
        return 0

    if args.dev_dashboard_file is None or not args.dev_dashboard_file.is_file():
        print(
            "runtime_deploy_gate_eval: dev-dashboard JSON fehlt — "
            "RUNTIME_GATE_SKIP_DEPLOY_DRIFT=1 nur mit dokumentierter Begruendung",
            file=sys.stderr,
        )
        return 20

    dd_raw = _read_json_file(args.dev_dashboard_file)
    if not isinstance(dd_raw, dict) or dd_raw.get("status") != "success":
        print("runtime_deploy_gate_eval: dev-dashboard Antwort ungueltig", file=sys.stderr)
        return 20
    body = dd_raw.get("dashboard")
    if not isinstance(body, dict):
        print("runtime_deploy_gate_eval: dashboard-Objekt fehlt", file=sys.stderr)
        return 20

    return evaluate_deploy_drift(body, allow_gray=args.allow_gray)


if __name__ == "__main__":
    raise SystemExit(main())
