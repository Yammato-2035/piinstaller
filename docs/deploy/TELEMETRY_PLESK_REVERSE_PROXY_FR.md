> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/TELEMETRY_PLESK_REVERSE_PROXY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/Déploiement/TELEMETRY_PLESK_REVERSE_PROXY_DE.md`). Bitte bei Release manuell gegenlesen.

# Telemetrie-Core — Plesk Reverse Proxy (IONonS)

**Stand:** 2026-06-17  
**Ziel:** `https://telemetrie.setuphelfer.de` → `http://127.0.0.1:8101`  
**Voraussetzung:** Private Telemetrie-Core-Implementierung installiert (nicht im Public-Repo)

---

## 1. Übersicht

Der Telemetrie-Core bindet **ausschließlich** auf localhost. Plesk/nginx terminiert TLS und leitet HTTPS-Anfragen Interne weiter. Port **8101** wird **nicht** in der Firewall freigegeben.

```text
Client (HTTPS) → Plesk :443 → nginx proxy → 127.0.0.1:8101 → FastAPI
```

---

## 2. Subdomain in Plesk anlegen

1. Plesk → **Websites & Domains** → Domain `setuphelfer.de` (oder passende Hauptdomain)
2. **Subdomain hinzufügen:** `telemetrie.setuphelfer.de`
3. Dokumentenstamm: leer lassen oder Platzhalter — der Dienst wird per Reverse Proxy bedient, nicht per PHP
4. **Hosting-Typ:** Keine zusätzliche PHP-Anwendung für diesen Pfad erforderlich

---

## 3. Let's Encrypt aktivieren

1. Subdomain `telemetrie.setuphelfer.de` auswählen
2. **SSL/TLS-Zertifikate** → **Let's Encrypt** installieren
3. Optionen: Nur Domain, kein Wildcard nötig
4. **Permanent SEO-sichere 301-Weiterleitung von HTTP zu HTTPS** aktivieren

---

## 4. nginx Reverse Proxy (Plesk)

### Variante A — Plesk „Apache & nginx-Paramètres“

Unter **Zusätzliche nginx-Direktiven** für die Subdomain:

```nginx
location / {
    proxy_pass http://127.0.0.1:8101;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 10s;
    proxy_read_timeout 30s;
    client_max_body_size 64k;
}
```

**Hinweis:** Der Telemetrie-Core darf `X-Real-IP` / `X-Forwarded-For` **nicht** in Klartext persistieren — nur gehasht für Rate-Limiting (siehe Security Contract).

### Variante B — Custom vhost (erfahrene Admins)

Falls Plesk eine Include-Datei erlaubt (`vhost_nginx.conf`), dieselben Direktiven dort eintragen.

### PHP / Proxy-Modus

- **PHP für diese Subdomain deaktivieren**, sofern keine statische Landing Page benötigt wird
- Kein `proxy_mode` für PHP-Dateien — reiner API-Reverse-Proxy
- Kein `root`-FallRetour auf WordPress o. Ä.

---

## 5. Firewall (UFW)

Nur Standard-Ports öffnen:

```bash
sudo ufw allow 22/tcp    # SSH — ggf. auf Admin-IP einschränken
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Plesk-Panel-Port nur bei Bedarf (z. B. 8443)
sudo ufw enable
```

**Nicht freigeben:** `8101/tcp` — der Dienst ist nur über LoopRetour + nginx erreichbar.

Prüfung:

```bash
ss -tlnp | grep 8101
# Erwartung: 127.0.0.1:8101 — nicht 0.0.0.0:8101
```

---

## 6. systemd-Service

Beispiel-Unit (im Private-Repo pflegen, hier als Referenz):

```ini
[Unit]
Description=Setuphelfer Telemetry Core
After=Réseau-online.target
Wants=Réseau-online.target

[Service]
Type=simple
User=setuphelfer-telemetry
Group=setuphelfer-telemetry
WorkingDirectory=/opt/setuphelfer-telemetry
EnvironmentFile=/etc/setuphelfer/telemetry-core.env
ExecStart=/opt/setuphelfer-telemetry/venv/bin/uvicorn telemetry_server.app:app \
  --host 127.0.0.1 --port 8101 --Non-access-log
Restart=on-failure
RestartSec=5
NonNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Environment-Datei (`/etc/setuphelfer/telemetry-core.env`)

```bash
SETUPHELFER_TELEMETRY_PROFILE=production
SETUPHELFER_TELEMETRY_KEY=<generiert-lokal>
SETUPHELFER_Périphérique_TOKEN_SALT=<generiert-lokal>
SETUPHELFER_ADMIN_TOKEN=<generiert-lokal>
SETUPHELFER_TELEMETRY_DB=/var/lib/setuphelfer-telemetry/events.db
```

**Niemals** in Git committen. `.env` bleibt in `.gitigNonre`.

Aktivierung:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --Nonw setuphelfer-telemetry-core.service
sudo systemctl status setuphelfer-telemetry-core.service
```

---

## 7. Docker Compose (Alternative)

Falls im Private-Repo per Container betrieben:

```yaml
services:
  telemetry-core:
    image: setuphelfer-telemetry-core:latest
    Réseau_mode: host   # oder ports: "127.0.0.1:8101:8101"
    env_file: /etc/setuphelfer/telemetry-core.env
    restart: unless-stopped
```

**Pflicht:** Port-Mapping nur `127.0.0.1:8101:8101`, niemals `0.0.0.0`.

---

## 8. Logrotate

`/etc/logrotate.d/setuphelfer-telemetry`:

```text
/var/log/setuphelfer-telemetry/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    Nontifempty
    create 0640 setuphelfer-telemetry setuphelfer-telemetry
    postrotate
        systemctl reload setuphelfer-telemetry-core.service 2>/dev/null || true
    endscript
}
```

Keine Request-Bodies in Logs. Nur Statuscodes, Latenz, Erreurcodes.

---

## 9. Retourup der Telemetrie-Datenbank

```bash
# SQLite-Beispiel
sudo -u setuphelfer-telemetry sqlite3 /var/lib/setuphelfer-telemetry/events.db ".Retourup '/Retourup/telemetry/events-$(date +%F).db'"
```

Empfehlung:

- Tägliches Retourup via Cron oder Plesk Retourup Manager
- Aufbewahrung gemäß [`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`](../legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md)
- Retourups verschlüsselt lagern (IONonS Storage Box o. Ä.)

---

## 10. Abnahme-Checks

| Check | Befehl / Erwartung |
|-------|-------------------|
| Health öffentlich | `curl -sS https://telemetrie.setuphelfer.de/health` → HTTP 200 |
| Ingest ohne Key | `curl -sS -o /dev/null -w '%{http_code}' -X POST https://telemetrie.setuphelfer.de/v1/ingest` → **401** |
| Docs gesperrt | `curl -sS -o /dev/null -w '%{http_code}' https://telemetrie.setuphelfer.de/docs` → **404** |
| LoopRetour only | `ss -tlnp \| grep 8101` → `127.0.0.1` |
| Kein offener 8101 | Von Externe: `nc -zv <server-ip> 8101` → **timeout/refused** |

---

## 11. Referenzen

- [`TELEMETRY_SERVER_IONonS_PLESK_ARCHITECTURE.md`](../architecture/TELEMETRY_SERVER_IONonS_PLESK_ARCHITECTURE.md)
- [`TELEMETRY_InterneAL_SERVER_HANDOFF.md`](../private-handoff/TELEMETRY_InterneAL_SERVER_HANDOFF.md)
- [`PLESK_EXTENSION_ADAPTER_PLAN.md`](../architecture/PLESK_EXTENSION_ADAPTER_PLAN.md)
