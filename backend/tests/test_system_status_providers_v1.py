"""Phase G.14: System Status Providers contract tests."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

CORE_PATH = _BACKEND / "core" / "system_status_core.py"
PROVIDERS_PATH = _BACKEND / "core" / "system_status_providers.py"


class TestSystemStatusProvidersV1(unittest.TestCase):
    def test_providers_module_has_version_and_api(self) -> None:
        import core.system_status_providers as providers

        self.assertEqual(providers.SYSTEM_STATUS_PROVIDER_VERSION, 1)
        for name in (
            "load_backup_realtest_state",
            "provide_security_config",
            "provide_updates_categorized",
            "build_system_status_providers_diagnostics",
        ):
            self.assertTrue(hasattr(providers, name))
            self.assertTrue(callable(getattr(providers, name)))

    def test_system_status_core_has_no_app_import(self) -> None:
        text = CORE_PATH.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"^\s*(import app|from app\b)", text, re.MULTILINE))
        self.assertIn("system_status_providers", text)

    def test_providers_allow_app_for_legacy_probes(self) -> None:
        text = PROVIDERS_PATH.read_text(encoding="utf-8")
        self.assertIn("import app", text)


if __name__ == "__main__":
    unittest.main()
