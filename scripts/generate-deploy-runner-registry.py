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
    registry_policy_warnings,
)
from deploy.runner_result_contract import (  # noqa: E402
    CONTRACT_VERSION,
    RunnerRiskLevel,
    build_empty_result_for_registry_entry,
    validate_registry_result_contract,
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


def _contract_summary_md(payload: dict) -> str:
    lines = [
        "# Deploy Runner Result Contract Summary (generated)",
        "",
        f"**Contract version:** {payload['contract_version']}",
        f"**Empty results buildable:** {payload['empty_results_buildable']}/{payload['total_runners']}",
        f"**Validation failures:** {payload['validation_failures']}",
        f"**Registry policy warnings:** {payload['registry_policy_warning_count']}",
        "",
        "## Example results by risk class",
        "",
    ]
    for risk, example in sorted(payload["examples_by_risk"].items()):
        lines.append(f"### `{risk}`")
        lines.append("")
        lines.append(f"- runner_id: `{example['runner_id']}`")
        lines.append(f"- status: `{example['status']}`")
        lines.append(f"- kind: `{example['kind']}`")
        lines.append(f"- valid: `{example['validation_valid']}`")
        lines.append("")
    if payload.get("policy_warnings"):
        lines.extend(["## Policy warnings (sample)", ""])
        for w in payload["policy_warnings"][:15]:
            lines.append(f"- `{w}`")
        lines.append("")
    return "\n".join(lines)


def _build_contract_payload(entries) -> dict:
    examples_by_risk: dict[str, dict] = {}
    validation_failures = 0
    empty_buildable = 0
    empty_samples: list[dict] = []

    for entry in entries:
        empty = build_empty_result_for_registry_entry(entry)
        v = validate_registry_result_contract(entry, empty)
        if v.valid:
            empty_buildable += 1
        else:
            validation_failures += 1
        risk = entry.risk_level.value
        if risk not in examples_by_risk:
            examples_by_risk[risk] = {
                "runner_id": entry.runner_id,
                "status": empty.status.value,
                "kind": empty.kind.value,
                "validation_valid": v.valid,
                "result": empty.to_dict(),
            }
        if len(empty_samples) < 5:
            empty_samples.append(empty.to_dict())

    policy_warnings = registry_policy_warnings(entries)
    return {
        "contract_version": CONTRACT_VERSION,
        "total_runners": len(entries),
        "empty_results_buildable": empty_buildable,
        "validation_failures": validation_failures,
        "registry_policy_warning_count": len(policy_warnings),
        "policy_warnings": policy_warnings,
        "examples_by_risk": examples_by_risk,
        "empty_result_samples": empty_samples,
        "no_execution_performed": True,
    }


def main() -> int:
    deploy_root = BACKEND / "deploy"
    entries = build_runner_registry_from_files(root=deploy_root)
    assert all(
        e.runner_id not in {"runner_registry", "runner_result_contract"} for e in entries
    )
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

    contract_payload = _build_contract_payload(entries)
    (OUT_DIR / "runner_result_contract.generated.json").write_text(
        json.dumps(contract_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "runner_result_contract_summary.md").write_text(
        _contract_summary_md(contract_payload),
        encoding="utf-8",
    )

    print(f"Wrote {len(entries)} entries to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
