#!/bin/bash
# Qt Creator mit QML-Import-Pfad starten, damit "import QtQuick" u. a. gefunden werden.
# Nutzung: ./start-qtcreator-for-qml.sh
# Optional: ./start-qtcreator-for-qml.sh /pfad/zu/main.qml

QML_PATH="/usr/lib/x86_64-linux-gnu/qt6/qml"
export QML2_IMPORT_PATH="$QML_PATH"
export QT_QML_IMPORT_PATH="$QML_PATH"

# Falls Qt Creator die Module über Plugin-Pfad sucht:
export QT_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins"

exec qtcreator "$@"
