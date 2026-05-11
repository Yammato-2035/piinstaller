"""Deploy cache execute local-only tests."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mod = _load("deploy/cache_execute.py", "setuphelfer_deploy_cache_execute_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_cache_execute_routes_test")


class TestDeployCacheExecuteV1(unittest.TestCase):
    def setUp(self):
        mod._DEPLOY_CACHE_SESSION_STORE.clear()
        self._orig_prefixes = list(mod._ALLOWED_CACHE_PREFIXES)

    def tearDown(self):
        mod._ALLOWED_CACHE_PREFIXES = self._orig_prefixes

    def _mk_source(self, path: str, *, stype: str = "local_image", checksum: str = "") -> dict:
        return {
            "source_id": "SRC_LOCAL",
            "type": stype,
            "name": "local-test",
            "local_path": path,
            "checksum": checksum,
        }

    def _mk_plan(self, cache_target: str, status: str = "ok") -> dict:
        return {
            "plan_status": status,
            "cache": {
                "cache_targets": [cache_target],
                "selected_cache_target": cache_target,
            },
        }

    def _create_session(self, source: dict, plan: dict) -> dict:
        return mod.create_deploy_cache_session({"source": source, "cache_plan": plan})

    def _execute(self, sess: dict, source: dict, plan: dict, token: str | None = None) -> dict:
        return mod.execute_deploy_cache(
            {
                "cache_session_id": sess.get("cache_session_id"),
                "confirmation_token": token if token is not None else sess.get("confirmation_token"),
                "source": source,
                "cache_plan": plan,
            }
        )

    def test_remote_image_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            src = self._mk_source(f"{td}/x.img", stype="remote_image")
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            r = self._create_session(src, plan)
            self.assertEqual(r["code"], "DEPLOY_CACHE_SOURCE_NOT_LOCAL")

    def test_missing_local_file_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            src = self._mk_source(f"{td}/missing.img")
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            r = self._create_session(src, plan)
            self.assertEqual(r["code"], "DEPLOY_CACHE_LOCAL_IMAGE_MISSING")

    def test_invalid_extension_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.txt"
            p.write_text("x", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            r = self._create_session(src, plan)
            self.assertEqual(r["code"], "DEPLOY_CACHE_LOCAL_IMAGE_INVALID")

    def test_session_created(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            r = self._create_session(src, plan)
            self.assertEqual(r["code"], "DEPLOY_CACHE_SESSION_CREATED")

    def test_wrong_token_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            out = self._execute(s, src, plan, token="wrong")
            self.assertEqual(out["code"], "DEPLOY_CACHE_TOKEN_INVALID")

    def test_session_expired_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            sid = str(s["cache_session_id"])
            mod._DEPLOY_CACHE_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            out = self._execute(s, src, plan)
            self.assertEqual(out["code"], "DEPLOY_CACHE_SESSION_EXPIRED")

    def test_source_mismatch_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            wrong = dict(src)
            wrong["name"] = "other"
            out = self._execute(s, wrong, plan)
            self.assertEqual(out["code"], "DEPLOY_CACHE_SOURCE_MISMATCH")

    def test_checksum_ok(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p), checksum="sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            out = self._execute(s, src, plan)
            self.assertEqual(out["code"], "DEPLOY_CACHE_EXECUTE_COMPLETED")
            self.assertEqual(out["verification"].get("code"), "DEPLOY_CACHE_CHECKSUM_OK")

    def test_checksum_failed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p), checksum="sha256:deadbeef")
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            out = self._execute(s, src, plan)
            self.assertEqual(out["code"], "DEPLOY_CACHE_EXECUTE_FAILED")
            self.assertIn("DEPLOY_CACHE_CHECKSUM_FAILED", out["errors"])

    def test_copy_completed(self):
        with tempfile.TemporaryDirectory() as td:
            src_dir = Path(td) / "src"
            cache_dir = Path(td) / "cache"
            src_dir.mkdir()
            cache_dir.mkdir()
            p = src_dir / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(str(cache_dir))
            mod._ALLOWED_CACHE_PREFIXES = [str(cache_dir)]
            s = self._create_session(src, plan)
            out = self._execute(s, src, plan)
            self.assertEqual(out["cache_result"]["code"], "DEPLOY_CACHE_COPY_COMPLETED")
            self.assertTrue((cache_dir / "ok.img").exists())

    def test_same_path_ready(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            out = self._execute(s, src, plan)
            self.assertEqual(out["cache_result"]["code"], "DEPLOY_CACHE_READY")

    def test_single_use(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(td)
            mod._ALLOWED_CACHE_PREFIXES = [td]
            s = self._create_session(src, plan)
            first = self._execute(s, src, plan)
            second = self._execute(s, src, plan)
            self.assertEqual(first["code"], "DEPLOY_CACHE_EXECUTE_COMPLETED")
            self.assertEqual(second["code"], "DEPLOY_CACHE_SESSION_ALREADY_USED")

    def test_symlink_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            src_dir = Path(td) / "src"
            outside = Path(td) / "outside"
            cache = Path(td) / "cache"
            src_dir.mkdir()
            outside.mkdir()
            cache.mkdir()
            link = cache / "escape"
            link.symlink_to(outside, target_is_directory=True)
            p = src_dir / "ok.img"
            p.write_text("abc", encoding="utf-8")
            src = self._mk_source(str(p))
            plan = self._mk_plan(str(link))
            mod._ALLOWED_CACHE_PREFIXES = [str(cache)]
            r = self._create_session(src, plan)
            self.assertEqual(r["code"], "DEPLOY_CACHE_TARGET_INVALID")

    def test_no_download_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/cache/download", json={})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
