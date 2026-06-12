# webserver_status Network Migration — G.3

**Route:** `GET /api/webserver/status` · **Feld:** `network` in Response

## Änderung

| Vorher | Nachher |
|--------|---------|
| `get_network_info()` | `build_network_info()` |

## Response

`network`-Block und abgeleitete `pi_installer.url` unverändert.
