# Backend Recovery After DCC Deploy — Result

**Datum:** 2026-06-03  
**HEAD:** `a5d57ed`

## Ursache Backend-Ausfall nach Deploy

**`daemon_reload_required`:** Deploy schrieb systemd-Unit-Dateien und startete Services, ohne zuvor `systemctl daemon-reload`. Kurz danach war Port 8000 nicht erreichbar (`curl: (7)`). systemd warnte explizit auf geänderte Unit-Dateien.

## Recovery

| Aussage | Wert |
|---------|------|
| Backend recovered | **yes** (Operator; API 200) |
| DCC-Fix live in `/opt` | **yes** |
| `/api/dev-dashboard/recent-evidence` live | **yes** (HTTP 200, local_lab) |
| Default 5 + Filter | **yes** |
| Juni-2026-Berichte oben | **yes** |
| 30.05. nicht oben in recent_reports | **yes** |
| release restored (Agent) | **no** — Operator-Trap ausstehend |
| QEMU | **no** |

## Nächster Schritt

1. Operator: `sudo systemctl daemon-reload` (Warnung beseitigen)
2. Operator: Release-Restart bestätigen (`install-profile.conf` = release)
3. **QEMU Guest Agent Smoke** wenn gewünscht
