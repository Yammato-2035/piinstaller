# Backend Runtime Operator Handoff

Ziel: Privilegierte Diagnose und kontrollierter Service-Neustart im echten Operator-Terminal durchfuehren. Diese Schritte wurden vom Agenten **nicht** ausgefuehrt.

## Sicherheitsrahmen

- In einem echten lokalen Terminal mit TTY arbeiten.
- Vorher sicherstellen, dass die Session autorisiert ist.
- Schritte der Reihe nach ausfuehren und alle Ausgaben dokumentieren.

## Manuelle Operator-Kommandos (auszufuehren durch Operator)

```bash
set -euo pipefail
cd /home/volker/piinstaller

echo "=== OPERATOR CONTEXT ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
whoami
hostname

echo "=== SUDO PREAUTH ==="
sudo -v

echo "=== SERVICE STATUS (PRE) ==="
sudo systemctl status --no-pager setuphelfer-backend.service
sudo systemctl show setuphelfer-backend.service --no-pager -p ActiveState -p SubState -p MainPID -p ExecMainStatus -p NRestarts

echo "=== JOURNAL (PRE, LAST 200) ==="
sudo journalctl -u setuphelfer-backend.service -n 200 --no-pager

echo "=== OPTIONAL THREAD STACKS (PID FROM systemctl show) ==="
PID="$(sudo systemctl show setuphelfer-backend.service --no-pager -p MainPID --value)"
if [ -n "${PID}" ] && [ "${PID}" != "0" ]; then
  sudo cat "/proc/${PID}/stack" || true
  sudo ls -l "/proc/${PID}/fd" | sed -n '1,80p' || true
fi

echo "=== CONTROLLED RESTART ==="
sudo systemctl restart setuphelfer-backend.service
sleep 2

echo "=== SERVICE STATUS (POST) ==="
sudo systemctl is-active setuphelfer-backend.service
sudo systemctl status --no-pager setuphelfer-backend.service
sudo systemctl show setuphelfer-backend.service --no-pager -p ActiveState -p SubState -p MainPID -p ExecMainStatus -p NRestarts

echo "=== HTTP VALIDATION (POST) ==="
/usr/bin/time -f 'time_real=%e exit=%x' curl -v -m 5 http://127.0.0.1:8000/api/version
/usr/bin/time -f 'time_real=%e exit=%x' curl -v -m 5 http://127.0.0.1:8000/health
/usr/bin/time -f 'time_real=%e exit=%x' curl -v -m 5 http://127.0.0.1:8000/docs
/usr/bin/time -f 'time_real=%e exit=%x' curl -v -m 5 http://127.0.0.1:8000/openapi.json

echo "=== JOURNAL (POST, LAST 200) ==="
sudo journalctl -u setuphelfer-backend.service -n 200 --no-pager
```

## Erwartetes Ergebnis fuer Rueckgabe

- Vollstaendige Terminal-Ausgabe als Evidence.
- Klare Klassifikation:
  - `recovered_after_operator_restart`, oder
  - `still_hanging_after_operator_restart`, oder
  - `restart_failed_with_privileged_error`.
- Danach Prompt-Ingest: `BACKEND_RUNTIME_OPERATOR_RESTART_RESULT_INGEST`.
