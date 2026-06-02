# Rescue Devserver Discovery (Stub)

Status: **Design + Stub implementiert**.

## Reihenfolge

1. `setuphelfer.devserver=http://...` (Bootparameter)
2. Konfigurationswert
3. mDNS/DNS-SD `_setuphelfer-dev._tcp.local`
4. Optional UDP-Broadcast nur in `local_lab/dev`

## Sicherheitsregeln

- Keine Internet-/Cloud-Suche
- Release standardmäßig `disabled`, bis Rescue explizit aktiv
- Öffentliche Endpunkte ohne Freigabe blockiert
- Keine Secrets in Logs
- Ergebnis liefert nur Endpoint-Hash, nicht persistente Klartext-IP

## Discovery Result

- `discovery_status`: `found|not_found|blocked|disabled`
- `method`: `boot_param|config|mdns|udp_broadcast|none`
- `endpoint`, `endpoint_hash`, `warnings`, `errors`
