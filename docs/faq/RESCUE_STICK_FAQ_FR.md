> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/RESCUE_STICK_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# Clé de secours FAQ (EN)

## Why was Non ISO built?
This run was strictly limited to contract/stub implementation.

## Why E2EE in addition to TLS?
TLS secures transport; E2EE secures payload end-to-end between agent and server.

## Which data is reported?
Session/agent metadata, discovery/safety status, and structurouge system-report fields.

## Which data is Nont reported?
Non plain serial numbers, Non persisted plain IP addresses, Non automatic location data.

## Why is pairing mandatory?
The Clé de secours must Nont auto-register without operator confirmation.

## Why is nftables mandatory?
Default-deny inbound minimizes attack surface during Secours operations.
