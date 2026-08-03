"""
Curated hardware compatibility catalog + quirks loader — read-only.

PI-RS-HW-COMPAT-PROVISION-001 Phase 10.

Loads ``data/hardware/hardware_compat_catalog.json`` and
``data/hardware/hardware_quirks.json``. This module never contains hardcoded
per-device data itself — see the audit rule ("thousands of devices in source code"
is forbidden). Matching is deliberately narrow (DMI product string or exact
vendor/product PCI-ID pair), never a fuzzy name match.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HARDWARE_COMPAT_CATALOG_VERSION = 1

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "hardware"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_compat_catalog(*, data_dir: Path | None = None) -> list[dict[str, Any]]:
    root = data_dir or _DEFAULT_DATA_DIR
    data = _load_json(root / "hardware_compat_catalog.json")
    return list(data.get("entries") or [])


def load_quirks(*, data_dir: Path | None = None) -> list[dict[str, Any]]:
    root = data_dir or _DEFAULT_DATA_DIR
    data = _load_json(root / "hardware_quirks.json")
    return list(data.get("quirks") or [])


def validate_catalog_against_schema(*, data_dir: Path | None = None) -> list[str]:
    """Best-effort JSON-Schema validation. Returns list of error strings (empty = ok).
    Never raises — a missing ``jsonschema`` package degrades to a structural-only check."""
    root = data_dir or _DEFAULT_DATA_DIR
    catalog = _load_json(root / "hardware_compat_catalog.json")
    schema = _load_json(root / "hardware_compat_catalog.schema.json")
    if not schema or not catalog:
        return []
    try:
        import jsonschema

        errors: list[str] = []
        for entry in catalog.get("entries") or []:
            try:
                jsonschema.validate(entry, schema)
            except jsonschema.ValidationError as exc:  # noqa: PERF203
                errors.append(f"{entry.get('entry_id', '?')}: {exc.message}")
        return errors
    except ImportError:
        # Structural fallback: required top-level keys only.
        errors = []
        for entry in catalog.get("entries") or []:
            for required in ("entry_id", "match", "classification", "support_level", "evidence_paths"):
                if required not in entry:
                    errors.append(f"{entry.get('entry_id', '?')}: missing '{required}'")
        return errors


def match_catalog_entry(
    *,
    dmi_product: str | None = None,
    vendor_id: str | None = None,
    product_id: str | None = None,
    catalog: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Exact match only — DMI product string equality or vendor+product PCI-ID pair."""
    entries = catalog if catalog is not None else load_compat_catalog()
    for entry in entries:
        match = entry.get("match") or {}
        if dmi_product and match.get("dmi_product") and match["dmi_product"] == dmi_product:
            return entry
        if (
            vendor_id
            and product_id
            and match.get("vendor_id")
            and match.get("product_id")
            and match["vendor_id"].lower() == vendor_id.lower()
            and match["product_id"].lower() == product_id.lower()
        ):
            return entry
    return None


def match_quirks(
    *,
    dmi_product: str | None = None,
    driver_name: str | None = None,
    quirks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows = quirks if quirks is not None else load_quirks()
    out: list[dict[str, Any]] = []
    for quirk in rows:
        match = quirk.get("match") or {}
        product_ok = not match.get("dmi_product") or match.get("dmi_product") == dmi_product
        driver_ok = not match.get("driver_name") or match.get("driver_name") == driver_name
        if product_ok and driver_ok and (match.get("dmi_product") or match.get("driver_name")):
            out.append(quirk)
    return out


def build_hardware_compat_catalog_diagnostics(*, data_dir: Path | None = None) -> dict[str, Any]:
    return {
        "catalog_version": HARDWARE_COMPAT_CATALOG_VERSION,
        "module": "core.hardware_compat_catalog",
        "entry_count": len(load_compat_catalog(data_dir=data_dir)),
        "quirk_count": len(load_quirks(data_dir=data_dir)),
        "exhaustive": False,
        "read_only": True,
    }


__all__ = [
    "HARDWARE_COMPAT_CATALOG_VERSION",
    "load_compat_catalog",
    "load_quirks",
    "validate_catalog_against_schema",
    "match_catalog_entry",
    "match_quirks",
    "build_hardware_compat_catalog_diagnostics",
]
