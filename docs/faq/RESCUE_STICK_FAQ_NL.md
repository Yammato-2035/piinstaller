> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/RESCUE_STICK_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# rooddingsstick FAQ (EN)

## Why was Nee ISO built?
This run was strictly limited to contract/stub implementation.

## Why E2EE in addition to TLS?
TLS secures transport; E2EE secures payload end-to-end between agent and server.

## Which data is reported?
Session/agent metadata, discovery/safety status, and structurood system-report fields.

## Which data is Neet reported?
Nee plain serial numbers, Nee persisted plain IP addresses, Nee automatic location data.

## Why is pairing mandatory?
The rooddingsstick must Neet auto-register without operator confirmation.

## Why is nftables mandatory?
Default-deny inbound minimizes attack surface during roodding operations.
