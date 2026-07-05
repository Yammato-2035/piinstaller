#!/usr/bin/env python3
"""Generate missing DE/EN/FR/NL documentation pairs for Phase-1 marathon."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "i18n"))
sys.path.insert(0, str(REPO / "backend"))
from marathon_glossary import (  # noqa: E402
    doc_banner,
    translate_de_to_en,
    translate_de_to_fr,
    translate_de_to_nl,
    translate_en_to_fr,
    translate_en_to_nl,
)
from core.dev_control_center_summary import _lang_from_doc_filename  # noqa: E402

PRIORITY_PREFIXES = (
    "faq/",
    "kb/",
    "blueprints/",
    "runbooks/",
    "knowledge-base/rescue/",
    "evidence/rescue/",
    "architecture/RESCUE",
    "architecture/DCC",
    "architecture/CORE",
    "architecture/DEPLOY",
    "architecture/APP",
)


def lang_suffix(lang: str) -> str:
    return f"_{lang.upper()}.md"


def dot_suffix(lang: str) -> str:
    return f".{lang.lower()}.md"


def find_file(docs_dir: Path, rel_base: str, lang: str) -> Path | None:
    parent = docs_dir / Path(rel_base).parent
    name = Path(rel_base).name
    for pattern in (
        f"{name}_{lang.upper()}.md",
        f"{name}_{lang.lower()}.md",
        f"{name}.{lang.lower()}.md",
        f"{name}.{lang.upper()}.md",
    ):
        p = parent / pattern
        if p.is_file():
            return p
    return None


def dest_lang_path(src: Path, rel_base: str, lang: str) -> Path:
    """Mirror DE/EN filename convention (underscore/dot, case) for FR/NL output."""
    name = Path(rel_base).name
    parent = src.parent
    m = re.match(r"^.+_(de|en|fr|nl)\.md$", src.name, re.I)
    if m:
        case = m.group(1)
        suffix = lang.lower() if case.islower() else lang.upper()
        return parent / f"{name}_{suffix}.md"
    return parent / f"{name}.{lang.lower()}.md"


def write_if_missing(path: Path, content: str, *, dry_run: bool = False) -> bool:
    if path.is_file():
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return True


def translate_md_body(text: str, target: str) -> str:
    if target == "EN":
        return translate_de_to_en(text)
    if target == "FR":
        return translate_en_to_fr(translate_de_to_en(text)) if "_DE." in text or "_DE.md" in text else translate_en_to_fr(text)
    if target == "NL":
        return translate_en_to_nl(translate_de_to_en(text)) if "_DE." in text or "_DE.md" in text else translate_en_to_nl(text)
    if target == "DE":
        # EN → DE (light reverse via EN glossary inversion — use EN source as base)
        return text  # caller passes pre-translated
    return text


def scan_bases(docs_dir: Path) -> dict[str, set[str]]:
    bases: dict[str, set[str]] = {}
    for fp in docs_dir.rglob("*.md"):
        parsed = _lang_from_doc_filename(fp.name)
        if not parsed:
            continue
        base_name, lang = parsed
        key = f"{fp.parent.relative_to(docs_dir)}/{base_name}".replace("\\", "/")
        bases.setdefault(key, set()).add(lang)
    return bases


def is_priority(key: str) -> bool:
    return any(key.startswith(p) or p.rstrip("/") in key for p in PRIORITY_PREFIXES)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Sync DE/EN/FR/NL documentation pairs")
    parser.add_argument(
        "--coverage",
        type=int,
        default=50,
        help="Target FR/NL coverage percent of DE/EN pairs (default 50; use 100 for full rollout)",
    )
    parser.add_argument("--all-prefixes", action="store_true", help="Include all docs paths, not only priority prefixes")
    args = parser.parse_args()
    coverage_pct = max(1, min(100, args.coverage))

    docs_dir = REPO / "docs"
    bases = scan_bases(docs_dir)
    stats = {"de_created": 0, "en_created": 0, "fr_created": 0, "nl_created": 0}

    # 1) Missing DE (has EN only)
    for key, langs in sorted(bases.items()):
        if "EN" not in langs or "DE" in langs:
            continue
        if not is_priority(key) and not key.startswith("architecture/") and not args.all_prefixes:
            continue
        src = find_file(docs_dir, key, "EN")
        if not src:
            continue
        body = src.read_text(encoding="utf-8")
        # Simple DE: translate title line + body via de from en (approximate)
        de_body = translate_md_body(body, "EN")  # placeholder — use EN with DE banner for arch
        # Better: use reverse - for architecture EN→DE use glossary on EN
        from marathon_glossary import EN_TO_FR  # noqa: F401 — keep import style
        de_text = body
        for en, de in (
            ("Overview", "Überblick"),
            ("Status", "Stand"),
            ("Architecture", "Architektur"),
            ("Migration", "Migration"),
            ("Router", "Router"),
            ("Facade", "Fassade"),
            ("Deploy", "Deploy"),
            ("Diagnostics", "Diagnostik"),
            ("Rescue", "Rettung"),
            ("Target", "Ziel"),
            ("Rules", "Regeln"),
            ("Audit", "Audit"),
            ("Extraction", "Extraktion"),
            ("required", "erforderlich"),
            ("optional", "optional"),
            ("not available", "nicht verfügbar"),
        ):
            de_text = de_text.replace(en, de)
        out = doc_banner("DE", src.relative_to(REPO).as_posix()) + de_text
        dest = dest_lang_path(src, key, "DE")
        if write_if_missing(dest, out):
            stats["de_created"] += 1
            bases.setdefault(key, set()).add("DE")

    # 2) Missing EN (has DE only) — rescue/faq priority
    for key, langs in sorted(bases.items()):
        if "DE" not in langs or "EN" in langs:
            continue
        if not is_priority(key) and not args.all_prefixes:
            continue
        src = find_file(docs_dir, key, "DE")
        if not src:
            continue
        body = src.read_text(encoding="utf-8")
        en_text = translate_de_to_en(body)
        out = doc_banner("EN", src.relative_to(REPO).as_posix()) + en_text
        dest = dest_lang_path(src, key, "EN")
        if write_if_missing(dest, out):
            stats["en_created"] += 1
            bases.setdefault(key, set()).add("EN")

    # Refresh bases after creates
    bases = scan_bases(docs_dir)
    de_en_keys = [k for k, v in bases.items() if "DE" in v and "EN" in v]

    # 3) FR/NL until target coverage of DE+EN pairs
    target_fr = max(1, (len(de_en_keys) * coverage_pct + 99) // 100)
    current_fr = sum(1 for k in de_en_keys if "FR" in bases.get(k, set()))
    need_fr = max(0, target_fr - current_fr)

    fr_created = 0
    for key in sorted(de_en_keys, key=lambda k: (0 if is_priority(k) else 1, k)):
        if fr_created >= need_fr:
            break
        if "FR" in bases.get(key, set()):
            continue
        if not is_priority(key) and not args.all_prefixes:
            continue
        src = find_file(docs_dir, key, "EN") or find_file(docs_dir, key, "DE")
        if not src:
            continue
        body = src.read_text(encoding="utf-8")
        fr_text = translate_en_to_fr(body) if re.search(r"_(en|EN)\.md$", src.name) or src.name.endswith(".en.md") else translate_de_to_fr(body)
        out = doc_banner("FR", src.relative_to(REPO).as_posix()) + fr_text
        dest = dest_lang_path(src, key, "FR")
        if write_if_missing(dest, out):
            stats["fr_created"] += 1
            fr_created += 1
            bases.setdefault(key, set()).add("FR")

    bases = scan_bases(docs_dir)
    de_en_keys = [k for k, v in bases.items() if "DE" in v and "EN" in v]
    target_nl = max(1, (len(de_en_keys) * coverage_pct + 99) // 100)
    current_nl = sum(1 for k in de_en_keys if "NL" in bases.get(k, set()))
    need_nl = max(0, target_nl - current_nl)
    nl_created = 0
    for key in sorted(de_en_keys, key=lambda k: (0 if is_priority(k) else 1, k)):
        if nl_created >= need_nl:
            break
        if "NL" in bases.get(key, set()):
            continue
        if not is_priority(key) and not args.all_prefixes:
            continue
        src = find_file(docs_dir, key, "EN") or find_file(docs_dir, key, "DE")
        if not src:
            continue
        body = src.read_text(encoding="utf-8")
        nl_text = translate_en_to_nl(body) if re.search(r"_(en|EN)\.md$", src.name) or src.name.endswith(".en.md") else translate_de_to_nl(body)
        out = doc_banner("NL", src.relative_to(REPO).as_posix()) + nl_text
        dest = dest_lang_path(src, key, "NL")
        if write_if_missing(dest, out):
            stats["nl_created"] += 1
            nl_created += 1

    bases = scan_bases(docs_dir)
    de_en = len([k for k, v in bases.items() if "DE" in v and "EN" in v])
    with_fr = len([k for k, v in bases.items() if "DE" in v and "EN" in v and "FR" in v])
    with_nl = len([k for k, v in bases.items() if "DE" in v and "EN" in v and "NL" in v])
    stats["de_en_pairs"] = de_en
    stats["fr_coverage_pct"] = round(100 * with_fr / de_en, 1) if de_en else 0
    stats["nl_coverage_pct"] = round(100 * with_nl / de_en, 1) if de_en else 0
    print("marathon-sync-doc-translations:", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
