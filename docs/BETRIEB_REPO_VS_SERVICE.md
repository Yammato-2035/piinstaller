# Betrieb: Repo-Modus vs. Service-/Produktivmodus

Zwei klar getrennte Szenarien. Vermischung führt zu typischen Fehlern (z. B. **EACCES** unter `frontend/node_modules/.vite`, doppeltes Backend, leere UI trotz laufendem API).

**Aktuell (ab 1.4.0):** Installationspfad **`/opt/setuphelfer`**, systemd **`setuphelfer-backend.service`** + **`setuphelfer.service`**, System-User **`setuphelfer`**.  
**Legacy (ältere Installationen):** `/opt/pi-installer`, `pi-installer*.service`, User `pi-installer` – Migration siehe Changelog 1.4.0.0.

---

## 1. Repo- / Entwicklungsmodus

**Zweck:** Arbeiten im geklonten Projektverzeichnis (z. B. `~/Documents/PI-Installer`).

| Schritt | Aktion |
|--------|--------|
| Services unter `/opt` | **nicht** parallel zu Entwicklung nutzen: `sudo systemctl stop setuphelfer.service setuphelfer-backend.service` (bzw. Legacy: `pi-installer.service pi-installer-backend.service`, wenn noch installiert) |
| Backend | `./scripts/start-backend.sh` oder `./start.sh` |
| Frontend (Dev) | `./start.sh` startet **Vite dev** (`npm run dev`) auf Port **3001** – Hot-Reload, schreibt nach `node_modules/.vite` |
| Tauri | siehe `docs/START_APPS.md` |

**Nicht parallel:** Installierte `setuphelfer.service` aus `/opt` starten, während im Repo dasselbe Backend/Frontend entwickelt wird – Portkonflikte und falsche API-Ziele.

---

## 2. Service-/Produktivmodus (`/opt/setuphelfer`)

**Zweck:** Systemd startet die Anwendung nach Installation/Deploy (DEB, `deploy-to-opt.sh`, `install-system.sh`).

| Komponente | Rolle |
|------------|-------|
| `setuphelfer-backend.service` | **Alleiniger Owner von Port 8000** – startet **`scripts/start-backend.sh`** (Uvicorn). |
| `setuphelfer.service` | Nur **Web-UI**: **`scripts/start-browser-production.sh`** (**vite preview** auf **`frontend/dist/`**). Startet **kein** Backend; bricht ab, wenn `/api/version` nicht erreichbar ist. |

**Standardbetrieb:**

- Beide Units **enabled**; `setuphelfer.service` hat **`Requires=setuphelfer-backend.service`** (Web-UI startet nicht ohne API).
- **`APP_EDITION=release`** in beiden Units (Repo-Zusatz: `.env` im Projekt kann für manuellen `start-backend.sh` weiterhin `repo` setzen).

**Service-User:** DEB und Deploy nutzen den System-User **`setuphelfer`**. `scripts/install-backend-service.sh` wählt für **`INSTALL_DIR=/opt/setuphelfer`** ebenfalls **`setuphelfer`**, falls dieser User existiert; sonst den aufrufenden Login-User (typisch: Entwicklung aus dem Repo).

**Nicht parallel sinnvoll:** Zusätzlich im Terminal `./start.sh` im Repo starten, während beide Services aktiv sind.

**Vite-Cache im Produktivstart:** `PI_INSTALLER_VITE_CACHE_DIR` bzw. Setuphelfer-Äquivalente – standardmäßig Cache unter `/tmp` (siehe `scripts/start-browser-production.sh`), nicht zwingend Schreiben unter `node_modules/.vite`.

---

## 3. Status prüfen

```bash
systemctl status setuphelfer.service setuphelfer-backend.service --no-pager
journalctl -u setuphelfer.service -n 40 --no-pager
journalctl -u setuphelfer-backend.service -n 40 --no-pager
curl -sS http://127.0.0.1:8000/api/version
curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:3001/
```

*(Legacy-Units: `pi-installer.service` / `pi-installer-backend.service` analog.)*

---

## 4. Fehlerbild: Backend antwortet, Browser-UI leer oder Fehler

| Prüfung | Bedeutung |
|---------|-----------|
| `curl http://127.0.0.1:8000/api/version` | Backend OK? |
| `curl -I http://127.0.0.1:3001/` | Liefert preview/UI etwas (HTTP 200)? |
| `journalctl -u setuphelfer.service` | Tritt **EACCES** / **mkdir … node_modules/.vite** auf? → Dann läuft noch **Dev-Start** (`start.sh` / `npm run dev`) statt `start-browser-production.sh`. `ExecStart` muss auf **`…/scripts/start-browser-production.sh`** zeigen. |
| Falsche gespeicherte API-URL in der App | Einstellungen zur Backend-URL; Fallback in der App versucht `127.0.0.1:8000` – ersetzt nicht die korrekte Trennung der Startmodi. |

---

## 5. Deploy nach `/opt` aktualisieren

Nach Änderung der Units im Repo:

```bash
sudo ./scripts/deploy-to-opt.sh
```

Oder Units manuell anpassen, `sudo systemctl daemon-reload`, dann z. B. `sudo systemctl restart setuphelfer-backend.service` und `sudo systemctl restart setuphelfer.service`.

---

Siehe auch: `docs/START_APPS.md`, `scripts/restart-backend-service.sh`.
