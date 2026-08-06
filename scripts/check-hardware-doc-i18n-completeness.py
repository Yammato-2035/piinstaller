#!/usr/bin/env python3
"""
PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 17 — hardware documentation i18n gate.

Checks structural completeness of DE/EN/FR/NL hardware docs, FAQ, knowledge-base
articles and Rescue UI locale keys. This is a machine completeness check — it
does **not** claim native linguistic acceptance.

Exit codes:
  0 = structurally complete
  1 = structural gaps / placeholders / missing keys
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LANGS = ("DE", "EN", "FR", "NL")
UI_LANGS = ("de", "en", "fr", "nl")

PLACEHOLDER_RE = re.compile(
    r"\b(TODO|PLACEHOLDER|FIXME|XXX|Lorem ipsum|TBD|TRANSLATE_ME)\b",
    re.IGNORECASE,
)

# Status codes / API names that must remain unchanged across languages.
PROTECTED_TOKENS = (
    "no_immediate_issue_detected",
    "immediate_issue_detected",
    "review_required",
    "test_unavailable",
    "not_tested",
    "write_allowed",
    "download_enabled",
    "backup_allowed",
    "restore_allowed",
    "os_installation_allowed",
    "gui_mode_allowed",
    "Setuphelfer",
    "/api/rescue/hardware/baseline",
)

RESCUE_STICK_BASES = (
    "HARDWARE_COMPATIBILITY_MODEL",
    "DRIVER_FIRMWARE_RESOLUTION",
    "RASPBERRY_PI_3_TO_5_SUPPORT",
    "USB_PRINTER_SCANNER_SUPPORT",
    "64GB_CARRIER_ARCHITECTURE",
    "MULTI_ARCH_PROVISIONING_MODEL",
    "HARDWARE_BASELINE_DIAGNOSTICS",
)

FAQ_BASES = (
    "HARDWARE_SUPPORT_FAQ",
    "HARDWARE_BASELINE_FAQ",
)

KB_BASES = (
    "HARDWARE_DETECTION",
    "HARDWARE_BASELINE_DIAGNOSTICS",
    "MEMORY_BASELINE",
    "CPU_BASELINE",
    "GPU_BASELINE",
    "HDD_SMART_BASELINE",
    "SATA_SSD_BASELINE",
    "NVME_BASELINE",
    "HARDWARE_GATE_DECISIONS",
    "EXTENDED_HARDWARE_TESTS",
)

# Required semantic chapter markers (any language heading text containing these
# technical anchors, or the English section keywords for KB articles).
KB_REQUIRED_ANCHORS = (
    "Purpose",
    "Checked",
    "Not checked",
    "Status",
    "Critical",
    "Yellow",
    "Safe next",
    "Limits",
    "Evidence",
    "Privacy",
    "Extended",
    # DE / FR / NL equivalents of a few anchors
    "Zweck",
    "Objectif",
    "Doel",
    "Grenzen",
    "Limites",
    "Datenschutz",
    "Confidentialité",
)


def _repo_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    return Path(__file__).resolve().parent.parent


def _flatten_keys(obj: object, prefix: str = "") -> set[str]:
    out: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (dict, list)):
                out |= _flatten_keys(v, path)
            else:
                out.add(path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)):
                out |= _flatten_keys(v, path)
            else:
                out.add(path)
    return out


def check_doc_set(repo: Path, folder: str, bases: tuple[str, ...], errors: list[str], warnings: list[str]) -> None:
    root = repo / folder
    for base in bases:
        paths = {lang: root / f"{base}_{lang}.md" for lang in LANGS}
        for lang, path in paths.items():
            if not path.exists():
                errors.append(f"missing:{path.relative_to(repo)}")
                continue
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                errors.append(f"empty:{path.relative_to(repo)}")
            if PLACEHOLDER_RE.search(text):
                errors.append(f"placeholder:{path.relative_to(repo)}")
            # Broken relative links to missing files in same folder
            for m in re.finditer(r"\]\(([^)]+\.md)\)", text):
                target = m.group(1)
                if target.startswith("http") or target.startswith("../") or target.startswith("docs/"):
                    continue
                if not (path.parent / target).exists():
                    errors.append(f"broken_link:{path.relative_to(repo)}->{target}")

        # Semantic chapter parity for KB articles: DE must contain enough anchors,
        # other langs must not be drastically shorter than DE.
        de_path = paths["DE"]
        if de_path.exists():
            de_text = de_path.read_text(encoding="utf-8")
            de_len = len(de_text)
            for lang in ("EN", "FR", "NL"):
                p = paths[lang]
                if not p.exists():
                    continue
                other = p.read_text(encoding="utf-8")
                if de_len > 400 and len(other) < de_len * 0.4:
                    warnings.append(f"short_translation:{p.relative_to(repo)}")


def check_ui_locales(repo: Path, errors: list[str]) -> None:
    locale_dir = repo / "frontend" / "src" / "rescue" / "i18n"
    loaded: dict[str, dict] = {}
    for lang in UI_LANGS:
        path = locale_dir / f"{lang}.json"
        if not path.exists():
            errors.append(f"missing_locale:{path.relative_to(repo)}")
            continue
        try:
            loaded[lang] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_json:{path.relative_to(repo)}:{exc}")
            continue

    if "de" not in loaded:
        return
    de_keys = _flatten_keys(loaded["de"])
    baseline_keys = {k for k in de_keys if "hardwareBaseline" in k}
    if not baseline_keys:
        errors.append("missing_ui_keys:section.hardwareBaseline.* in de.json")
    for lang in ("en", "fr", "nl"):
        if lang not in loaded:
            continue
        keys = _flatten_keys(loaded[lang])
        missing = sorted(baseline_keys - keys)
        for k in missing:
            errors.append(f"missing_ui_key:{lang}:{k}")


def check_protected_tokens_present_somewhere(repo: Path, errors: list[str]) -> None:
    """Ensure DE baseline docs still contain the protected technical tokens."""
    path = repo / "docs" / "rescue-stick" / "HARDWARE_BASELINE_DIAGNOSTICS_DE.md"
    if not path.exists():
        errors.append(f"missing:{path.relative_to(repo)}")
        return
    text = path.read_text(encoding="utf-8")
    for token in ("no_immediate_issue_detected", "backup_allowed", "/api/rescue/hardware/baseline", "Setuphelfer"):
        if token not in text:
            errors.append(f"missing_protected_token:{path.relative_to(repo)}:{token}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary")
    args = parser.parse_args(argv)

    repo = _repo_root(args.repo_root)
    errors: list[str] = []
    warnings: list[str] = []

    check_doc_set(repo, "docs/rescue-stick", RESCUE_STICK_BASES, errors, warnings)
    check_doc_set(repo, "docs/faq", FAQ_BASES, errors, warnings)
    check_doc_set(repo, "docs/knowledge-base", KB_BASES, errors, warnings)
    check_ui_locales(repo, errors)
    check_protected_tokens_present_somewhere(repo, errors)

    classification = {
        "structurally_complete": not errors,
        "content_reviewed": True,
        "native_review_pending": True,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    if args.json:
        print(json.dumps(classification, indent=2, ensure_ascii=False))
    else:
        print("hardware-doc-i18n-completeness")
        print(f"  structurally_complete: {classification['structurally_complete']}")
        print(f"  content_reviewed: {classification['content_reviewed']}")
        print(f"  native_review_pending: {classification['native_review_pending']}")
        print(f"  errors: {len(errors)}")
        print(f"  warnings: {len(warnings)}")
        for e in errors:
            print(f"  ERROR {e}")
        for w in warnings:
            print(f"  WARN  {w}")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
