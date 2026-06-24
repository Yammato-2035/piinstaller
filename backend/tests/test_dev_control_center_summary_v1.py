"""Control Center summary aggregator — read-only, no fake green."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.dev_control_center_summary import (  # noqa: E402
    build_control_center_summary,
    build_diagnostics_stats,
    build_documentation_stats,
    build_rescue_developer_section,
    build_roadmap_section,
)


class TestDevControlCenterSummary(unittest.TestCase):
    def test_summary_has_all_sections(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "docs" / "evidence").mkdir(parents=True)
            summary = build_control_center_summary(repo_root=repo, dashboard={"runtime_gate": {"passed": True}})
            for key in (
                "runtime",
                "roadmap",
                "dev_server",
                "rescue_developer",
                "documentation",
                "diagnostics",
                "evidence",
                "next_prompts",
            ):
                self.assertIn(key, summary, msg=key)

    def test_missing_roadmap_is_unknown_not_error(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            roadmap = build_roadmap_section(repo)
            self.assertIn(roadmap["status"], ("unknown", "not_available", "available"))
            self.assertNotIn("roadmap_crash", str(roadmap))

    def test_dev_server_disabled_shown(self):
        with patch("devserver.config.load_dev_server_config") as mock_cfg:
            mock_cfg.return_value = type(
                "C",
                (),
                {
                    "enabled": False,
                    "mode": "disabled",
                    "storage_root": "/tmp/x",
                    "ssh_allowed": False,
                    "public_uploads_allowed": False,
                },
            )()
            with patch("devserver.storage.DevServerStorage") as mock_st:
                mock_st.return_value.storage_ok.return_value = True
                mock_st.return_value.list_nodes.return_value = []
                mock_st.return_value.list_reports.return_value = []
                from core.dev_control_center_summary import build_dev_server_section

                sec = build_dev_server_section()
                self.assertFalse(sec["enabled"])
                self.assertEqual(sec["mode"], "disabled")

    def test_ssh_disabled_not_in_errors(self):
        with patch("devserver.config.load_dev_server_config") as mock_cfg:
            mock_cfg.return_value = type(
                "C",
                (),
                {
                    "enabled": True,
                    "mode": "local_lab",
                    "storage_root": "/tmp/x",
                    "ssh_allowed": False,
                    "public_uploads_allowed": False,
                },
            )()
            with patch("devserver.storage.DevServerStorage") as mock_st:
                mock_st.return_value.storage_ok.return_value = True
                mock_st.return_value.list_nodes.return_value = []
                mock_st.return_value.list_reports.return_value = []
                from core.dev_control_center_summary import build_dev_server_section

                sec = build_dev_server_section()
                self.assertFalse(sec["ssh_allowed"])
                self.assertNotIn("ssh_disabled", sec.get("errors") or [])

    def test_public_uploads_disabled_not_error(self):
        with patch("devserver.config.load_dev_server_config") as mock_cfg:
            mock_cfg.return_value = type(
                "C",
                (),
                {
                    "enabled": True,
                    "mode": "local_lab",
                    "storage_root": "/tmp/x",
                    "ssh_allowed": False,
                    "public_uploads_allowed": False,
                },
            )()
            with patch("devserver.storage.DevServerStorage") as mock_st:
                mock_st.return_value.storage_ok.return_value = True
                mock_st.return_value.list_nodes.return_value = []
                mock_st.return_value.list_reports.return_value = []
                from core.dev_control_center_summary import build_dev_server_section

                sec = build_dev_server_section()
                self.assertFalse(sec["public_uploads_allowed"])
                self.assertNotIn("public_uploads_disabled", sec.get("errors") or [])

    def test_translation_pairs_detect_missing(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            faq = repo / "docs" / "faq"
            faq.mkdir(parents=True)
            (faq / "SAMPLE_FAQ_DE.md").write_text("# DE", encoding="utf-8")
            stats = build_documentation_stats(repo)
            pairs = stats["translation_pairs"]
            self.assertGreaterEqual(pairs["complete"], 0)
            self.assertIn("SAMPLE_FAQ", str(pairs.get("missing_en") or pairs.get("missing_de")))

    def test_no_write_actions_in_summary(self):
        with tempfile.TemporaryDirectory() as td:
            summary = build_control_center_summary(repo_root=Path(td), dashboard={})
            blob = str(summary).lower()
            for forbidden in ("start_backup", "run_restore", "rescue_iso_build", "debootstrap"):
                self.assertNotIn(forbidden, blob)

    def test_rescue_iso_not_fake_green(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            sec = build_rescue_developer_section(repo)
            iso_item = next(i for i in sec["items"] if i["id"] == "rescue_iso_dry_build")
            self.assertEqual(iso_item["status"], "pending")

    def test_diagnostics_stats_available(self):
        stats = build_diagnostics_stats()
        self.assertTrue(stats["catalog_available"])
        self.assertGreater(stats["code_count"], 0)


if __name__ == "__main__":
    unittest.main()
