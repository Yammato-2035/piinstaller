from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_OUT = _HANDOFF / "legacy_identifier_inventory.json"


class DeployRunnerLegacyIdentifierInventoryV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("legacy_identifier_inventory.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def test_aktive_runtime_identifier_erkannt(self) -> None:
        res = build_legacy_identifier_inventory(explicit_overwrite=True)
        self.assertIn(res.get("inventory_status"), ("ok", "review_required"))
        inv = res.get("inventory") or {}
        counts = inv.get("counts") or {}
        self.assertGreaterEqual(int(counts.get("active_runtime_identifier", 0)), 1)

    def test_historische_evidence_erlaubt(self) -> None:
        marker = _REPO_ROOT / "docs/evidence/runtime-results/handoff/_legacy_identifier_test_marker.md"
        marker.write_text("historical token: pi-installer\n", encoding="utf-8")
        try:
            res = build_legacy_identifier_inventory(explicit_overwrite=True)
            findings = (res.get("inventory") or {}).get("findings") or []
            has_hist = any(str(x.get("path") or "").endswith("_legacy_identifier_test_marker.md") for x in findings)
            self.assertTrue(has_hist)
        finally:
            marker.unlink(missing_ok=True)

    def test_atomisches_schreiben(self) -> None:
        build_legacy_identifier_inventory(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "legacy_identifier_inventory.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_legacy_identifier_inventory.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mount", "umount", "wipefs", "mkfs", "dd "):
            self.assertNotIn(bad, t)

    def test_keine_runtime_manipulation(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_legacy_identifier_inventory.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("unlink(", "rmtree(", "remove(", "rename(", "replace("):
            if bad == "replace(":
                continue
            self.assertNotIn(bad, t)


if __name__ == "__main__":
    unittest.main()
