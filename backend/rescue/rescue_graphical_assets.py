"""Graphical rescue boot menu assets — manifest and validation (no writes to USB)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

FORBIDDEN_BRAND_PHRASES: tuple[str, ...] = (
    "rescue stick",
    "rettungsstick",
)

ASSET_MANIFEST_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RescueAssetSpec:
    source_rel: str
    target_rel: str
    purpose: str
    locale: str | None = None
    required: bool = True


CANONICAL_ASSET_SPECS: tuple[RescueAssetSpec, ...] = (
    RescueAssetSpec("logo/setuphelfer-logo2.png", "usr/share/setuphelfer/rescue/assets/logo/setuphelfer-logo2.png", "logo"),
    RescueAssetSpec(
        "boot-menu/setuphelfer-boot-menu-de.png",
        "usr/share/setuphelfer/rescue/assets/boot-menu/setuphelfer-boot-menu-de.png",
        "boot_menu_background",
        locale="de",
    ),
    RescueAssetSpec(
        "boot-menu/setuphelfer-boot-menu-en.png",
        "usr/share/setuphelfer/rescue/assets/boot-menu/setuphelfer-boot-menu-en.png",
        "boot_menu_background",
        locale="en",
    ),
    RescueAssetSpec("splash/setuphelfer-splash.png", "usr/share/setuphelfer/rescue/assets/splash/setuphelfer-splash.png", "splash"),
    RescueAssetSpec("icons/setuphelfer-icon.png", "usr/share/setuphelfer/rescue/assets/icons/setuphelfer-icon.png", "icon"),
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def asset_file_readable(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 64:
        return False
    try:
        head = path.read_bytes()[:16]
    except OSError:
        return False
    return head[:8] == b"\x89PNG\r\n\x1a\n" or head[:2] == b"\xff\xd8"


def build_asset_manifest_entry(source: Path, spec: RescueAssetSpec, repo_root: Path) -> dict[str, Any]:
    return {
        "source_path": str(source.relative_to(repo_root)),
        "target_path": spec.target_rel,
        "opt_target_path": f"opt/setuphelfer-rescue/assets/{spec.source_rel}",
        "sha256": sha256_file(source) if source.is_file() else None,
        "size_bytes": source.stat().st_size if source.is_file() else 0,
        "purpose": spec.purpose,
        "locale": spec.locale,
        "required": spec.required,
        "readable": asset_file_readable(source),
    }


def build_asset_manifest(repo_root: Path) -> dict[str, Any]:
    assets_root = repo_root / "assets" / "rescue"
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for spec in CANONICAL_ASSET_SPECS:
        src = assets_root / spec.source_rel
        if not src.is_file():
            missing.append(spec.source_rel)
            continue
        entries.append(build_asset_manifest_entry(src, spec, repo_root))
    return {
        "schema_version": ASSET_MANIFEST_SCHEMA_VERSION,
        "assets_root": str(assets_root.relative_to(repo_root)),
        "entries": entries,
        "missing_required": missing,
        "complete": not missing,
        "secrets_exposed": False,
    }


def ui_text_has_forbidden_brand(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in FORBIDDEN_BRAND_PHRASES if p in lowered]


def rescue_menu_item_allows_direct_write(item: Mapping[str, Any]) -> bool:
    if item.get("enabled") is False:
        return False
    if item.get("requires_confirmation") is True:
        return False
    risk = str(item.get("write_risk") or "").lower()
    return risk in ("write", "destructive", "high")


def validate_rescue_menu_items(items: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for item in items:
        for key in ("id", "titleKey", "subtitleKey", "actionTarget", "safetyLevel"):
            if not item.get(key):
                errors.append(f"MISSING_{key.upper()}:{item.get('id', '?')}")
        if rescue_menu_item_allows_direct_write(item):
            errors.append(f"DIRECT_WRITE_NOT_ALLOWED:{item.get('id')}")
    return errors
