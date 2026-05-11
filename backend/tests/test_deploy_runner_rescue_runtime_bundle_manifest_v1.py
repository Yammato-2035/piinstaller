from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_runtime_assembly_pipeline import (
    build_rescue_backend_runtime_assembly,
    build_rescue_frontend_runtime_assembly,
    build_rescue_offline_configuration_assembly,
    build_rescue_recovery_runtime_assembly,
    build_rescue_runtime_root,
    build_rescue_startup_script_assembly,
    validate_rescue_runtime_assembly_safety,
)
from deploy.runner_rescue_runtime_bundle_manifest import (
    build_rescue_runtime_bundle_hash_manifest,
    build_rescue_runtime_bundle_inventory,
    build_rescue_runtime_bundle_seal,
    check_rescue_runtime_bundle_consistency,
)

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_RT = _BR / "runtime"
_H = _REPO / "docs/evidence/runtime-results/handoff"
_RUNNER = _REPO / "backend/deploy/runner_rescue_runtime_bundle_manifest.py"
_ROUTES = _REPO / "backend/deploy/routes.py"


class DeployRunnerRescueRuntimeBundleManifestV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        self._backs: dict[Path, bytes | None] = {}
        for p in (
            _BR / "runtime_bundle_inventory.json",
            _BR / "runtime_bundle_hash_manifest.json",
            _BR / "runtime_bundle.seal.json",
            _H / "rescue_runtime_bundle_consistency_check.json",
            _H / "rescue_runtime_assembly_final_gate.json",
            _H / "rescue_runtime_assembly_safety.json",
        ):
            self._backs[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)
        (_RT / "r.json").unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _materialize_runtime(self) -> None:
        build_rescue_runtime_root(explicit_overwrite=True)
        build_rescue_backend_runtime_assembly(explicit_overwrite=True)
        build_rescue_frontend_runtime_assembly(explicit_overwrite=True)
        build_rescue_recovery_runtime_assembly(explicit_overwrite=True)
        build_rescue_offline_configuration_assembly(explicit_overwrite=True)
        build_rescue_startup_script_assembly(explicit_overwrite=True)

    def _seed_assembly_handoffs(self) -> None:
        (_H / "rescue_runtime_assembly_final_gate.json").write_text(
            json.dumps({"gate_status": "ready"}),
            encoding="utf-8",
        )
        (_H / "rescue_runtime_assembly_safety.json").write_text(
            json.dumps({"evaluation": {"rescue_runtime_assembly_safety_eval_status": "ok"}}),
            encoding="utf-8",
        )

    def test_inventory_detects_required_layout(self) -> None:
        self._materialize_runtime()
        r = build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_bundle_inventory_status"), "ok")
        body = r.get("rescue_runtime_bundle_inventory") or {}
        self.assertEqual(body.get("inventory_status"), "ok")
        self.assertEqual(len(body.get("missing_expected_paths") or []), 0)

    def test_inventory_blocked_when_script_missing(self) -> None:
        self._materialize_runtime()
        (_RT / "scripts" / "start-backend.sh").unlink()
        r = build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_bundle_inventory_status"), "blocked")

    def test_hash_manifest_sha256_known_file(self) -> None:
        self._materialize_runtime()
        ph = _RT / "opt" / "setuphelfer" / ".setuphelfer_runtime_assembly_placeholder"
        ph.write_text("bundle-test-bytes\n", encoding="utf-8")
        r = build_rescue_runtime_bundle_hash_manifest(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_bundle_hash_manifest_status"), "ok")
        body = r.get("rescue_runtime_bundle_hash_manifest") or {}
        rel = "opt/setuphelfer/.setuphelfer_runtime_assembly_placeholder"
        self.assertIn(rel, body.get("sha256") or {})

    def test_seal_canonical_bundle_hash(self) -> None:
        self._materialize_runtime()
        build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        build_rescue_runtime_bundle_hash_manifest(explicit_overwrite=True)
        r = build_rescue_runtime_bundle_seal(explicit_overwrite=True)
        self.assertIn(r.get("rescue_runtime_bundle_seal_status"), ("ok", "review_required"))
        seal = r.get("rescue_runtime_bundle_seal") or {}
        self.assertTrue(seal.get("bundle_sha256"))

    def test_consistency_ok_when_aligned(self) -> None:
        self._materialize_runtime()
        self._seed_assembly_handoffs()
        validate_rescue_runtime_assembly_safety(explicit_overwrite=True)
        build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        build_rescue_runtime_bundle_hash_manifest(explicit_overwrite=True)
        build_rescue_runtime_bundle_seal(explicit_overwrite=True)
        c = check_rescue_runtime_bundle_consistency(explicit_overwrite=True)
        self.assertEqual(c.get("rescue_runtime_bundle_consistency_check_status"), "ok")

    def test_consistency_blocks_on_hash_mismatch(self) -> None:
        self._materialize_runtime()
        self._seed_assembly_handoffs()
        validate_rescue_runtime_assembly_safety(explicit_overwrite=True)
        build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        build_rescue_runtime_bundle_hash_manifest(explicit_overwrite=True)
        build_rescue_runtime_bundle_seal(explicit_overwrite=True)
        ph = _RT / "opt" / "setuphelfer" / ".setuphelfer_runtime_assembly_placeholder"
        ph.write_text("tampered\n", encoding="utf-8")
        c = check_rescue_runtime_bundle_consistency(explicit_overwrite=True)
        self.assertEqual(c.get("rescue_runtime_bundle_consistency_check_status"), "blocked")

    def test_inventory_blocks_iso(self) -> None:
        self._materialize_runtime()
        bad = _RT / "evil.iso"
        bad.write_text("not-really-iso", encoding="utf-8")
        r = build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_bundle_inventory_status"), "blocked")
        bad.unlink(missing_ok=True)

    def test_inventory_blocks_legacy_in_json(self) -> None:
        self._materialize_runtime()
        tainted = _RT / "backend_runtime_assembly.json"
        obj = json.loads(tainted.read_text(encoding="utf-8"))
        obj["inject_legacy_marker"] = "/opt/pi-installer/bin"
        tainted.write_text(json.dumps(obj), encoding="utf-8")
        r = build_rescue_runtime_bundle_inventory(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_bundle_inventory_status"), "blocked")

    def test_runner_no_forbidden_calls(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        for bad in ("subprocess", "os.system", "qemu-system", "systemctl"):
            self.assertNotIn(bad, raw)

    def test_routes_runtime_bundle_paths(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for n in (
            "/rescue/runtime-bundle/inventory",
            "/rescue/runtime-bundle/hash-manifest",
            "/rescue/runtime-bundle/seal",
            "/rescue/runtime-bundle/consistency-check",
        ):
            self.assertIn(n, txt)
        low = txt.lower()
        self.assertNotIn("publish-release", low)
        self.assertNotIn("qemu-system", low)
