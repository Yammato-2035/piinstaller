"""Security: sudo_store.store_password must use has_password() guard in extracted handlers."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

HANDLER_FILES = [
    _backend / "core/system_handlers.py",
    _backend / "core/backup_readonly_handlers.py",
    _backend / "core/backup_execute_handlers.py",
]

BAD_PATTERN = re.compile(
    r"if\s+not\s+rt\.sudo_store\(\)\.get_password\(\)\s*:\s*\n\s*rt\.sudo_store\(\)\.store_password",
)


class TestSecuritySudoStoreHasPasswordGuardV1(unittest.TestCase):
    def test_no_get_password_guard_before_store(self) -> None:
        for path in HANDLER_FILES:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(BAD_PATTERN.search(text), f"unsafe sudo store guard in {path.name}")

    def test_asus_set_profile_uses_has_password(self) -> None:
        text = (_backend / "core/system_handlers.py").read_text(encoding="utf-8")
        block = text.split("async def set_asus_fan_profile")[1].split("\n\nasync def")[0]
        self.assertIn("has_password()", block)
        self.assertIn("store_password(sudo_password)", block)


if __name__ == "__main__":
    unittest.main()
