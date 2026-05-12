# Zielsystem prüfen (Phase F)

Nach Installation oder Update soll das System **ohne Raten** prüfbar sein: Dienste laufen, API antwortet, Logs lesbar.

## Schnellcheck (Skript)

Im geklonten Repository oder mit kopiertem Skript auf dem Raspberry Pi:

```bash
./scripts/verify-setuphelfer-install.sh
```

- Prüft **systemd**: `setuphelfer-backend.service` und `setuphelfer.service` (falls Units vorhanden); sonst **Legacy** `pi-installer-backend` / `pi-installer`.
- Prüft per **curl**: `http://127.0.0.1:8000/api/version` (HTTP 200 erwartet).
- Prüft die **Web-UI** auf Port **3001** (Warnung, wenn nicht 200 – z. B. nur Backend aktiv).
- Zeigt die letzten Zeilen aus **journalctl** für die Backend-Unit (ohne sudo, soweit erlaubt).

Ohne Journal-Ausgabe:

```bash
./scripts/verify-setuphelfer-install.sh --no-journal
```

Andere Ports/Hosts:

```bash
VERIFY_BACKEND_URL=http://192.168.1.10:8000 VERIFY_FRONTEND_URL=http://192.168.1.10:3001 ./scripts/verify-setuphelfer-install.sh
```

**Exit-Code:** `0` wenn systemd-Backend (falls vorhanden) aktiv ist und die API HTTP 200 liefert; sonst `1`.

## Manuell (Referenz)

```bash
systemctl status setuphelfer-backend setuphelfer --no-pager
curl -sS http://127.0.0.1:8000/api/version
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3001/
journalctl -u setuphelfer-backend -n 40 --no-pager
```

Siehe auch: `docs/BETRIEB_REPO_VS_SERVICE.md`, `docs/architecture/NAMING_AND_SERVICES.md`.
