#!/usr/bin/env python3
"""
start.py – Setuphelfer Partitionierungstool
Einstiegspunkt: python3 start.py
"""

import sys
import os

# Projektpfad setzen
PROJEKT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJEKT_DIR)


def check_voraussetzungen():
    """Prüft ob alle nötigen Tools vorhanden sind."""
    probleme = []

    # Python-Version
    if sys.version_info < (3, 10):
        probleme.append(f"Python 3.10+ benötigt (gefunden: {sys.version})")

    # tkinter
    try:
        import tkinter
    except ImportError:
        probleme.append(
            "tkinter fehlt. Installation:\n"
            "  Ubuntu/Debian: sudo apt install python3-tk\n"
            "  Fedora:        sudo dnf install python3-tkinter\n"
            "  Arch:          sudo pacman -S tk"
        )

    # lsblk
    import shutil
    if not shutil.which("lsblk"):
        probleme.append("lsblk fehlt (util-linux Paket benötigt)")

    return probleme


def main():
    print("═" * 50)
    print("  Setuphelfer Partitionshelfer")
    print("  Phase 1: Anzeige, Sicherheitsanalyse & geführte Hilfe")
    print("═" * 50)

    # Voraussetzungen prüfen
    probleme = check_voraussetzungen()
    if probleme:
        print("\n❌ Fehlende Voraussetzungen:\n")
        for p in probleme:
            print(f"  • {p}")
        print()
        sys.exit(1)

    print("✓ Alle Voraussetzungen erfüllt")
    print("  Starte grafische Oberfläche...\n")

    # App starten
    from ui.main_window import SetuphelferApp
    app = SetuphelferApp()
    app.starten()


if __name__ == "__main__":
    main()
