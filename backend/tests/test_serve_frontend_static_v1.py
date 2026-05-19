"""Regression tests for scripts/serve-frontend-production.py (stdlib static SPA server)."""

from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest


def _load_serve_module():
    root = pathlib.Path(__file__).resolve().parents[2]
    path = root / "scripts" / "serve-frontend-production.py"
    spec = importlib.util.spec_from_file_location("serve_frontend_production", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestServeFrontendStaticV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = _load_serve_module()

    def test_spa_fallback_unknown_route(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "index.html").write_text("<html></html>", encoding="utf-8")
            p = self.m.resolve_public_path(root, "/settings")
            self.assertEqual(p, root / "index.html")

    def test_static_file_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "index.html").write_text("i", encoding="utf-8")
            (root / "x.txt").write_text("y", encoding="utf-8")
            p = self.m.resolve_public_path(root, "/x.txt")
            self.assertEqual(p, root / "x.txt")

    def test_path_traversal_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "index.html").write_text("i", encoding="utf-8")
            p = self.m.resolve_public_path(root, "/../outside")
            self.assertIsNone(p)

    def test_api_path_returns_none_from_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "index.html").write_text("i", encoding="utf-8")
            p = self.m.resolve_public_path(root, "/api/version")
            self.assertIsNone(p)


if __name__ == "__main__":
    unittest.main()
