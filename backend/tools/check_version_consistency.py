#!/usr/bin/env python3
"""CLI: Workspace-/Runtime-Versionskonsistenz prüfen (Exit 0 = OK)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.version_consistency import (  # noqa: E402
    check_runtime_consistency,
    check_workspace_consistency,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check version source consistency.")
    parser.add_argument("--repo-root", type=Path, default=_backend.parent)
    parser.add_argument("--runtime-root", type=Path, default=None)
    parser.add_argument("--api-project-version", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.runtime_root is not None:
        report = check_runtime_consistency(
            workspace_root=args.repo_root,
            runtime_root=args.runtime_root,
            api_project_version=args.api_project_version,
        )
    else:
        report = check_workspace_consistency(args.repo_root)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        ok = bool(report.get("ok"))
        print(f"check-version-consistency: scope={report.get('scope')} ok={ok}")
        for mm in report.get("mismatches") or []:
            print(f"  mismatch: {mm}")

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
