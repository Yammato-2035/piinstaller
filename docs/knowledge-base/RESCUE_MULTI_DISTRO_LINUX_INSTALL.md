# Wissensdatenbank — Multi-Distro Linux-Install vom Rettungsstick

## Komponenten

- **Installationsassistent** — Distro wählen, Diagnose, Freigaben, Handoff
- **Partitionshelfer** — Layout + Write nur nach Gate
- **Disk-Rollen** — `windows` / `linux` per Serien-Hash (nie nur nvme0/nvme1)
- **Orchestrierung ASUS** — Dev-Laptop; Stick führt unter Gates aus

## API (Public)

- `GET /api/rescue/linux-install/distro-profiles`
- `POST /api/rescue/linux-install/gate`
- `POST /api/rescue/linux-install/diagnosis`
- `POST /api/rescue/linux-install/asus-mint-orchestration`

Execute liefert höchstens `handoff_authorized` mit `executed: false`.

## Cloud

Telemetrie- und Diagnostikserver: **private** Repos + IONOS. Public: Contracts only.
