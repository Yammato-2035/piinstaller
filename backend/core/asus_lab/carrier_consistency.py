"""Carrier/version consistency gate — blocks stick build on drift."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _json_version(path: Path, *keys: str) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    for key in keys:
        val = data.get(key)
        if val:
            return str(val).strip()
    return ""


def collect_workspace_carriers(repo_root: Path) -> dict[str, str]:
    root = Path(repo_root)
    return {
        "config/rescue_payload_version.json": _json_version(
            root / "config/rescue_payload_version.json", "rescue_payload_version"
        ),
        "config/version.json": _json_version(root / "config/version.json", "project_version"),
    }


def collect_squash_root_carriers(squash_root: Path) -> dict[str, str]:
    root = Path(squash_root)
    return {
        "opt/setuphelfer-rescue/VERSION": _read_text(root / "opt/setuphelfer-rescue/VERSION"),
        "opt/setuphelfer-rescue/rescue_payload_version": _read_text(
            root / "opt/setuphelfer-rescue/rescue_payload_version"
        ),
        "opt/setuphelfer-rescue/config/rescue_payload_version.json": _json_version(
            root / "opt/setuphelfer-rescue/config/rescue_payload_version.json",
            "rescue_payload_version",
        ),
        "opt/setuphelfer-rescue/config/version.json": _json_version(
            root / "opt/setuphelfer-rescue/config/version.json",
            "rescue_payload_version",
            "project_version",
        ),
    }


def collect_esp_carriers(esp_mount: Path) -> dict[str, str]:
    root = Path(esp_mount)
    return {
        "setuphelfer/rescue/rescue_payload_version": _read_text(
            root / "setuphelfer/rescue/rescue_payload_version"
        ),
        "setuphelfer/rescue/version.json": _json_version(
            root / "setuphelfer/rescue/version.json", "rescue_payload_version", "project_version"
        ),
    }


def evaluate_carrier_consistency(
    carriers: Mapping[str, str],
    *,
    expected_version: str,
) -> dict[str, Any]:
    expected = (expected_version or "").strip()
    mismatches: list[dict[str, str]] = []
    missing: list[str] = []
    for name, value in carriers.items():
        if not value:
            missing.append(name)
            continue
        if value != expected:
            mismatches.append({"carrier": name, "observed": value, "expected": expected})
    passed = not mismatches and not missing and bool(expected)
    return {
        "schema_version": SCHEMA_VERSION,
        "carrier_version_consistency": "passed" if passed else "failed",
        "expected_version": expected,
        "carriers": dict(carriers),
        "mismatches": mismatches,
        "missing": missing,
        "build_allowed": passed,
        "stick_update_allowed": passed,
        "physical_test_allowed": passed,
    }
