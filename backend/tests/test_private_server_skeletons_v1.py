"""Private server skeleton structure tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKEL = REPO / "docs/private-server-skeletons"


class PrivateServerSkeletonsV1Tests(unittest.TestCase):
    def test_monorepo_readme(self) -> None:
        self.assertTrue((SKEL / "README.md").is_file())

    def test_beta_fastapi_entry(self) -> None:
        self.assertTrue((SKEL / "beta-registration-server/app/main.py").is_file())

    def test_telemetry_forbidden_routes_in_skeleton(self) -> None:
        text = (SKEL / "telemetry-server/app/main.py").read_text(encoding="utf-8")
        self.assertIn("/execute", text)
        self.assertIn("forbidden_route", text)

    def test_diagnostics_pii_rejection(self) -> None:
        text = (SKEL / "diagnostics-server/app/main.py").read_text(encoding="utf-8")
        self.assertIn("rejected_pii", text)

    def test_docker_compose_lab(self) -> None:
        self.assertTrue((SKEL / "infra/docker-compose.lab.yml").is_file())

    def test_bootstrap_script_exists(self) -> None:
        self.assertTrue((REPO / "scripts/bootstrap-setuphelfer-private-repo.sh").is_file())

    def test_lab_mocks_script_exists(self) -> None:
        self.assertTrue((REPO / "scripts/start-rescue-lab-mocks.sh").is_file())


if __name__ == "__main__":
    unittest.main()
