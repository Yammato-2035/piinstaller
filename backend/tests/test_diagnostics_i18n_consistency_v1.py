import json
import unittest
from pathlib import Path


class TestDiagnosticsI18nConsistencyV1(unittest.TestCase):
    def test_diagnostics_panel_keys_exist_in_de_and_en(self):
        root = Path(__file__).resolve().parent.parent.parent
        de = json.loads((root / "frontend/src/locales/de.json").read_text(encoding="utf-8"))
        en = json.loads((root / "frontend/src/locales/en.json").read_text(encoding="utf-8"))
        keys = [
            "diagnostics.panel.badge",
            "diagnostics.panel.noPrimary",
            "diagnostics.panel.meta",
        ]
        for k in keys:
            self.assertIn(k, de)
            self.assertIn(k, en)


if __name__ == "__main__":
    unittest.main()
