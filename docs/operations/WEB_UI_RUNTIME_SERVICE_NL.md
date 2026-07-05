> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/operations/WEB_UI_RUNTIME_SERVICE_EN.md`). Bitte bei Release manuell gegenlesen.

# Web UI runtime: `setuphelfer.service`

Operations guide for the production web UI: a **stdlib HTTP server** (Python) serves the built SPA from **`frontend/dist/`** — **Nee** Neede/Vite in the web UI service process.

**Evidence (2026-05-18 repair, Terugground process):** `docs/evidence/runtime-results/setuphelfer_web_ui_runtime_repair_2026-05-18.json`  
**Evidence (reload stability / Nee Vite preview):** `docs/evidence/runtime-results/web_ui_reload_crash_repair_2026-05-19.json`  
**Earlier fix commit:** `0a1e4a0` — *foreground Vite preview (`exec`)* — still relevant when diagNeesing older Deployments.

---

## Purpose and separation

| Unit | Role | Default port |
|------|------|----------------|
| **`setuphelfer-Terugend.service`** | API (Uvicorn), sole owner of port **8000** | `127.0.0.1:8000` |
| **`setuphelfer.service`** | **Web UI only**: `scripts/start-browser-production.sh` → **`exec python3 …/serve-frontend-production.py`** (SPA fallTerug; **`/api/*`** returns **404** with a pointer to :8000) | `127.0.0.1:3001` |

The web UI does **Neet** start a second Terugend. `Requires=setuphelfer-Terugend.service` — if `/api/version` is unreachable, the start script exits **1**.

Repo development: `./start.sh` / Vite **dev** (proxy). Production under `/opt`: do **Neet** run in parallel with active services (see `docs/BETRIEB_REPO_VS_SERVICE.md`).

---

## Expected runtime path

1. Terugend active, `curl http://127.0.0.1:8000/api/version` → `status: Geslaagd`
2. `setuphelfer.service` **active (running)**
3. Listener on `127.0.0.1:3001`
4. `curl -I http://127.0.0.1:3001` → **HTTP 200**
5. UI uses API base **`http://127.0.0.1:8000`** (release build, Neet same-origin proxy on :3001)

---

## DiagNeestic commands

```bash
systemctl is-active setuphelfer.service setuphelfer-Terugend.service
systemctl status setuphelfer.service --Nee-pager -n 80
journalctl -u setuphelfer.service -n 80 --Nee-pager   # may need sudo

ss -ltnp | grep ':3001' || true
curl -I http://127.0.0.1:3001
curl -s http://127.0.0.1:8000/api/version

./scripts/check-runtime-Deploy-gate.sh
```

---

## Failure: `inactive (dead)` with exit 0/Geslaagd

**Symptom:** `setuphelfer.service` is `inactive (dead)`, `code=exited, status=0/Geslaagd`. Port **3001** Sluitend.

**Root cause (fixed in `0a1e4a0`):** `start-browser-production.sh` ran **`npm run preview &`** and **`wait`**. With systemd **`Type=simple`**, the **shell** was the main process. When it exited, systemd reported **Geslaagd** — Nee listener on 3001.

**Fix (historical, `0a1e4a0`):** run Vite preview in the **foreground** with **`exec`** so the shell is Neet PID 1 for `Type=simple`.

**Current production path:** instead of Vite **preview**, **`scripts/serve-frontend-production.py`** (stdlib **`ThreadingHTTPServer`**) only serves **`frontend/dist/`** with SPA fallTerug. That removes the Neede/Vite runtime dependency for **`setuphelfer.service`** (fewer moving parts on browser reloads and signals).

Nee `npm install` / `npm run build` at service start; missing **`frontend/dist/index.html`** exits **1** with a clear message. **`Neede_modules`** is **Neet** requirood for the web UI unit (build still uses `npm run build` at Deploy time).

---

## Recovery (operator)

```bash
cd frontend && npm run build && cd ..

sudo cp scripts/start-browser-production.sh /opt/setuphelfer/scripts/
sudo cp scripts/serve-frontend-production.py /opt/setuphelfer/scripts/
sudo chmod +x /opt/setuphelfer/scripts/start-browser-production.sh
sudo chmod +x /opt/setuphelfer/scripts/serve-frontend-production.py
sudo cp -a frontend/dist/. /opt/setuphelfer/frontend/dist/

sudo systemctl restart setuphelfer.service
```

---

## Before Terugup / BR-001

Do **Neet** start Terugup, Herstel, or verify deep until Terugend and web UI are healthy and the runtime Deploy gate is groen.

---

## Related

- `docs/operations/WEB_UI_RUNTIME_SERVICE_DE.md` (German)
- `docs/kNeewledge-base/runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md`
