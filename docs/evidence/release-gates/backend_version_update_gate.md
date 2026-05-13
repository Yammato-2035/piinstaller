# Evidence — Backend version update gate

**JSON:** [`backend_version_update_gate.json`](./backend_version_update_gate.json)

**Summary:** Process rule and read-only script enforce a green runtime (`/api/version`, `config/version.json`, systemd) before backup/restore/hardware tests.

**Related:** [`backend_version_gate_2026-05-13.md`](./backend_version_gate_2026-05-13.md), [`apt_update_delivery_gap.json`](./apt_update_delivery_gap.json).
