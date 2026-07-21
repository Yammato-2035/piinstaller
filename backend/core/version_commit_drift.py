"""Version / commit / payload drift evaluation (PI-RS-BVR-GUI-DCC-001)."""

from __future__ import annotations

from typing import Any


def _norm(value: Any) -> str:
    return str(value or "").strip()


def classify_identity_pair(
    *,
    left: str,
    right: str,
    documented_ok: bool = False,
) -> str:
    """Return green|yellow|red|gray for a compared identity pair."""
    a = _norm(left)
    b = _norm(right)
    if not a or not b or a.lower() in {"unknown", "n/a"} or b.lower() in {"unknown", "n/a"}:
        return "gray"
    if a == b:
        return "green"
    if documented_ok:
        return "yellow"
    return "red"


def build_version_drift_matrix(
    *,
    workspace_version: str,
    workspace_commit: str,
    runtime_version: str,
    runtime_commit: str,
    api_version: str,
    frontend_version: str,
    payload_version: str,
    payload_commit: str,
    payload_sha256: str,
    usb_payload_version: str,
    usb_payload_sha256: str,
    origin_main_commit: str = "",
    feature_commit: str = "",
) -> dict[str, Any]:
    rows = [
        {
            "component": "workspace",
            "version": workspace_version,
            "commit": workspace_commit,
            "build_id": "",
            "sha256": "",
            "expected": feature_commit or workspace_commit,
            "status": "green" if workspace_commit else "gray",
        },
        {
            "component": "runtime_opt",
            "version": runtime_version,
            "commit": runtime_commit,
            "build_id": "",
            "sha256": "",
            "expected": feature_commit or workspace_commit,
            "status": classify_identity_pair(
                left=runtime_commit,
                right=feature_commit or workspace_commit,
            ),
        },
        {
            "component": "backend_api",
            "version": api_version,
            "commit": "",
            "build_id": "",
            "sha256": "",
            "expected": workspace_version,
            "status": classify_identity_pair(left=api_version, right=workspace_version),
        },
        {
            "component": "frontend",
            "version": frontend_version,
            "commit": "",
            "build_id": "",
            "sha256": "",
            "expected": workspace_version,
            "status": classify_identity_pair(left=frontend_version, right=workspace_version),
        },
        {
            "component": "payload",
            "version": payload_version,
            "commit": payload_commit,
            "build_id": "",
            "sha256": payload_sha256,
            "expected": payload_version,
            "status": "green" if payload_version else "gray",
        },
        {
            "component": "usb_stick",
            "version": usb_payload_version,
            "commit": "",
            "build_id": "",
            "sha256": usb_payload_sha256,
            "expected": payload_version,
            "status": classify_identity_pair(
                left=usb_payload_version or usb_payload_sha256,
                right=payload_version or payload_sha256,
            )
            if (usb_payload_version or usb_payload_sha256)
            else "gray",
        },
    ]

    # Documented origin/main lag vs feature branch is yellow, not automatic red.
    origin_status = "gray"
    if origin_main_commit and workspace_commit:
        if origin_main_commit == workspace_commit:
            origin_status = "green"
        else:
            origin_status = "yellow"

    statuses = [str(r["status"]) for r in rows]
    if "red" in statuses:
        overall = "red"
    elif "gray" in statuses:
        overall = "gray"
    elif "yellow" in statuses or origin_status == "yellow":
        overall = "yellow"
    else:
        overall = "green"

    drifts: list[str] = []
    if classify_identity_pair(left=runtime_commit, right=feature_commit or workspace_commit) == "red":
        drifts.append("workspace_runtime_commit_drift")
    if classify_identity_pair(left=runtime_version, right=workspace_version) == "red":
        drifts.append("workspace_runtime_version_drift")
    if classify_identity_pair(left=api_version, right=workspace_version) == "red":
        drifts.append("backend_frontend_version_drift")  # API vs workspace
    if classify_identity_pair(left=frontend_version, right=workspace_version) == "red":
        drifts.append("backend_frontend_version_drift")
    if usb_payload_version and payload_version and usb_payload_version != payload_version:
        drifts.append("payload_usb_version_drift")
    if usb_payload_sha256 and payload_sha256 and usb_payload_sha256 != payload_sha256:
        drifts.append("payload_usb_sha256_drift")
    if not runtime_commit:
        drifts.append("unknown_runtime_identity")

    return {
        "schema": "setuphelfer.version-commit-drift-matrix.v1",
        "overall_status": overall,
        "origin_main_status": origin_status,
        "drifts": drifts,
        "rows": rows,
    }
