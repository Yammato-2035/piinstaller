#!/bin/bash
#
# PI-Installer: NVMe Hardware-Ketten-Diagnose (Pi 5)
# Fokus:
# - PCIe/NVMe-Erkennung auf Bus-Ebene
# - Treiberzustand (nvme/nvme_core)
# - Relevante Kernel-Logs ohne dmesg-Zugriff (journalctl -k)
# - Basis-Indikatoren für Strom-/Unterspannungsprobleme
#

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

OK="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"
WARN="${YELLOW}!${NC}"
INFO="${BLUE}i${NC}"

echo -e "${CYAN}=== NVMe Hardware-Kette Diagnose ===${NC}"
echo ""

echo -e "${CYAN}[1] System-Basis${NC}"
if [[ -f /proc/device-tree/model ]]; then
  model=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || true)
  echo "  Modell: ${model:-?}"
else
  echo -e "  $WARN /proc/device-tree/model nicht verfügbar."
fi

kernel=$(uname -r 2>/dev/null || true)
echo "  Kernel: ${kernel:-?}"
echo ""

echo -e "${CYAN}[2] PCIe-Bus / NVMe-Controller${NC}"
if command -v lspci >/dev/null 2>&1; then
  pcie_lines=$(lspci -nn 2>/dev/null | awk '
    /PCI bridge/ || /Non-Volatile memory controller/ || /NVMe/ || /BCM2712 PCIe Bridge/ {print}
  ')
  if [[ -n "${pcie_lines:-}" ]]; then
    echo "$pcie_lines" | while IFS= read -r line; do
      if echo "$line" | grep -Eqi "Non-Volatile memory controller|NVMe"; then
        echo -e "  $OK $line"
      else
        echo "  $line"
      fi
    done
  else
    echo -e "  $WARN Keine relevanten PCIe-/NVMe-Zeilen gefunden."
  fi

  nvme_ctrl_count=$(lspci -nn 2>/dev/null | awk '
    /Non-Volatile memory controller/ || /NVMe/ {c++} END {print c+0}
  ')
  if [[ "$nvme_ctrl_count" -gt 0 ]]; then
    echo -e "  $OK NVMe-Controller auf PCIe gefunden: $nvme_ctrl_count"
  else
    echo -e "  $FAIL Kein NVMe-Controller auf PCIe gefunden."
  fi
else
  echo -e "  $FAIL lspci nicht verfügbar."
fi
echo ""

echo -e "${CYAN}[3] PCIe-Linkstatus Root-Port${NC}"
if command -v lspci >/dev/null 2>&1; then
  root_port=$(lspci -D | awk '/Broadcom.*BCM2712 PCIe Bridge/ {print $1; exit}')
  if [[ -n "${root_port:-}" ]]; then
    lnkcap=$(lspci -vv -s "$root_port" 2>/dev/null | awk '/LnkCap:/{print; exit}')
    lnksta=$(lspci -vv -s "$root_port" 2>/dev/null | awk '/LnkSta:/{print; exit}')
    lnkctl2=$(lspci -vv -s "$root_port" 2>/dev/null | awk '/LnkCtl2:/{print; exit}')
    echo "  Root-Port: $root_port"
    [[ -n "${lnkcap:-}" ]] && echo "  $lnkcap"
    [[ -n "${lnksta:-}" ]] && echo "  $lnksta"
    [[ -n "${lnkctl2:-}" ]] && echo "  $lnkctl2"
  else
    echo -e "  $WARN BCM2712 Root-Port nicht gefunden."
  fi
else
  echo -e "  $WARN lspci nicht verfügbar."
fi
echo ""

echo -e "${CYAN}[4] NVMe-Blockgeräte und Treiber${NC}"
nvme_nodes=$(ls /dev/nvme* 2>/dev/null || true)
if [[ -n "${nvme_nodes:-}" ]]; then
  echo -e "  $OK Geräte unter /dev:"
  echo "$nvme_nodes" | while IFS= read -r n; do
    echo "    $n"
  done
else
  echo -e "  $FAIL Keine /dev/nvme* Geräte vorhanden."
fi

nvme_mod_loaded="no"
if lsmod 2>/dev/null | awk '{print $1}' | grep -qx "nvme"; then
  nvme_mod_loaded="yes"
  echo -e "  $OK Kernelmodul 'nvme' geladen."
elif [[ -d /sys/module/nvme ]]; then
  nvme_mod_loaded="yes"
  echo -e "  $OK 'nvme' ist im Kernel vorhanden (built-in oder bereits aktiv)."
else
  echo -e "  $WARN Kernelmodul 'nvme' nicht geladen."
fi

if lsmod 2>/dev/null | awk '{print $1}' | grep -qx "nvme_core"; then
  echo -e "  $OK Kernelmodul 'nvme_core' geladen."
elif [[ -d /sys/module/nvme_core ]]; then
  echo -e "  $OK 'nvme_core' ist im Kernel vorhanden (built-in oder bereits aktiv)."
else
  echo -e "  $WARN Kernelmodul 'nvme_core' nicht geladen."
fi

if [[ "$nvme_mod_loaded" == "no" ]]; then
  echo -e "  $INFO Testweise laden (manuell): sudo modprobe nvme"
fi
echo ""

echo -e "${CYAN}[5] Kernel-Logs (journalctl -k, letzte 200 Zeilen)${NC}"
if command -v journalctl >/dev/null 2>&1; then
  # Nutzt journalctl statt dmesg, falls dmesg-Lesen gesperrt ist.
  log_hits=$(journalctl -k -n 200 --no-pager 2>/dev/null | grep -Ei "nvme|pcie|aer|link down|link up|timeout|reset|undervoltage" || true)
  if [[ -n "${log_hits:-}" ]]; then
    echo "$log_hits" | tail -n 40 | while IFS= read -r line; do
      echo "  $line"
    done
  else
    echo -e "  $WARN Keine passenden Kernel-Log-Zeilen gefunden."
  fi

  bus_assign_issue=$(journalctl -k -n 500 --no-pager 2>/dev/null | grep -E "cannot be assigned for them|bridge has subordinate" || true)
  if [[ -n "${bus_assign_issue:-}" ]]; then
    echo ""
    echo -e "  $WARN Hinweis: Möglicher PCIe-Busnummern-/Bridge-Adressierungsengpass erkannt:"
    echo "$bus_assign_issue" | tail -n 4 | while IFS= read -r line; do
      echo "    $line"
    done
  fi
else
  echo -e "  $WARN journalctl nicht verfügbar."
fi
echo ""

echo -e "${CYAN}[6] Strom/Unterspannung (wenn verfügbar)${NC}"
if command -v vcgencmd >/dev/null 2>&1; then
  throttled=$(vcgencmd get_throttled 2>/dev/null || true)
  if [[ -n "${throttled:-}" ]]; then
    echo "  get_throttled: $throttled"
    if echo "$throttled" | grep -q "0x0"; then
      echo -e "  $OK Keine Unterspannungs-/Throttle-Flags aktiv."
    else
      echo -e "  $WARN Es sind Throttle/Unterspannungs-Bits gesetzt."
    fi
  else
    echo -e "  $WARN vcgencmd get_throttled lieferte keine Daten."
  fi
else
  echo -e "  $WARN vcgencmd nicht verfügbar."
fi
echo ""

echo -e "${CYAN}[7] Handlungsempfehlung${NC}"
if [[ -z "${nvme_nodes:-}" ]]; then
  echo "  1) Physik prüfen: NVMe richtig im Adapter, Adapter korrekt auf Pi-5 PCIe, ggf. neu stecken."
  echo "  2) Strom prüfen: Netzteil min. 5V/5A, keine schwachen USB-C-Kabel."
  echo "  3) Neustart nach Kaltstart testen: sudo poweroff; 10s warten; wieder einschalten."
  echo "  4) Wenn weiterhin kein NVMe-Controller in lspci erscheint: Adapter/NVMe an anderem System gegenprüfen."
else
  echo "  NVMe-Hardware wird erkannt. Nächster Fokus: Partitionierung/Boot-Konfiguration."
fi
echo ""

echo -e "${CYAN}=== Ende Diagnose ===${NC}"
