#!/usr/bin/env python3
"""Generate deploy runner registry evidence (read-only, no runner execution)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from deploy.runner_registry import (  # noqa: E402
    build_runner_registry_from_files,
    build_runner_registry_summary,
    entry_to_dict,
)

OUT_DIR = ROOT / "docs" / "evidence" / "deploy-runner"


def _summary_markdown(summary, entries) -> str:
    lines = [
        "# Deploy Runner Registry Summary (generated)",
        "",
        f"**Total runners:** {summary.total}",
        f"**Device write:** {summary.device_write_count}",
        f"**Destructive:** {summary.destructive_count}",
        f"**Sudo:** {summary.sudo_count}",
        f"**Unknown category:** {summary.unknown_count}",
        "",
        "## By category",
        "",
    ]
    for k, v in sorted(summary.by_category.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## By risk", ""])
    for k, v in sorted(summary.by_risk.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## By execution policy", ""])
    for k, v in sorted(summary.by_policy.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Largest runners", ""])
    for row in summary.largest[:10]:
        lines.append(f"- `{row['runner_id']}` — {row['lines']} lines")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    deploy_root = BACKEND / "deploy"
    entries = build_runner_registry_from_files(root=deploy_root)
    assert all(e.runner_id != "runner_registry" for e in entries)
    summary = build_runner_registry_summary(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "facade_version": summary.facade_version,
        "total": summary.total,
        "summary": {
            "by_category": summary.by_category,
            "by_risk": summary.by_risk,
            "by_policy": summary.by_policy,
            "device_write_count": summary.device_write_count,
            "destructive_count": summary.destructive_count,
            "sudo_count": summary.sudo_count,
            "unknown_count": summary.unknown_count,
        },
        "entries": [entry_to_dict(e) for e in entries],
    }
    (OUT_DIR / "runner_registry.generated.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "runner_registry_summary.md").write_text(
        _summary_markdown(summary, entries),
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} entries to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
