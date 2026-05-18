# Web-UI-Runtime: `setuphelfer.service`

Betriebsdokumentation für die produktive Weboberfläche (Vite **preview** auf `frontend/dist/`).

**Evidence (Reparatur 2026-05-18):** `docs/evidence/runtime-results/setuphelfer_web_ui_runtime_repair_2026-05-18.json`  
**Fix-Commit:** `0a1e4a0` — *Keep production web UI preview running in foreground*

---

## Zweck und Abgrenzung

| Unit | Rolle | Port (Standard) |
|------|--------|-----------------|
| **`setuphelfer-backend.service`** | API (Uvicorn), alleiniger Owner von Port **8000** | `127.0.0.1:8000` |
| **`setuphelfer.service`** | Nur **Web-UI**: `scripts/start-browser-production.sh` → **`exec npm run preview`** | `127.0.0.1:3001` |

Die Web-UI startet **kein** zweites Backend. `Requires=setuphelfer-backend.service` — ohne erreichbares `/api/version` bricht das Startskript mit Exit **1** ab.

Repo-Entwicklung: `./start.sh` / Vite **dev** (Proxy). Produktion unter `/opt`: **nicht** parallel zu aktiven Services nutzen (siehe `docs/BETRIEB_REPO_VS_SERVICE.md`).

---

## Erwarteter Laufzeitpfad

1. Backend aktiv, `curl http://127.0.0.1:8000/api/version` → `status: success`
2. `setuphelfer.service` **active (running)**
3. Listener `127.0.0.1:3001`
4. `curl -I http://127.0.0.1:3001` → **HTTP 200**
5. UI nutzt API-Basis **`http://127.0.0.1:8000`** (Release-Build, kein Same-Origin-Proxy auf :3001)

---

## Diagnosebefehle

```bash
systemctl is-active setuphelfer.service setuphelfer-backend.service
systemctl status setuphelfer.service --no-pager -n 80
journalctl -u setuphelfer.service -n 80 --no-pager   # ggf. sudo

ss -ltnp | grep ':3001' || true
curl -I http://127.0.0.1:3001
curl -s http://127.0.0.1:8000/api/version

./scripts/check-runtime-deploy-gate.sh
```

---

## Fehlerbild: `inactive (dead)` mit Exit 0/SUCCESS

**Symptom:** `systemctl status setuphelfer.service` zeigt `inactive (dead)`, `code=exited, status=0/SUCCESS`. Port **3001** geschlossen, Browser: *connection refused*.

**Ursache (behoben in `0a1e4a0`):** `start-browser-production.sh` startete **`npm run preview &`** im Hintergrund und wartete mit **`wait`**. Unter systemd **`Type=simple`** war die **Shell** der Hauptprozess — nicht Vite. Beendete sich die Shell (Kindprozess weg, Signal-Handler), meldete systemd **SUCCESS** → **kein** dauerhafter Listener auf 3001.

**Korrektur:** Vite Preview im **Vordergrund** per **`exec`**:

```bash
exec npm run preview -- --host 127.0.0.1 --port 3001 --strictPort
```

- Kein `&`, kein `wait`, kein Hintergrundprozess  
- **`--strictPort`**: Port-Konflikt schlägt sofort fehl  
- Kein **`npm install`** / **`npm run build`** im Produktivstart (reproduzierbarer Deploy)  
- Fehlt `frontend/dist/index.html` oder `node_modules` → klare Fehlermeldung, Exit **1**

---

## Wiederherstellung (Operator)

Nach Repo-Update oder manuellem Fix:

```bash
cd /home/volker/piinstaller   # oder Ihr Checkout

# Frontend-Build (vor Deploy, nicht im Service-Skript)
cd frontend && npm run build && cd ..

sudo cp scripts/start-browser-production.sh /opt/setuphelfer/scripts/
sudo chmod +x /opt/setuphelfer/scripts/start-browser-production.sh
sudo cp -a frontend/dist/. /opt/setuphelfer/frontend/dist/

sudo systemctl daemon-reload
sudo systemctl restart setuphelfer.service
```

Prüfen:

```bash
systemctl is-active setuphelfer.service
curl -I http://127.0.0.1:3001
```

---

## Vor Backup / BR-001

**Kein** Backup, Restore oder Verify Deep starten, solange:

- `setuphelfer-backend.service` nicht **active** ist  
- `setuphelfer.service` nicht **active** ist und **:3001** nicht antwortet  
- `./scripts/check-runtime-deploy-gate.sh` nicht Exit **0** liefert  

SMTP-Test und BR-001 sind **separate** Schritte nach grünem Runtime-Gate.

---

## Verwandte Dokumente

- `docs/BETRIEB_REPO_VS_SERVICE.md` — Repo vs. `/opt`  
- `docs/knowledge-base/runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md` — Kurz-KB  
- `docs/architecture/NAMING_AND_SERVICES.md` — Service-Namen
