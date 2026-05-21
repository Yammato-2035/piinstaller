from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from deploy.runner_rescue_storage_discovery import (
    build_rescue_storage_discovery_plan,
    build_rescue_storage_discovery_result,
    execute_rescue_storage_discovery,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_storage_discovery_plan.json"
_RES = _H / "rescue_storage_discovery_result.json"


class DeployRunnerRescueStorageDiscoveryV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES)}
        for p in (_PLAN, _RES):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_plan_and_execute_mock_lsblk(self) -> None:
        build_rescue_storage_discovery_plan(explicit_overwrite=True)
        fake = json.dumps(
            {
                "blockdevices": [
                    {
                        "name": "nvme0n1",
                        "type": "disk",
                        "children": [
                            {
                                "name": "nvme0n1p1",
                                "type": "part",
                                "fstype": "vfat",
                                "label": "EFI",
                                "uuid": "AAA",
                                "mountpoint": "/boot/efi",
                            },
                            {
                                "name": "nvme0n1p2",
                                "type": "part",
                                "fstype": "ext4",
                                "uuid": "BBB",
                                "mountpoint": "/",
                            },
                        ],
                    }
                ]
            }
        )
        with mock.patch("core.storage_facade.subprocess.run") as m:
            m.side_effect = [
                mock.MagicMock(returncode=0, stdout=fake, stderr=""),
                mock.MagicMock(returncode=0, stdout="/dev/foo: UUID=\"AAA\"\n", stderr=""),
            ]
            with mock.patch("core.storage_facade.detect_block_devices", return_value=[]):
                with mock.patch("core.storage_facade.detect_filesystems", return_value={}):
                    r = execute_rescue_storage_discovery(
                        explicit_overwrite=True, explicit_execute_storage_discovery=True
                    )
        self.assertEqual(r.get("rescue_storage_discovery_result_status"), "ok")
        body = r.get("rescue_storage_discovery_result") or {}
        self.assertTrue((body.get("evaluation") or {}).get("readonly_analysis_only"))

    def test_uuid_conflict_review(self) -> None:
        _RES.write_text(
            json.dumps(
                {
                    "classification": {
                        "flags": {},
                        "uuid_conflicts": ["dup"],
                        "row_count": 2,
                    },
                    "lsblk_rows": [{"name": "x", "uuid": "dup"}, {"name": "y", "uuid": "dup"}],
                }
            ),
            encoding="utf-8",
        )
        r = build_rescue_storage_discovery_result(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_storage_discovery_result_status"), "review_required")
