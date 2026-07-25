# PI-RS-INSTALL-ASSISTANT-001 — Zug A2 Distro-Profile + Mint ISO

## Distro-Registry

| Profile | Capability | P0 execute-prepared |
|---------|------------|---------------------|
| `linux_mint` | preview | ja |
| `ubuntu_server_lts` | preview | Stub |
| `ubuntu_server` | preview | Stub |
| `debian` | preview | Stub |

## ISO-Cache-Contract

- Root: `SETUP_LOGS/setuphelfer/iso-cache/<profile>/`
- SHA256 Pflicht für Status `valid`
- Fehlende ISO → Status `missing` (kein Crash)
- Falscher Hash → `corrupt`
- Kein automatischer Massen-Download ohne Operator-Start (`download_policy_gate`)

## API

- `GET /api/rescue/install-assistant/distro/profiles`
- `POST .../distro/iso-status|iso-verify|iso-check|download-policy`
