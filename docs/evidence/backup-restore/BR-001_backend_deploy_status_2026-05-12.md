# BR-001 — Produktives Backend: Stand, Diff, Deploy (2026-05-12)

## Phase 1 — Erfasste Fakten

| Prüfung | Ergebnis |
|---------|----------|
| Workspace `git rev-parse HEAD` | `03cf7bd43e6bff1f7147ec742d50cf3ceb1b7515` (Stand zum Evidence-Lauf; Arbeitskopie kann zusätzlich lokale Änderungen haben) |
| `curl http://127.0.0.1:8000/api/version` | `install_profile`: **opt**, Version **1.5.0.0** |
| `systemctl show setuphelfer-backend.service` | `User=setuphelfer`, `Group=setuphelfer`, `WorkingDirectory=/opt/setuphelfer`, Start: `/opt/setuphelfer/backend/venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8000` |
| `systemctl status` | **active (running)** |

## Diff Workspace ↔ `/opt/setuphelfer/backend`

Dateien **verschieden** (`diff -q`):

- `app.py`
- `core/safe_device.py`
- `core/diagnostics/registry.py`
- `core/diagnostics/matcher.py`

## Marker im produktiven `/opt` (grep)

- **`STORAGE-PROTECTION-006`**, **`backup.target_traverse_denied`**, **`_assert_media_tree_traversable`**: im produktiven **`app.py`** / **`safe_device.py`** **nicht** nachweisbar (0 Treffer für 006-Zeichenkette in `safe_device.py`).
- **`_normalize_findmnt_bracket_block_source`**, **`_flatten_findmnt_filesystems`**: im produktiven Bestand **unklar/abweichend** gegenüber Workspace — vollständiger Dateiabgleich nicht nötig für Evidence: **Kern: produktiv veraltet** relativ zu Workspace `03cf7bd`.

## Phase 2 — Deploy / Restart

**Status:** **BLOCKED**

- `sudo -n true` → Passwort erforderlich (`exit 1`).
- **Kein** Kopieren nach `/opt`, **kein** `/tmp/setuphelfer-deploy-backup-*`, **kein** `systemctl restart`.

## target-check strategischer Pfad (produktiv, alter Code)

```text
GET /api/backup/target-check?backup_dir=/media/setuphelfer/setuphelfer-back&create=0
→ STORAGE-PROTECTION-001 (backup.path_invalid)
```

**Hinweis:** Pfad existiert auf dem System nicht; zudem fehlt der Workspace-Diagnosefix auf `/opt`. Nach erfolgreichem Deploy des Workspace-Stands ist bei fehlendem Traverse **`backup.target_traverse_denied`** / **006** erwartbar — weiterhin **blockierend**, aber nicht als „Systemplatte“ fehlklassifiziert.

## Rollback

Nicht anwendbar (kein Deploy).

## Nächste Schritte

1. Interaktives **sudo** mit dokumentiertem Deploy-Runbook (Backup unter `/tmp/setuphelfer-deploy-backup-<ts>/`, `sha256sum`, Kopie der vier Dateien, `systemctl restart setuphelfer-backend.service`).  
2. Erneut **`curl …/api/version`** und **target-check** gegen freigegebenen Pfad.

---

## Deploy-Versuch 2026-05-13 (Betreiberfreigabe: vier Dateien) — im Cursor-Agenten **BLOCKED**

**Ursache:** `sudo -n` und `sudo` ohne TTY schlagen fehl (`sudo: ein Terminal ist erforderlich …`). In dieser Umgebung wurde **kein** Backup-Verzeichnis unter `/tmp` angelegt, **keine** Datei nach `/opt` kopiert, **kein** `systemctl restart`.

### sha256 — **alt** (aktuell `/opt/setuphelfer/backend`, 2026-05-13 erfasst)

| Datei | SHA256 |
|-------|--------|
| `app.py` | `68a740b72aaadba848a8f35536b1b9ad19ca538e6fdbb9889764c43257ac9138` |
| `core/safe_device.py` | `2c0085c5bb6ecc24b53f92b83ae6aba2fa6aa59b05bb5f9918b85afd00930601` |
| `core/diagnostics/registry.py` | `d11835c09f02c0901d945e3f1bf15c48967b08d42e071c3bbb22b198e40562a0` |
| `core/diagnostics/matcher.py` | `2c369ca919d2d65c53b1573d584f2863959853adeecf6c8ef8b3c2b6fd95b3f8` |

### sha256 — **neu** (Workspace `main` @ `a1aebba17985d0646ff440913709c1e47e766c67`, Quellbäume `backend/…`)

| Datei | SHA256 |
|-------|--------|
| `app.py` | `60517c0c9cbae832b94788e419f13f6c8872084c45e37cb0b62c1f3ea5db486a` |
| `core/safe_device.py` | `e33be50f750ce36631f3d3943bc90e3d60d72bfbf669e6ba375ee5468a52b849` |
| `core/diagnostics/registry.py` | `5986134ca868c981692c93af24dc8bcf1e5231014fc4b26986f0a5951adbc0a6` |
| `core/diagnostics/matcher.py` | `348335c22c4e9b299ff7fff0736845a3ad8395596be04627e3dd12be2547c0fe` |

### target-check (nur dokumentiert, **ohne** erfolgreichen Deploy)

`GET /api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0` → weiterhin **STORAGE-PROTECTION-001** / `backup.path_invalid` (Produktivcode noch alt).

---

## Operator-Runbook (auf dem Zielhost **interaktiv** ausführen)

Nur die vier freigegebenen Dateien; **kein** Backup-Start, **keine** Mount-/Rechteänderung.

```bash
set -euo pipefail
WS=/home/volker/piinstaller/backend
OPT=/opt/setuphelfer/backend
TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP=/tmp/setuphelfer-deploy-backup-${TS}
sudo mkdir -p "$BACKUP"
sudo cp -a "$OPT/app.py" "$OPT/core/safe_device.py" \
  "$OPT/core/diagnostics/registry.py" "$OPT/core/diagnostics/matcher.py" "$BACKUP/"
sudo sha256sum "$OPT/app.py" "$OPT/core/safe_device.py" \
  "$OPT/core/diagnostics/registry.py" "$OPT/core/diagnostics/matcher.py" \
  | sudo tee "$BACKUP/SHA256SUMS.before"
sudo install -o root -g root -m 0644 "$WS/app.py" "$OPT/app.py"
sudo install -o root -g root -m 0644 "$WS/core/safe_device.py" "$OPT/core/safe_device.py"
sudo install -o root -g root -m 0644 "$WS/core/diagnostics/registry.py" "$OPT/core/diagnostics/registry.py"
sudo install -o root -g root -m 0644 "$WS/core/diagnostics/matcher.py" "$OPT/core/diagnostics/matcher.py"
sudo chown setuphelfer:setuphelfer "$OPT/app.py" "$OPT/core/safe_device.py" \
  "$OPT/core/diagnostics/registry.py" "$OPT/core/diagnostics/matcher.py"
sudo sha256sum "$OPT/app.py" "$OPT/core/safe_device.py" \
  "$OPT/core/diagnostics/registry.py" "$OPT/core/diagnostics/matcher.py" \
  | sudo tee "$BACKUP/SHA256SUMS.after"
sudo systemctl restart setuphelfer-backend.service
curl -s http://127.0.0.1:8000/api/version
curl -s "http://127.0.0.1:8000/api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0"
echo "BACKUP=$BACKUP"
```

**Rollback** (nur bei Bedarf): aus `$BACKUP` die vier Dateien zurück nach `$OPT/…` kopieren, `chown setuphelfer:setuphelfer`, `systemctl restart`.

---

## STRICT — `core.versioning` für `/api/version` (2026-05-13)

### Phase 1 — Modulprüfung

| Prüfung | Ergebnis |
|---------|----------|
| Workspace `backend/core/versioning.py` | **vorhanden** (`ls -l` ok) |
| `/opt/setuphelfer/backend/core/versioning.py` | **fehlte** (`ls`: keine Datei) — **Ursache** für `ModuleNotFoundError: No module named 'core.versioning'` nach Teildeploy von `app.py`, das `core.versioning` importiert |
| Imports in `versioning.py` | nur **stdlib** (`json`, `dataclasses`, `pathlib`, `typing`) |

### Phase 2 — Laufzeitabhängigkeit (ohne weitere Python-Module)

- `versioning.py` liest **`config/version.json`** relativ zu `_REPO_ROOT` = zwei Ebenen über `backend/core/versioning.py` → **`/opt/setuphelfer/config/version.json`**.
- **`/opt/setuphelfer/config/version.json`:** **vorhanden** — **keine** weiteren fehlenden lokalen Python-Module für `versioning.py` identifiziert.

### Phase 3 — Backup der Zieldatei

- Datei unter `/opt` **existierte nicht** → **„neu in /opt“** — kein `/tmp/setuphelfer-deploy-backup-*`-Backup einer alten `versioning.py` erforderlich.

### Phase 4–5 — Deploy / Restart (Agent)

**BLOCKED:** `sudo install …` schlägt fehl mit *„ein Terminal ist erforderlich … Passwort ist notwendig“*. **Keine** Datei nach `/opt` kopiert, **`systemctl restart`** nicht ausgeführt.

### Verifikation (ohne erfolgreichen Deploy)

| Prüfung | Ergebnis (2026-05-13, Host) |
|---------|------------------------------|
| `curl -i http://127.0.0.1:8000/api/version` | **HTTP 500** `Internal Server Error` (konsistent mit fehlendem `core.versioning` auf Importpfad von `/api/version`) |
| `curl -i "http://127.0.0.1:8000/api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0"` | **HTTP 200**, JSON **`status":"success"`**, **`code":"backup.target_check_ok"`** (unabhängig von fehlendem `versioning`-Modul) |
| `systemctl status setuphelfer-backend.service --no-pager` | **active (running)** |

### Operator — Minimalbefehl (nur diese eine Datei)

Kein Backup-Start, kein Restore, kein anderer Zielpfad:

```bash
sudo install -o setuphelfer -g setuphelfer -m 0644 \
  /home/volker/piinstaller/backend/core/versioning.py \
  /opt/setuphelfer/backend/core/versioning.py
sudo systemctl restart setuphelfer-backend.service
curl -i http://127.0.0.1:8000/api/version
```

**SHA256** Quelle (Workspace): `39c22a547578ec5027455ef29565d6e8a368348a71cd2101999507d5544d0f1d` — `backend/core/versioning.py`.

---

## STRICT — Vollständiger Backend-/Version-Sync (2026-05-13, Phasen 0–9)

### Kurzfassung

| Thema | Ergebnis |
|-------|----------|
| `sudo` für `/tmp`-Backup + `install` + `restart` | **BLOCKED** (TTY/Passwort) |
| `backend/app.py` … `matcher.py` vs. Workspace | **SHA256 identisch** (bereits auf Workspace-Stand) |
| `core/versioning.py` | **identisch** (Zwischenstand „fehlend unter `/opt`“ aus früherem STRICT-Lauf ist **überholt**) |
| **`/opt/setuphelfer/config/version.json`** | **Altes Schema** (`version`/`codename`/`release_date`) → **`/api/version` → HTTP 500** |
| Workspace `config/version.json` | **Neues Schema** mit `version_source_of_truth` |
| `target-check` nur `/media/gabriel/setuphelfer-back` | **HTTP 200**, JSON-Fehler **`backup.backup_target_not_writable`**; Shell-`findmnt` **rw**, API **`ro`** + EROFS → **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`** |
| Backup gestartet | **Nein** |

### Operator — vollständiges Runbook (wie Prompt; interaktiv)

Geplanter Backup-Pfad: `/tmp/setuphelfer-deploy-backup-$(date -u +%Y%m%dT%H%M%SZ)` — siehe **`BR-001_backend_update_and_version_fix_2026-05-13.md`** für SHA256-Referenz und Befund „nur `version.json` drift“.

### Abnahme (dieser Lauf)

**Nicht erfolgreich:** `/api/version` nicht HTTP 200; `target-check` nicht „sauber grün“; BR-001 bleibt **`blocked`**.
