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
from core.profile_deploy_manifest import build_profile_manifest_data, manifest_sha256  # noqa: E402


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
    parser.add_argument(
        "--profile",
        type=str,
        default="release",
        help="Install profile (release, developer, local_lab, rescue_lab, production)",
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
    profile = (args.profile or "release").strip().lower()
    try:
        data = build_manifest_data(repo)
        profile_meta = build_profile_manifest_data(profile, repo)
        data["install_profile"] = profile
        data["manifest_profile"] = profile
        data["profile_manifest"] = profile_meta
    except DeployManifestError as exc:
        print(f"deploy_manifest_error: {exc}", file=sys.stderr)
        return 1
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        out.write_text(payload, encoding="utf-8")
        data["manifest_sha256"] = manifest_sha256(out)
    except OSError as exc:
        print(f"deploy_manifest_error: write_failed:{out}:{exc}", file=sys.stderr)
        return 1
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
