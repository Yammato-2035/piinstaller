"""Import boundaries for runtime_governance package."""

from __future__ import annotations

from pathlib import Path


def test_runtime_governance_does_not_import_app():
    root = Path(__file__).resolve().parent.parent / "runtime_governance"
    forbidden = ("backend.app", "from app ", "import app")
    for py in root.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{py.name} must not reference {token}"
