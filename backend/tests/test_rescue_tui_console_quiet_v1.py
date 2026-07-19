"""Console must stay quiet while TUI owns tty1 (boot-observer must not spam)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMMON = REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
OBSERVER = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-boot-observer.service"
TIMER = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-boot-observer.timer"
QUIET = REPO / "scripts/rescue-live/image/systemd/system.conf.d/10-setuphelfer-quiet-console.conf"
ENTRY = REPO / "scripts/rescue-live/image/setuphelfer-rescue-entrypoint.sh"


class RescueTuiConsoleQuietTests(unittest.TestCase):
    def test_observer_skips_when_tui_active(self) -> None:
        text = OBSERVER.read_text(encoding="utf-8")
        self.assertIn("ConditionPathExists=!/run/setuphelfer/rescue-tui-active", text)

    def test_observer_timer_skips_when_tui_active(self) -> None:
        text = TIMER.read_text(encoding="utf-8")
        self.assertIn("ConditionPathExists=!/run/setuphelfer/rescue-tui-active", text)
        self.assertIn("OnUnitInactiveSec=120s", text)

    def test_tui_mark_active_stops_observer_timer(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_quiet_console_for_tui", text)
        mark = text.split("setuphelfer_rescue_tui_mark_active() {", 1)[1][:900]
        self.assertIn("setuphelfer-rescue-boot-observer.timer", mark)
        self.assertIn("SetShowStatus", text)

    def test_entrypoint_marks_tui_before_exec(self) -> None:
        text = ENTRY.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_tui_mark_active", text)
        self.assertLess(
            text.index("setuphelfer_rescue_tui_mark_active"),
            text.index('exec "${SCRIPT_DIR}/setuphelfer-rescue-tui"'),
        )

    def test_system_conf_disables_show_status(self) -> None:
        text = QUIET.read_text(encoding="utf-8")
        self.assertIn("ShowStatus=no", text)


if __name__ == "__main__":
    unittest.main()
