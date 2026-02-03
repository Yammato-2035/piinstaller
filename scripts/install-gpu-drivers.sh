#!/bin/bash
# Installiert die für die erkannte Hardware passenden NVIDIA- und AMD-Treiber.
# Erkannt auf diesem System: NVIDIA GeForce RTX 4070 Max-Q/Mobile, AMD Raphael (iGPU).
# Für Linux Mint 22.1 / Ubuntu 24.04.
# Ausführen: ./scripts/install-gpu-drivers.sh  (mit sudo-Rechten oder nach Aufforderung)

set -e

echo "=== GPU-Treiber Installation (NVIDIA + AMD) ==="
echo ""

# 1) Empfohlene Treiber anzeigen
if command -v ubuntu-drivers &>/dev/null; then
  echo "Empfohlene Treiber für Ihre Hardware:"
  ubuntu-drivers devices
  echo ""
fi

# 2) Paketlisten aktualisieren
echo "Aktualisiere Paketlisten..."
sudo apt-get update -qq

# 3) NVIDIA: empfohlener Treiber (für RTX 4070 z.B. nvidia-driver-590-open)
echo ""
echo "Installiere empfohlenen NVIDIA-Treiber (ubuntu-drivers autoinstall)..."
sudo ubuntu-drivers autoinstall

# Alternativ nur den empfohlenen installieren (falls autoinstall nicht gewünscht):
# RECOMMENDED=$(ubuntu-drivers list 2>/dev/null | grep recommended | head -1)
# if [ -n "$RECOMMENDED" ]; then
#   sudo apt-get install -y "$RECOMMENDED"
# fi

# 4) AMD: amdgpu ist im Kernel; Firmware und X-Treiber sicherstellen
echo ""
echo "Stelle AMD-Treiber (amdgpu) und Firmware sicher..."
sudo apt-get install -y --no-install-recommends \
  linux-firmware \
  xserver-xorg-video-amdgpu \
  libdrm-amdgpu1

echo ""
echo "=== Installation abgeschlossen. ==="
echo "Bei NVIDIA: Neustart empfohlen (sudo reboot), damit der neue Treiber aktiv wird."
echo "AMD amdgpu läuft über den Kernel und ist in der Regel bereits aktiv."
