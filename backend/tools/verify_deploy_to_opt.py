#!/usr/bin/env python3
"""
CLI: Post-Deploy-Verifikation fuer deploy-to-opt (Dateien + OpenAPI).

Exit 0 = OK, 1 = mindestens eine Pruefung fehlgeschlagen.
Keine Secrets in der Ausgabe.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.deploy_runtime_verify import run_verify  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify deploy-to-opt runtime sync and OpenAPI routes.")
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace/repo root (Quelle)")
    parser.add_argument("--runtime", type=Path, default=Path("/opt/setuphelfer"), help="Runtime root")
    parser.add_argument(
        "--phase",
        choices=("post-rsync", "post-restart", "all"),
        default="all",
        help="post-rsync: Dateien+app.py; post-restart: openapi.json; all: beides",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL (post-restart)")
    parser.add_argument("--json", action="store_true", help="Vollstaendigen Report als JSON auf stdout")
    args = parser.parse_args()

    ok, report = run_verify(
        workspace_root=args.workspace,
        runtime_root=args.runtime,
        phase=args.phase,
        base_url=args.base_url,
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        phase = report.get("phase", args.phase)
        print(f"verify-deploy-to-opt: phase={phase} ok={ok}")
        if phase in ("post_rsync", "all") or "post_rsync" in report:
            block = report if phase == "post_rsync" else report.get("post_rsync", {})
            files = block.get("files") or {}
            if files.get("missing_runtime"):
                print("  missing_runtime:", ", ".join(files["missing_runtime"]))
            if files.get("sha256_mismatch"):
                print("  sha256_mismatch:", ", ".join(files["sha256_mismatch"]))
            routes = block.get("app_routes") or {}
            if routes.get("missing_markers"):
                print("  app_route_markers_missing:", ", ".join(routes["missing_markers"]))
        if phase in ("post_restart", "all") or "post_restart" in report:
            block = report if phase == "post_restart" else report.get("post_restart", {})
            openapi = block.get("openapi") or {}
            if openapi.get("missing_paths"):
                print("  openapi_missing_paths:", ", ".join(openapi["missing_paths"]))
            if openapi.get("error"):
                print("  openapi_error:", openapi["error"])
            version = block.get("version_consistency") or {}
            if version.get("mismatches"):
                print("  version_mismatches:", ", ".join(version["mismatches"]))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
