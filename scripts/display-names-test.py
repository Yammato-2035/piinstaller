#!/usr/bin/env python3
"""
PI-Installer – Test-App: Zeigt auf jedem angeschlossenen Bildschirm den Namen des Ausgangs.
Hilft, den richtigen Wayfire-Ausgabenamen (z. B. DSI-0, HDMI-A-1) für Fensterregeln zu finden.

Start: python3 scripts/display-names-test.py
Voraussetzung: PyQt6 (pip install PyQt6)
"""

import sys
import subprocess


def get_output_names_wlr_randr():
    """Namen der Ausgänge aus wlr-randr auslesen (Fallback)."""
    try:
        r = subprocess.run(
            ["wlr-randr"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0 or not r.stdout:
            return []
        names = []
        for line in r.stdout.splitlines():
            line = line.strip()
            # Zeilen wie "DSI-1 disconnected" oder "HDMI-A-1 connected"
            if line and not line.startswith("Screen") and " " in line:
                name = line.split()[0]
                if name and name not in names:
                    names.append(name)
        return names
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def main_qt():
    from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    app = QApplication(sys.argv)
    screens = app.screens()

    if not screens:
        # Keine Screens von Qt → wlr-randr in einem Fenster anzeigen
        names = get_output_names_wlr_randr()
        win = QWidget()
        win.setWindowTitle("Ausgabenamen (wlr-randr)")
        layout = QVBoxLayout(win)
        text = "Keine Qt-Screens. Erkannte Ausgaben (wlr-randr):\n\n" + "\n".join(f"  • {n}" for n in names) if names else "wlr-randr im Terminal ausführen."
        label = QLabel(text)
        label.setFont(QFont("Sans", 14))
        label.setWordWrap(True)
        layout.addWidget(label)
        win.resize(500, 300)
        win.show()
        return app.exec()

    for i, screen in enumerate(screens):
        name = screen.name() or f"Screen-{i}"
        geometry = screen.geometry()

        win = QWidget()
        win.setWindowTitle(f"Output: {name}")
        win.setScreen(screen)
        win.setGeometry(geometry)
        win.setWindowState(win.windowState() | Qt.WindowState.WindowFullScreen)

        layout = QVBoxLayout(win)
        label = QLabel(f"Name dieses Bildschirms:\n\n{name}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        font = QFont()
        font.setPointSize(max(14, min(72, geometry.width() // 15)))
        label.setFont(font)
        label.setStyleSheet(
            "QLabel { color: white; background: #1e293b; padding: 40px; border-radius: 12px; }"
        )
        layout.addWidget(label)

        info = f"Auflösung: {geometry.width()}×{geometry.height()}\n"
        if screen.model():
            info += f"Modell: {screen.model()}\n"
        if screen.manufacturer():
            info += f"Hersteller: {screen.manufacturer()}"
        info_label = QLabel(info)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { color: #94a3b8; font-size: 12px; }")
        layout.addWidget(info_label)

        win.showFullScreen()

    return app.exec()


def main_fallback():
    """Ohne PyQt6: nur wlr-randr ausgeben."""
    print("PyQt6 nicht installiert. Zeige wlr-randr Ausgabe:\n")
    names = get_output_names_wlr_randr()
    if names:
        print("Erkannte Ausgabenamen:")
        for n in names:
            print(f"  • {n}")
    subprocess.run(["wlr-randr"], timeout=5)
    return 0


if __name__ == "__main__":
    try:
        import PyQt6.QtWidgets  # noqa: F401
    except ImportError:
        sys.exit(main_fallback())
    sys.exit(main_qt())
