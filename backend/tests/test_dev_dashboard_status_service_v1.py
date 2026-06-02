from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.dev_dashboard_status_service import build_dcc_profile_block_response


class DevDashboardStatusServiceTests(unittest.TestCase):
    def test_release_profile_returns_block_response(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
            body = build_dcc_profile_block_response()
        self.assertIsNotNone(body)
        assert body is not None
        self.assertEqual(body["code"], "PROFILE_ROUTE_BLOCKED")
        self.assertEqual(body["required_profile"], "local_lab")

    def test_local_lab_profile_not_blocked(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=False):
            body = build_dcc_profile_block_response()
        self.assertIsNone(body)


if __name__ == "__main__":
    unittest.main()

