#!/bin/bash
# PI-Installer – Diagnose: Grafische Oberfläche / Boot in Desktop
# Führt alle relevanten Prüfungen auf der Konsole aus.
# Ohne sudo ausführbar (einige Einträge ggf. „Permission denied“).
#
# Optionen:
#   --revert-lightdm-override
#     Entfernt lightdm.service.d/wait-for-drm.conf, lädt systemd neu. (sudo)
#   --fix-desktop-boot [B3|B4]
#     B3 = Desktop mit Login | B4 = Desktop mit Autologin (Standard).
#     Setzt Boot via raspi-config nonint + graphical.target. (sudo)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cmdline_locations=("/boot/firmware/cmdline.txt" "/boot/cmdline.txt")
override_dirs=(
  "/etc/systemd/system/default.target.d"
  "/etc/systemd/system/getty@tty1.service.d"
  "/etc/systemd/system/autologin@.service.d"
  "/etc/systemd/system/lightdm.service.d"
)

# --- Revert LightDM-Override (optional) ---
if [ "${1:-}" = "--revert-lightdm-override" ]; then
  echo "Entferne LightDM-Override (wait-for-drm) und setze auf Standard zurück..."
  if [ "$(id -u)" -ne 0 ]; then
    echo "Bitte mit sudo ausführen: sudo $0 --revert-lightdm-override"
    exit 1
  fi
  rm -f /etc/systemd/system/lightdm.service.d/wait-for-drm.conf
  rmdir /etc/systemd/system/lightdm.service.d 2>/dev/null || true
  systemctl daemon-reload
  echo "Erledigt. Optional: sudo reboot"
  exit 0
fi

# --- Fix Desktop-Boot via raspi-config (optional) ---
if [ "${1:-}" = "--fix-desktop-boot" ]; then
  mode="${2:-B4}"
  case "$mode" in B3|B4) ;; *) mode=B4;; esac
  echo "Setze Boot auf Desktop via raspi-config nonint (do_boot_behaviour $mode)..."
  if [ "$(id -u)" -ne 0 ]; then
    echo "Bitte mit sudo ausführen: sudo $0 --fix-desktop-boot [B3|B4]"
    exit 1
  fi
  if ! command -v raspi-config &>/dev/null; then
    echo "raspi-config nicht gefunden. Nur systemd-Boot-Ziel wird gesetzt."
  else
    raspi-config nonint do_boot_behaviour "$mode" || true
  fi
  systemctl set-default graphical.target
  systemctl daemon-reload
  echo "Erledigt. Bitte neu starten: sudo reboot"
  echo "  B3 = Desktop mit Login | B4 = Desktop mit Autologin"
  exit 0
fi

echo "=============================================="
echo "  Diagnose: Grafischer Boot / Desktop-Start"
echo "=============================================="
echo ""

# --- 1. Default-Target ---
echo -e "${CYAN}[1] Default-Boot-Target${NC}"
def=$(systemctl get-default 2>/dev/null || echo "?")
if [ "$def" = "graphical.target" ]; then
  echo -e "    Default: ${GREEN}graphical.target${NC} (erwartet für Desktop)"
else
  echo -e "    Default: ${YELLOW}${def}${NC} (für Desktop: graphical.target)"
fi
echo ""

# --- 2. Symlink default.target ---
echo -e "${CYAN}[2] Symlink default.target${NC}"
if [ -L /etc/systemd/system/default.target ]; then
  dest=$(readlink -f /etc/systemd/system/default.target 2>/dev/null || readlink /etc/systemd/system/default.target)
  echo "    $(ls -la /etc/systemd/system/default.target)"
  if [[ "$dest" == *graphical* ]]; then
    echo -e "    ${GREEN}→ zeigt auf graphical.target${NC}"
  else
    echo -e "    ${YELLOW}→ zeigt nicht auf graphical.target${NC}"
  fi
else
  echo -e "    ${RED}Kein Symlink oder nicht gefunden.${NC}"
fi
echo ""

# --- 3. Kernel-Cmdline (systemd.unit) ---
echo -e "${CYAN}[3] Kernel-Cmdline (systemd.unit)${NC}"
found_cmdline=""
for f in "${cmdline_locations[@]}"; do
  if [ -r "$f" ]; then
    found_cmdline="$f"
    echo "    Datei: $f"
    line=$(cat "$f" 2>/dev/null || sudo cat "$f" 2>/dev/null || true)
    echo "    Inhalt: ${line:0:120}..."
    if echo "$line" | grep -qE 'systemd\.unit=(multi-user|rescue)'; then
      echo -e "    ${RED}⚠ Enthält systemd.unit=... → überschreibt Default-Target (Konsole)!${NC}"
    else
      echo -e "    ${GREEN}Kein systemd.unit=multi-user o.ä. gefunden.${NC}"
    fi
    break
  fi
done
if [ -z "$found_cmdline" ]; then
  echo -e "    ${YELLOW}Weder /boot/firmware/cmdline.txt noch /boot/cmdline.txt lesbar.${NC}"
fi
echo ""

# --- 4. Overrides ---
echo -e "${CYAN}[4] Systemd-Overrides${NC}"
for d in "${override_dirs[@]}"; do
  if [ -d "$d" ]; then
    echo "    $d:"
    ls -la "$d" 2>/dev/null | sed 's/^/      /' || true
    for f in "$d"/*.conf; do
      [ -f "$f" ] || continue
      echo "      --- $f ---"
      cat "$f" 2>/dev/null | sed 's/^/        /' || true
    done
  else
    echo "    $d: (nicht vorhanden)"
  fi
done
echo ""

# --- 5. LightDM / Display-Manager ---
echo -e "${CYAN}[5] LightDM / Display-Manager${NC}"
echo -n "    lightdm enabled: "
systemctl is-enabled lightdm 2>/dev/null || echo "?"
echo -n "    graphical.target enabled: "
systemctl is-enabled graphical.target 2>/dev/null || echo "?"
echo "    lightdm status:"
systemctl status lightdm --no-pager 2>/dev/null | sed 's/^/      /' || echo "      (nicht lesbar)"
if [ -e /etc/systemd/system/display-manager.service ]; then
  echo "    display-manager.service:"
  cat /etc/systemd/system/display-manager.service 2>/dev/null | sed 's/^/      /' || true
fi
echo ""

# --- 6. LightDM Journal (dieser Boot) ---
echo -e "${CYAN}[6] LightDM Log (dieser Boot) – letzte 35 Zeilen${NC}"
journalctl -u lightdm -b --no-pager -n 35 2>/dev/null | sed 's/^/    /' || echo "    (journalctl nicht verfügbar oder kein Eintrag)"
echo ""

# --- 7. Plymouth ---
echo -e "${CYAN}[7] Plymouth (Boot-Splash)${NC}"
v=$(systemctl is-active plymouth 2>/dev/null) || v=""
[ "$v" = "active" ] && echo "    plymouth: active" || echo "    plymouth: inactive oder nicht installiert"
echo ""

# --- 8. getty@tty1 (Konsole auf Hauptdisplay) ---
echo -e "${CYAN}[8] getty@tty1 (Konsole auf Hauptdisplay)${NC}"
v=$(systemctl is-active getty@tty1 2>/dev/null) || v=""
echo "    getty@tty1: ${v:-?}"
echo -n "    enabled: "
systemctl is-enabled getty@tty1 2>/dev/null || echo "?"
if [ -d /etc/systemd/system/getty@tty1.service.d ]; then
  echo "    Overrides:"
  ls -la /etc/systemd/system/getty@tty1.service.d/ 2>/dev/null | sed 's/^/      /' || true
  for f in /etc/systemd/system/getty@tty1.service.d/*.conf; do
    [ -f "$f" ] || continue
    echo "      --- $(basename "$f") ---"
    grep -vE '^[[:space:]]*#' "$f" 2>/dev/null | sed 's/^/        /' || true
  done
fi
echo ""

# --- 9. raspi-config Boot-Verhalten ---
echo -e "${CYAN}[9] raspi-config Boot / Autologin${NC}"
if command -v raspi-config &>/dev/null; then
  cli=$(raspi-config nonint get_boot_cli 2>/dev/null || true)
  alog=$(raspi-config nonint get_autologin 2>/dev/null || true)
  echo "    get_boot_cli: ${cli:-?}  (0=Desktop, 1=Konsole)"
  echo "    get_autologin: ${alog:-?}  (0=Login, 1=Autologin)"
  if [ "${cli:-}" = "1" ]; then
    echo -e "    ${RED}→ raspi-config steht auf KONSOLE, obwohl graphical.target gesetzt ist.${NC}"
    echo -e "    ${YELLOW}→ Fix: sudo $0 --fix-desktop-boot [B3|B4]${NC}"
  fi
else
  echo "    raspi-config nicht installiert"
fi
echo ""

# --- 10. VT-Hinweis ---
echo -e "${CYAN}[10] Hinweis: Virtuelle Terminals (VT)${NC}"
echo "    Bildschirm zeigt oft tty1 (Konsole). LightDM läuft ggf. auf tty7."
echo "    Nach dem Boot probieren: ${GREEN}Ctrl+Alt+F7${NC} bzw. ${GREEN}Ctrl+Alt+F8${NC}"
echo "    → Wechselt zum grafischen Login/Desktop, falls dieser dort läuft."
echo ""

echo "=============================================="
echo "  Ende Diagnose"
echo "=============================================="
echo ""
echo "Mögliche Aktionen:"
echo "  LightDM-Override zurücksetzen:  sudo $0 --revert-lightdm-override"
echo "  Boot auf Desktop erzwingen:     sudo $0 --fix-desktop-boot [B3|B4]"
echo "    B3 = Desktop mit Login | B4 = Desktop mit Autologin (Standard)"
echo ""
