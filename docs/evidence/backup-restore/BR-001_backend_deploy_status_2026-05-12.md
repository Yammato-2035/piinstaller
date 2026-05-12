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
