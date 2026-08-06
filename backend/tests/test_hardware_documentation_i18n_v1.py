"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 17: hardware documentation i18n gate."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "check-hardware-doc-i18n-completeness.py"


class TestHardwareDocumentationI18nGate(unittest.TestCase):
    def test_script_exists_and_is_executable_via_python(self) -> None:
        self.assertTrue(_SCRIPT.exists())

    def test_gate_passes_structurally(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--repo-root", str(_REPO), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["structurally_complete"])
        self.assertTrue(payload["native_review_pending"])
        self.assertEqual(payload["error_count"], 0)

    def test_ui_hardware_baseline_keys_match_across_locales(self) -> None:
        locale_dir = _REPO / "frontend" / "src" / "rescue" / "i18n"

        def flatten(obj, prefix=""):
            out = set()
            if isinstance(obj, dict):
                for k, v in obj.items():
                    path = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, (dict, list)):
                        out |= flatten(v, path)
                    else:
                        out.add(path)
            return out

        de = flatten(json.loads((locale_dir / "de.json").read_text(encoding="utf-8")))
        baseline = {k for k in de if "hardwareBaseline" in k}
        self.assertGreater(len(baseline), 10)
        for lang in ("en", "fr", "nl"):
            keys = flatten(json.loads((locale_dir / f"{lang}.json").read_text(encoding="utf-8")))
            missing = baseline - keys
            self.assertEqual(missing, set(), msg=f"missing in {lang}: {sorted(missing)[:10]}")

    def test_required_doc_bases_present_in_all_four_languages(self) -> None:
        bases = {
            "docs/rescue-stick": [
                "HARDWARE_COMPATIBILITY_MODEL",
                "HARDWARE_BASELINE_DIAGNOSTICS",
                "DRIVER_FIRMWARE_RESOLUTION",
                "RASPBERRY_PI_3_TO_5_SUPPORT",
                "USB_PRINTER_SCANNER_SUPPORT",
                "64GB_CARRIER_ARCHITECTURE",
                "MULTI_ARCH_PROVISIONING_MODEL",
            ],
            "docs/faq": ["HARDWARE_SUPPORT_FAQ", "HARDWARE_BASELINE_FAQ"],
            "docs/knowledge-base": [
                "HARDWARE_DETECTION",
                "HARDWARE_BASELINE_DIAGNOSTICS",
                "MEMORY_BASELINE",
                "CPU_BASELINE",
                "GPU_BASELINE",
                "HDD_SMART_BASELINE",
                "SATA_SSD_BASELINE",
                "NVME_BASELINE",
                "HARDWARE_GATE_DECISIONS",
                "EXTENDED_HARDWARE_TESTS",
            ],
        }
        for folder, names in bases.items():
            for name in names:
                for lang in ("DE", "EN", "FR", "NL"):
                    path = _REPO / folder / f"{name}_{lang}.md"
                    self.assertTrue(path.exists(), msg=str(path))
                    self.assertGreater(path.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
