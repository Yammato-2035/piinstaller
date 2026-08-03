"""
Driver catalog — vendor keyword to official manufacturer support-page lookup.

Informational only (plan-only / documentation, matches
core.diagnostic_finding_contract.RecommendationMode.DOCUMENTATION): a match
returns a name and an official manufacturer URL, never a download, install,
or execute action. Deliberately not exhaustive — it is meant to grow as new
vendors are encountered (see docs/knowledge-base/rescue/
DRIVER_CATALOG_AND_PERIPHERAL_DISCOVERY.md), not to claim full coverage of
every chipset/CPU/GPU/peripheral vendor of the last 20 years.

Seeded from the existing MANUFACTURER_DRIVER_LINKS list in
frontend/src/pages/PeripheryScan.tsx (single source of truth is this module;
the frontend list predates it and should eventually consume this instead of
duplicating it).
"""

from __future__ import annotations

from typing import Any

DRIVER_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "vendor": "NVIDIA",
        "official_url": "https://www.nvidia.com/Download/index.aspx",
        "keywords": ("nvidia", "geforce", "quadro", "tesla"),
        "categories": ("gpu",),
    },
    {
        "vendor": "AMD",
        "official_url": "https://www.amd.com/en/support",
        "keywords": ("amd", "radeon", "ati "),
        "categories": ("gpu", "cpu"),
    },
    {
        "vendor": "Intel",
        "official_url": "https://www.intel.com/content/www/us/en/download/785597/intel-graphics-drivers.html",
        "keywords": ("intel", "graphics", "uhd", "iris"),
        "categories": ("gpu", "cpu"),
    },
    {
        "vendor": "Realtek",
        "official_url": "https://www.realtek.com/en/downloads",
        "keywords": ("realtek", "rtl"),
        "categories": ("audio", "network"),
    },
    {
        "vendor": "Broadcom",
        "official_url": "https://www.broadcom.com/support",
        "keywords": ("broadcom", "bcm"),
        "categories": ("network",),
    },
    {
        "vendor": "Qualcomm",
        "official_url": "https://www.qualcomm.com/support",
        "keywords": ("qualcomm", "atheros"),
        "categories": ("network",),
    },
    {
        "vendor": "Logitech",
        "official_url": "https://support.logitech.com/",
        "keywords": ("logitech",),
        "categories": ("input",),
    },
    {
        "vendor": "Corsair",
        "official_url": "https://github.com/ckb-next/ckb-next",
        "keywords": ("corsair",),
        "categories": ("input",),
    },
    {
        "vendor": "Lenovo",
        "official_url": "https://pcsupport.lenovo.com/",
        "keywords": ("lenovo",),
        "categories": ("mainboard",),
    },
    {
        "vendor": "Dell",
        "official_url": "https://www.dell.com/support/home",
        "keywords": ("dell",),
        "categories": ("mainboard",),
    },
    {
        "vendor": "HP",
        "official_url": "https://support.hp.com/",
        "keywords": ("hewlett", "hp "),
        "categories": ("mainboard", "printer"),
    },
    {
        "vendor": "Canon",
        "official_url": "https://www.canon.de/support/",
        "keywords": ("canon",),
        "categories": ("printer",),
    },
    {
        "vendor": "Epson",
        "official_url": "https://www.epson.de/support",
        "keywords": ("epson",),
        "categories": ("printer",),
    },
    {
        "vendor": "Brother",
        "official_url": "https://support.brother.com/",
        "keywords": ("brother",),
        "categories": ("printer",),
    },
)


def match_driver_hint(text: str) -> dict[str, str] | None:
    """Return {"vendor", "official_url"} for the first catalog entry whose
    keyword appears in `text` (case-insensitive), or None."""
    lowered = (text or "").lower()
    for entry in DRIVER_CATALOG:
        if any(keyword in lowered for keyword in entry["keywords"]):
            return {"vendor": entry["vendor"], "official_url": entry["official_url"]}
    return None
