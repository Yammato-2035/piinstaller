#!/usr/bin/env python3
"""CLI: Packaging-Version-Projection pruefen (Tauri-Bundle-Dateinamen)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.version_projection import (  # noqa: E402
    build_version_projection_from_repo,
    check_packaging_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Tauri bundle artifact version projection.")
    parser.add_argument("--repo-root", type=Path, default=_backend.parent)
    parser.add_argument("--bundle-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat semver-only artifact names as failure (default: warn only)",
    )
    args = parser.parse_args()

    if args.bundle_root is None and args.json is False:
        proj = build_version_projection_from_repo(args.repo_root)
        print(f"check-packaging-version-gate: project={proj.project_version} semver={proj.semver_package_version}")
        for kind, name in proj.expected_artifact_names().items():
            print(f"  expected_{kind}: {name}")
        for kind, name in proj.tauri_default_artifact_names().items():
            print(f"  tauri_default_{kind}: {name}")

    report = check_packaging_artifacts(repo_root=args.repo_root, bundle_root=args.bundle_root)
    if args.strict and report.get("warnings"):
        report = dict(report)
        report["ok"] = False
        report["status"] = "blocked"
        report["errors"] = list(report.get("errors") or []) + [
            "strict:semver_projection_artifact_names"
        ]

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for w in report.get("warnings") or []:
            print(f"  warn: {w}")
        for e in report.get("errors") or []:
            print(f"  error: {e}")
        print(f"check-packaging-version-gate: status={report.get('status')} ok={report.get('ok')}")

    if not report.get("ok"):
        return 19
    if report.get("warnings"):
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
