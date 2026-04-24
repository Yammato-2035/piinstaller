#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a structured diagnostics evidence record template.")
    parser.add_argument("--id", required=True, help="Evidence ID, e.g. EVID-2026-HW1-001")
    parser.add_argument("--scenario", required=True, help="Scenario identifier, e.g. HW1-01")
    parser.add_argument("--domain", default="backup_restore")
    parser.add_argument("--platform", default="linux_laptop")
    parser.add_argument("--profile", default="profile-linux-laptop-nvme-host")
    parser.add_argument("--source-type", default="hardware_test")
    parser.add_argument("--outcome", default="inconclusive")
    args = parser.parse_args()

    out_dir = Path(__file__).resolve().parents[2] / "data" / "diagnostics" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.id}.json"
    if out_file.exists():
        raise SystemExit(f"File already exists: {out_file}")

    payload = {
        "id": args.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_type": args.source_type,
        "domain": args.domain,
        "platform": args.platform,
        "scenario": args.scenario,
        "test_goal": "",
        "outcome": args.outcome,
        "severity": "low",
        "confidence": "low",
        "system_profile_id": args.profile,
        "storage_profile": "",
        "encryption_profile": "",
        "boot_profile": "",
        "observed_symptoms": [],
        "raw_signals": {},
        "matched_diagnosis_ids": [],
        "diagnosis_links": [],
        "suspected_root_causes": [],
        "confirmed_root_cause": "",
        "corrective_actions": [],
        "unresolved_questions": [],
        "docs_updated": False,
        "faq_updated": False,
        "catalog_updated": False,
        "tests_added": False,
    }
    out_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
