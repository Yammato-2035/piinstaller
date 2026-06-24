"""Isolate DCC gate tests from host /etc/setuphelfer/developer.env."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

RELEASE_DCC_TOKEN = "pytest-dcc-token"
RELEASE_DCC_HEADERS = {"X-Setuphelfer-Developer-Token": RELEASE_DCC_TOKEN}

_RELEASE_DCC_ENV = {
    "SETUPHELFER_INSTALL_PROFILE": "release",
    "DCC_DEVELOPER_ENABLED": "1",
    "DCC_DEVELOPER_TOKEN": RELEASE_DCC_TOKEN,
}

_RELEASE_NO_DCC_ENV = {
    "SETUPHELFER_INSTALL_PROFILE": "release",
    "DCC_DEVELOPER_ENABLED": "",
    "DCC_DEVELOPER_TOKEN": "",
}


@contextmanager
def isolated_release_dcc_client() -> Iterator[dict[str, str]]:
    """Release profile with valid DCC token; ignores host developer.env."""
    with patch("core.developer_capability._load_developer_env_file"), patch.dict(
        os.environ, _RELEASE_DCC_ENV, clear=False
    ):
        yield dict(RELEASE_DCC_HEADERS)


@contextmanager
def isolated_release_no_dcc() -> Iterator[None]:
    """Release profile without DCC configured; ignores host developer.env."""
    with patch("core.developer_capability._load_developer_env_file"), patch(
        "core.developer_capability.load_configured_dcc_token", return_value=(None, None)
    ), patch.dict(os.environ, _RELEASE_NO_DCC_ENV, clear=False):
        yield
