# Rescue NFTables Policy (Preview-Validator)

Status: **Plan/Preview implementiert**, keine Regelanwendung in diesem Lauf.

## Pflichtregeln

- Inbound Default `drop`
- Loopback + `established,related` erlaubt
- DHCP/DNS erlaubt
- mDNS nur temporär in Discovery-Phase
- Outbound zum validierten Devserver erlaubt
- SSH/Remote-Support standardmäßig deaktiviert
- Firewall ist Pflicht (`mandatory=true`)

## Output

- `policy_status`: `ready|review_required|blocked`
- `apply_allowed=false` (in diesem Durchlauf zwingend)
