# Minimales CMake-Projekt für Qt Creator (nichts wird gebaut).
# WICHTIG: Projekt als CMake öffnen (CMakeLists.txt), Kit = Qt aus ~/Qt (Online-Installer).
# Dann nutzt Qt Creator automatisch den QML-Pfad der Kit-Qt (z. B. ~/Qt/6.10.2/gcc_64/qml).
# Kein QML_IMPORT_PATH hier – sonst wird die Kit-Qt überschrieben und Imports gehen kaputt.
cmake_minimum_required(VERSION 3.16)
project(SabrinaTunerQML NONE)
