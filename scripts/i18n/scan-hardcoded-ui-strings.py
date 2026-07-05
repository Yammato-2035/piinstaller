#!/usr/bin/env python3
"""Scan frontend for likely hardcoded UI strings (Phase-1 marathon)."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN_DIRS = (
    REPO / "frontend/src/rescue",
    REPO / "frontend/src/pages/SettingsPage.tsx",
    REPO / "frontend/src/components/dev-dashboard",
)
PATTERNS = (
    re.compile(r"""setError\(\s*['"]([^'"]{6,})['"]"""),
    re.compile(r"""de \? ['"]([^'"]{6,})['"]\s*:\s*['"]"""),
    re.compile(r"""<h[23][^>]*>([A-ZÄÖÜ][^<]{8,})</h"""),
)

ALLOW = ("setuphelfer", "http", "className", "data-testid", "GET /api")


def main() -> int:
    hits: list[str] = []
    for base in SCAN_DIRS:
        files = [base] if base.is_file() else list(base.rglob("*.tsx"))
        for fp in files:
            if "test." in fp.name:
                continue
            text = fp.read_text(encoding="utf-8", errors="replace")
            if "tPath(" in text or "useTranslation" in text:
                pass
            for pat in PATTERNS:
                for m in pat.finditer(text):
                    s = m.group(1).strip()
                    if any(a in s.lower() for a in ALLOW):
                        continue
                    if re.search(r"[äöüßÄÖÜ]", s) or re.match(r"[A-Z]", s):
                        hits.append(f"{fp.relative_to(REPO)}: {s[:80]}")
    out = REPO / "docs/evidence/I18N_HARDCODED_SCAN.md"
    lines = [
        "# Hardcoded UI strings — Phase-1 scan",
        "",
        f"**Hits:** {len(hits)}",
        "",
    ]
    lines.extend(f"- `{h}`" for h in sorted(set(hits))[:120])
    if len(hits) > 120:
        lines.append(f"\n… und {len(hits) - 120} weitere")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"hardcoded scan: {len(hits)} hits -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
