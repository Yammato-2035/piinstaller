# Rescue Stick FAQ (EN)

## Why was no ISO built?
This run was strictly limited to contract/stub implementation.

## Why E2EE in addition to TLS?
TLS secures transport; E2EE secures payload end-to-end between agent and server.

## Which data is reported?
Session/agent metadata, discovery/safety status, and structured system-report fields.

## Which data is not reported?
No plain serial numbers, no persisted plain IP addresses, no automatic location data.

## Why is pairing mandatory?
The rescue stick must not auto-register without operator confirmation.

## Why is nftables mandatory?
Default-deny inbound minimizes attack surface during rescue operations.
