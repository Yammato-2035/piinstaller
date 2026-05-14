#!/usr/bin/env python3
"""
Erzeugt build/deploy/setuphelfer-deploy-manifest.json aus der kanonischen Whitelist (SHA256, kein sudo).

Liest nur Workspace-Dateien; kein Zugriff auf /opt erforderlich.
Exit 1 bei fehlender Pflichtdatei oder DeployManifestError.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.deploy_manifest import (  # noqa: E402
    DeployManifestError,
    MANIFEST_BASENAME,
    build_manifest_data,
    workspace_manifest_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate setuphelfer deploy manifest (read-only file hashes, no /opt access)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of backend/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output JSON (default: <repo>/build/deploy/{MANIFEST_BASENAME})",
    )
    args = parser.parse_args()
    repo = args.repo_root
    if repo is None:
        repo = _backend.parent
    try:
        repo = repo.expanduser().resolve()
    except OSError as exc:
        print(f"deploy_manifest_error: invalid_repo_root:{exc}", file=sys.stderr)
        return 1
    out = args.output
    if out is None:
        out = workspace_manifest_path(repo)
    try:
        data = build_manifest_data(repo)
    except DeployManifestError as exc:
        print(f"deploy_manifest_error: {exc}", file=sys.stderr)
        return 1
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"deploy_manifest_error: write_failed:{out}:{exc}", file=sys.stderr)
        return 1
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
