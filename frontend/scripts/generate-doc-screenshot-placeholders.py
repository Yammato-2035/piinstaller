#!/usr/bin/env python3
"""Erzeugt doc-*.png-Platzhalter unter public/docs/screenshots (1360×860 wie Playwright)."""
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    raise SystemExit("Pillow fehlt: pip install Pillow") from e

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "docs" / "screenshots"

FILES: list[tuple[str, str]] = [
    ("doc-dashboard.png", "Dashboard"),
    ("doc-wizard.png", "Setup-Assistent"),
    ("doc-presets.png", "Voreinstellungen"),
    ("doc-security.png", "Sicherheit"),
    ("doc-users.png", "Benutzer"),
    ("doc-devenv.png", "Dev-Umgebung"),
    ("doc-webserver.png", "Webserver"),
    ("doc-mailserver.png", "Mailserver"),
    ("doc-nas.png", "NAS"),
    ("doc-homeautomation.png", "Hausautomatisierung"),
    ("doc-musicbox.png", "Musikbox"),
    ("doc-kino-streaming.png", "Kino / Streaming"),
    ("doc-learning.png", "Lerncomputer"),
    ("doc-monitoring.png", "Monitoring"),
    ("doc-backup.png", "Backup & Restore"),
    ("doc-settings-general.png", "Einstellungen – Allgemein"),
    ("doc-settings-cloud.png", "Einstellungen – Cloud-Backup"),
    ("doc-control-center.png", "Control Center"),
    ("doc-periphery-scan.png", "Peripherie-Scan"),
    ("doc-raspberry-pi-config.png", "Raspberry Pi Config"),
    ("doc-documentation.png", "Dokumentation / Desktop"),
]

W, H = 1360, 860
BG = (30, 41, 59)
SUB = (148, 163, 184)
TITLE = (241, 245, 249)
HINT = (100, 116, 139)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
        font_s = font

    for name, label in FILES:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw.text((48, H // 2 - 72), "SetupHelfer – Dokumentation", fill=SUB, font=font_s)
        draw.text((48, H // 2 - 24), label, fill=TITLE, font=font)
        draw.text(
            (48, H // 2 + 40),
            "Platzhalter – npm run screenshots:docs für echte Aufnahmen",
            fill=HINT,
            font=font_s,
        )
        img.save(OUT / name, "PNG")
        print("OK", name)


if __name__ == "__main__":
    main()
