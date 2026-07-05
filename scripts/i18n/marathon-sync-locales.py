#!/usr/bin/env python3
"""Sync rescue + main frontend locales for Phase-1 translation marathon."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "i18n"))
from marathon_glossary import (  # noqa: E402
    translate_de_to_fr,
    translate_de_to_nl,
    translate_en_to_fr,
    translate_en_to_nl,
)


def flatten(obj: dict[str, Any], prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, val in obj.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict):
            out.update(flatten(val, path))
        elif isinstance(val, str):
            out[path] = val
    return out


def unflatten(flat: dict[str, str]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    for path, value in sorted(flat.items()):
        parts = path.split(".")
        cur: dict[str, Any] = root
        for part in parts[:-1]:
            nxt = cur.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[part] = nxt
            cur = nxt
        cur[parts[-1]] = value
    return root


def sync_rescue_locales() -> dict[str, int]:
    base = REPO / "frontend/src/rescue/i18n"
    de = json.loads((base / "de.json").read_text(encoding="utf-8"))
    en = json.loads((base / "en.json").read_text(encoding="utf-8"))
    stats: dict[str, int] = {}
    for loc, fn, translator in (
        ("fr", translate_de_to_fr, translate_de_to_fr),
        ("nl", translate_de_to_nl, translate_de_to_nl),
    ):
        target_path = base / f"{loc}.json"
        existing = json.loads(target_path.read_text(encoding="utf-8")) if target_path.is_file() else {}
        flat_de = flatten(de)
        flat_en = flatten(en)
        flat_existing = flatten(existing)
        added = 0
        for key, de_val in flat_de.items():
            if key in flat_existing and flat_existing[key].strip():
                continue
            src = flat_en.get(key) or de_val
            if loc == "fr":
                flat_existing[key] = translate_en_to_fr(src) if key in flat_en else translate_de_to_fr(de_val)
            else:
                flat_existing[key] = translate_en_to_nl(src) if key in flat_en else translate_de_to_nl(de_val)
            added += 1
        target_path.write_text(
            json.dumps(unflatten(flat_existing), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        stats[f"rescue_{loc}_added"] = added
        stats[f"rescue_{loc}_total"] = len(flat_existing)
    return stats


def sync_main_locales() -> dict[str, int]:
    base = REPO / "frontend/src/locales"
    en = json.loads((base / "en.json").read_text(encoding="utf-8"))
    dcc_en = json.loads((base / "dccVis001.en.json").read_text(encoding="utf-8"))
    flat_en = {**flatten(en), **flatten(dcc_en)}
    stats: dict[str, int] = {}
    for loc, translator in (("fr", translate_en_to_fr), ("nl", translate_en_to_nl)):
        main_path = base / f"{loc}.json"
        dcc_path = base / f"dccVis001.{loc}.json"
        existing_main = json.loads(main_path.read_text(encoding="utf-8")) if main_path.is_file() else {}
        existing_dcc = json.loads(dcc_path.read_text(encoding="utf-8")) if dcc_path.is_file() else {}
        flat_main = flatten(existing_main)
        flat_dcc = flatten(existing_dcc)
        added_main = added_dcc = 0
        for key, val in flat_en.items():
            if key.startswith("devDashboard.vis."):
                if key not in flat_dcc or not str(flat_dcc.get(key, "")).strip():
                    flat_dcc[key] = translator(val)
                    added_dcc += 1
            else:
                if key not in flat_main or not str(flat_main.get(key, "")).strip():
                    flat_main[key] = translator(val)
                    added_main += 1
        main_path.write_text(json.dumps(unflatten(flat_main), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        dcc_path.write_text(json.dumps(unflatten(flat_dcc), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stats[f"main_{loc}_added"] = added_main
        stats[f"dcc_{loc}_added"] = added_dcc
        stats[f"main_{loc}_total"] = len(flat_main)
    return stats


def main() -> int:
    rescue = sync_rescue_locales()
    main_stats = sync_main_locales()
    print("marathon-sync-locales:", json.dumps({**rescue, **main_stats}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
