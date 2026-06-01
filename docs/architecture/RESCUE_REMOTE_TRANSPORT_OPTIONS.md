# Rescue Remote Transport Options

## A. HTTPS Pull-Agent (Phase-1-Entscheidung)

- Stick initiiert **ausgehend** HTTPS zum lokalen Development Server (`127.0.0.1` / QEMU `10.0.2.2:8001` via Proxy).
- Pairing-Token + Agent-ID.
- Jobqueue: `GET /jobs`, `POST /claim`, `POST /result`.
- Gut für NAT/LAN, kein eingehender Port am Stick.

## B. WireGuard Lab Tunnel (vorbereitet)

- Peer-Key pro Session.
- `AllowedIPs` nur Rescue-Agent.
- Später für Feld-Support.

## C. Restricted SSH Forced Command (nur Debug, nicht Standard)

- `authorized_keys` mit `command=`, `no-pty`, `no-port-forwarding`.
- Kein interaktives Login.

## Threat Model (Kurz)

| Bedrohung | Mitigation |
|-----------|------------|
| Öffentlicher Zugriff | API nur local_lab; kein Deploy ins Internet |
| Arbitrary commands | Kein `command_plan`; Runbook-Allowlist |
| Token-Leak | Redaction; keine Klartext-Speicherung |
| Replay | Job `expires_at`; Token-Laufzeit (später) |
| Unbefugter Server | Pairing + Server-Fingerprint (Konzept) |

## Audit

- JSONL: `build/runtime/rescue-remote/agents.jsonl`, `jobs.jsonl`.
- Keine Secrets in JSONL.
