#!/usr/bin/env python3
"""Prüft, ob Qt und Qt Quick (QML) starten. Gibt jede Stufe aus und zeigt Fehler."""
import sys
import os

# Repo-Pfad für Imports
_DSI = os.path.dirname(os.path.abspath(__file__))
if _DSI not in sys.path:
    sys.path.insert(0, _DSI)

def step(name):
    print(f"  [{name}] ", end="", flush=True)

def ok():
    print("OK")
def fail(msg):
    print("FEHLER:", msg)
    sys.exit(1)

print("Qt / Qt Quick Check")
print("===================")

# 1) PyQt6 Core
step("PyQt6 import")
try:
    from PyQt6.QtCore import QCoreApplication, QUrl
    from PyQt6.QtGui import QGuiApplication
except Exception as e:
    fail(str(e))
ok()

# 2) QGuiApplication (Qt starten)
step("QGuiApplication")
try:
    app = QGuiApplication(sys.argv)
except Exception as e:
    fail(str(e))
ok()

# 3) QQmlApplicationEngine
step("QQmlApplicationEngine")
try:
    from PyQt6.QtQml import QQmlApplicationEngine
    engine = QQmlApplicationEngine()
except Exception as e:
    fail(str(e))
ok()

# 4) Minimales QML (nur QtQuick)
step("QML load (QtQuick)")
try:
    engine.loadData(b"import QtQuick\nItem { width: 1; height: 1 }", QUrl())
except Exception as e:
    fail(str(e))
if not engine.rootObjects():
    for err in engine.errors():
        print("    ", err.toString())
    fail("rootObjects() leer")
ok()

# 5) QtQuick.Controls + Window (wie in main.qml)
step("QtQuick.Controls + Window")
try:
    engine2 = QQmlApplicationEngine()
    # Minimales Fenster mit Controls – ohne Bridge
    engine2.loadData(
        b"""
        import QtQuick
        import QtQuick.Controls
        import QtQuick.Window
        Window { width: 200; height: 100; visible: false; title: "Test" }
        """.strip(),
        QUrl(),
    )
    if not engine2.rootObjects():
        for err in engine2.errors():
            print("   ", err.toString())
        fail("Window/Controls nicht geladen")
except Exception as e:
    fail(str(e))
ok()

print("")
print("Alles OK – Qt und Qt Quick sind nutzbar.")
print("Start: ./scripts/start-dsi-radio-qml.sh")
