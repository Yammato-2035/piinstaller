"""Hilfen für systemd-Template-Validierung."""

from __future__ import annotations

from pathlib import Path

TEMPLATE_REL = Path("packaging/systemd/setuphelfer-dev-agent.service")


def template_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    return root / TEMPLATE_REL


def read_template(repo_root: Path | None = None) -> str:
    return template_path(repo_root).read_text(encoding="utf-8")
