# Namensgebung, Pakete und systemd (Referenz ab 1.4.0)

_Diese Seite ist die **Referenz für Reviews und Architekturentscheidungen** (Phase D3). Nutzerdoku bleibt in `docs/SYSTEM_INSTALLATION.md`, `docs/START_APPS.md`, `docs/BETRIEB_REPO_VS_SERVICE.md`._

---

## 1. Begriffe

| Begriff | Bedeutung |
|---------|-----------|
| **Setuphelfer** | Produkt-/Anzeigename; Debian-**Binary-Paket** `setuphelfer`. |
| **piinstaller / PI-Installer** | Häufig der **GitHub-Repository-Name** und historische Bezeichnung in älteren Texten. |
| **Source-Paket (Debian)** | In `debian/control`: `Source: pi-installer` – unverändert; daraus wird das Binary-Paket `setuphelfer` gebaut. |
| **Tauri-Binary** | Artefaktname im Build oft weiterhin `pi-installer` (`frontend/src-tauri/target/release/pi-installer`) – Umbenennung nur mit angepasstem `Cargo.toml`/CI. |

---

## 2. Installations- und Konfigurationspfade

Implementierung: `backend/core/install_paths.py`.

| Zweck | Standard (neu) | Legacy (&lt; 1.4.0) |
|-------|----------------|----------------------|
| Programm | `/opt/setuphelfer` | `/opt/pi-installer` |
| Konfiguration | `/etc/setuphelfer` | `/etc/pi-installer` |
| Zustand | `/var/lib/setuphelfer` | `/var/lib/pi-installer` |
| Logs (system) | `/var/log/setuphelfer` | `/var/log/pi-installer` |
| Dev (`PI_INSTALLER_DEV=1`) | `~/.config/setuphelfer` (u. a.) | – |

**Umgebungsvariablen** (in `install_paths.py`: zuerst `SETUPHELFER_*`, nur wenn leer `PI_INSTALLER_*`):

- `SETUPHELFER_DIR` → sonst `PI_INSTALLER_DIR`
- `SETUPHELFER_CONFIG_DIR` → sonst `PI_INSTALLER_CONFIG_DIR`
- `SETUPHELFER_STATE_DIR` → sonst `PI_INSTALLER_STATE_DIR`
- `SETUPHELFER_LOG_DIR` → sonst `PI_INSTALLER_LOG_DIR`

**Service-Modus:** Ohne Dev-Flag kein Home-Fallback für `config.json` (siehe `_config_path()` in Backend).

---

## 3. systemd (Produktion)

| Unit | Rolle |
|------|--------|
| **`setuphelfer-backend.service`** | Alleinig **Owner von Port 8000**; startet `scripts/start-backend.sh` (Uvicorn). |
| **`setuphelfer.service`** | **Web-UI**: `scripts/start-browser-production.sh` (Vite **preview** auf `frontend/dist/`). **Requires** Backend; startet kein zweites Backend. |

Vorlagen: Repo-Root `setuphelfer.service`, `setuphelfer-backend.service`; Debian installiert nach `/etc/systemd/system/`.

**Legacy:** `pi-installer.service` / `pi-installer-backend.service` – bei Migration stilllegen/entfernen (siehe `debian/postinst`, `scripts/deploy-to-opt.sh`).

---

## 4. CLI und Symlinks (`install-system.sh`)

Unter `/usr/local/bin/` u. a.:

- `setuphelfer` → `scripts/start-setuphelfer.sh` (bzw. Wrapper `start-pi-installer.sh`)
- `setuphelfer-backend`, `setuphelfer-frontend`, `setuphelfer-start`, `setuphelfer-scripts`

Legacy-Symlinks `pi-installer*` können auf älteren Systemen noch existieren.

---

## 5. Repo- vs. Release-Edition

- **`APP_EDITION=release`:** Installiertes System (DEB/`/opt`); kein „Update aus Repo“-Menü für Endnutzer wie in Repo-Builds.
- **`APP_EDITION=repo`:** Entwicklung; Sidebar kann z. B. „Setuphelfer Update“ / technische Seiten zeigen (`appEdition` in Frontend).

Details: `docs/review/security/repo_vs_release_mode_summary.md` (IDs wie `pi-installer-update` sind **interne Route-IDs**, nicht der Produktname).

---

## 6. Verwandte Dokumente

| Dokument | Inhalt |
|----------|--------|
| `docs/architecture/init_flow.md` | Startreihenfolge Backend, Skripte |
| `docs/architecture/config_flow.md` | `config.json`, Debug-Layering |
| `docs/BETRIEB_REPO_VS_SERVICE.md` | Repo-Modus vs. `/opt`-Betrieb |
| `docs/review/phase1_structure.md` | Modul- und Pfadübersicht (wird mit dieser Referenz abgestimmt) |
| `docs/VERIFY_TARGET_SYSTEM.md` | Phase F: Skript `scripts/verify-setuphelfer-install.sh` (systemd, curl, journalctl) |
