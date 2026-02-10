#!/bin/bash
# PI-Installer: AnyDesk doppeltes Icon / Flackern beheben
#
# Zwei AnyDesk-Icons in der Taskleiste (Flackern) entstehen oft durch zwei laufende
# AnyDesk-Instanzen (z. B. Autostart + manueller Start). Dieses Script beendet alle
# AnyDesk-Prozesse und startet genau eine Instanz neu.
# Sollte das Flackern bleiben: AnyDesk deinstallieren (--uninstall).
#
# --check: Prüft, ob AnyDesk doppelt gestartet wird (laufende Prozesse + Autostart-Einträge).
#
# Als Benutzer ausführen (nicht sudo): ./scripts/fix-anydesk-double-icon.sh
# Prüfen: ./scripts/fix-anydesk-double-icon.sh --check
# Deinstallieren: sudo ./scripts/fix-anydesk-double-icon.sh --uninstall

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

UNINSTALL=""
CHECK=""
[ "${1:-}" = "--uninstall" ] && UNINSTALL="yes"
[ "${1:-}" = "--check" ] && CHECK="yes"

if [ -n "$CHECK" ]; then
  echo -e "${CYAN}Prüfung: Wird AnyDesk doppelt gestartet?${NC}"
  echo ""
  # Laufende AnyDesk-Prozesse
  N=$(pgrep -x anydesk 2>/dev/null | wc -l)
  echo -e "${CYAN}[1] Laufende AnyDesk-Prozesse:${NC} $N"
  if [ "$N" -gt 0 ]; then
    pgrep -a -x anydesk 2>/dev/null | while read -r line; do echo "    $line"; done
    if [ "$N" -gt 1 ]; then
      echo -e "    ${YELLOW}→ Mehr als eine Instanz läuft (kann zwei Icons / Flackern verursachen).${NC}"
    fi
  else
    echo "    Keine AnyDesk-Prozesse gefunden."
  fi
  echo ""
  # Autostart-Einträge (Benutzer + System)
  echo -e "${CYAN}[2] Autostart-Einträge für AnyDesk:${NC}"
  FOUND=""
  for dir in "${XDG_CONFIG_HOME:-$HOME/.config}/autostart" /etc/xdg/autostart; do
    [ -d "$dir" ] || continue
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      echo "    $f"
      FOUND="yes"
      grep -E '^Exec=|^Hidden=|^X-GNOME-Autostart-enabled=' "$f" 2>/dev/null | sed 's/^/      /'
    done < <(find "$dir" -maxdepth 1 -type f 2>/dev/null | grep -i anydesk || true)
  done
  [ -n "$FOUND" ] || echo "    Keine AnyDesk-Autostart-Dateien gefunden."
  echo ""
  # Systemd user service
  echo -e "${CYAN}[3] Systemd User-Service (AnyDesk):${NC}"
  if systemctl --user list-unit-files 2>/dev/null | grep -qi anydesk; then
    systemctl --user list-unit-files 2>/dev/null | grep -i anydesk | sed 's/^/    /'
  else
    echo "    Kein AnyDesk User-Service."
  fi
  echo ""
  echo -e "${GREEN}Prüfung fertig.${NC} Bei mehr als einem Prozess oder mehreren Autostart-Einträgen: $0 (ohne --check) ausführen."
  exit 0
fi

if [ -n "$UNINSTALL" ]; then
  if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}Bitte mit sudo ausführen: sudo $0 --uninstall${NC}"
    exit 1
  fi
  echo -e "${CYAN}AnyDesk deinstallieren${NC}"
  apt-get remove -y anydesk 2>/dev/null || apt-get remove -y anydesk-* 2>/dev/null || true
  echo -e "${GREEN}AnyDesk wurde deinstalliert.${NC}"
  exit 0
fi

echo -e "${CYAN}AnyDesk doppeltes Icon / Flackern beheben${NC}"
echo ""

# Alle AnyDesk-Prozesse beenden (behebt zwei Icons / Flackern)
if pgrep -x anydesk >/dev/null 2>&1; then
  echo -e "${CYAN}Beende alle AnyDesk-Instanzen …${NC}"
  pkill -x anydesk 2>/dev/null || killall anydesk 2>/dev/null || true
  sleep 2
  # Falls noch Prozesse laufen (z. B. anydesk --service)
  pkill -x anydesk 2>/dev/null || true
  sleep 1
  echo -e "${GREEN}AnyDesk-Instanzen beendet.${NC}"
else
  echo -e "${YELLOW}Keine laufende AnyDesk-Instanz gefunden.${NC}"
fi

# Eine Instanz starten (damit nur ein Icon in der Taskleiste erscheint)
if command -v anydesk >/dev/null 2>&1; then
  echo -e "${CYAN}Starte eine AnyDesk-Instanz …${NC}"
  export DISPLAY="${DISPLAY:-:0}"
  anydesk &
  sleep 1
  echo -e "${GREEN}Fertig. Es sollte nur noch ein AnyDesk-Icon sichtbar sein.${NC}"
else
  echo -e "${YELLOW}AnyDesk nicht gefunden (nicht installiert?).${NC}"
fi

echo ""
echo -e "${YELLOW}Falls das Flackern bleibt: AnyDesk deinstallieren mit${NC}"
echo -e "  ${CYAN}sudo $0 --uninstall${NC}"
echo ""
