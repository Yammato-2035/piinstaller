# QEMU Guest Agent Smoke — Precheck

**Datum:** 2026-06-02

| Prüfpunkt | Ergebnis |
|-----------|----------|
| qemu-system-x86_64 | **yes** (8.2.2) |
| KVM vorhanden | **yes** (`/dev/kvm`, Gruppe `kvm`) |
| KVM nutzbar | **yes** |
| Projekt-QEMU-Skript | **yes** — `run-qemu-developer-iso-smoke.sh` |
| Operator-Guard-Skript | **yes** — `qemu-guest-agent-smoke-operator.sh` |
| Dev-Server-Proxy-Skript | **yes** — `start-qemu-lab-dev-server-proxy.sh` (Port 8001) |
| Host-Disk-Attach im Skript | **no** (nur `-cdrom`, `-snapshot`) |
| USB/dd im Skript | **no** |

## Bewertung

**Status: ok** (Tooling) — **blocked** für Agent-Ausführung wegen Profilwechsel (`sudo`).
