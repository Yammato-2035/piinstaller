# BR-001 — Produktiver target-check: Shell vs. API (`/media/gabriel/setuphelfer-back`)

**Datum:** 2026-05-12  
**Modus:** STRICT — nur Lesen, Analyse, Evidence; **kein** Backup, **kein** Deploy, **kein** Restart, **kein** Pfadwechsel.

## 1. Verbindlich freigegebener Pfad

**`/media/gabriel/setuphelfer-back`** (ausschließlich; kein Unterordner im Prompt genannt).

## 2. Shell — Ist-Zustand (Phase 1)

### `lsblk` (Auszug relevant)

- **`/dev/sda1`:** ext4, LABEL **setuphelfer-back**, UUID **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, MOUNTPOINTS **`/media/gabriel/setuphelfer-back`**, TRAN **usb**.

### `findmnt -T /media/gabriel/setuphelfer-back`

```text
TARGET                          SOURCE    FSTYPE OPTIONS
/media/gabriel/setuphelfer-back /dev/sda1 ext4   rw,...
```

### `df -hT`

- `/dev/sda1` ext4 auf `/media/gabriel/setuphelfer-back`.

### `stat` (Kern)

| Pfad | Gerät | Modus | Owner:Group |
|------|-------|-------|----------------|
| `/media` | 259/9 | 0755 | root:root |
| `/media/gabriel` | 259/9 | **0750** | **root:root** |
| `/media/gabriel/setuphelfer-back` | **8/1** | 2770 | root:setuphelfer |

**Hinweis:** `/media` und `/media/gabriel` liegen auf dem **Root-Dateisystem** (Gerät 259/9 = nvme-Stack); das **Volume** des Ziels ist **8/1** (`/dev/sda1`).

### `realpath`

`/media/gabriel/setuphelfer-back` (unverändert).

### Kontroll-`findmnt` für mögliche API-Anker (als Shell-User mit Traverse)

```text
$ findmnt -T /media
TARGET SOURCE         FSTYPE
/      /dev/nvme0n1p2 ext4

$ findmnt -T /media/gabriel
TARGET SOURCE         FSTYPE
/      /dev/nvme0n1p2 ext4
```

**Bedeutung:** Liefert `findmnt -T` den Anker **`/media`** oder **`/media/gabriel`**, wird fälschlich die **System-Root-Partition** (`/dev/nvme0n1p2`) zugeordnet.

## 3. Produktive API — target-check vor Änderung

**Request:** `GET http://127.0.0.1:8000/api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`

**Response (vollständig):**

```json
{
  "status": "error",
  "message": "Ungültiges Backup-Ziel: STORAGE-PROTECTION-001: Schreibzugriff auf Systemplatte ist nicht erlaubt",
  "code": "backup.path_invalid",
  "severity": "error",
  "details": {
    "reason": "STORAGE-PROTECTION-001: Schreibzugriff auf Systemplatte ist nicht erlaubt"
  }
}
```

**Diagnosecode:** **STORAGE-PROTECTION-001** (Systemplatte).

## 4. Unterschied Shell vs. API

| Aspekt | Shell (z. B. Operator-User mit Traverse) | API (Prozess `setuphelfer`) |
|--------|------------------------------------------|------------------------------|
| `findmnt -T` auf **vollständigem** Zielpfad | **`/dev/sda1`**, ext4, korrekt | (intern) ggf. Anker **ohne** Traverse bis zum Ziel |
| Ergebnis | extern, rw | **STORAGE-001** |

## 5. Produktiver Dienst (Phase 2, nur lesend)

- **`GET /api/version`:** `1.5.0.0`, `install_profile`: `opt`.
- **systemd:** `User=setuphelfer`, `Group=setuphelfer`, `WorkingDirectory=/opt/setuphelfer`, Start über `/opt/setuphelfer/scripts/start-backend.sh`.
- **Status:** `active (running)`.

### `grep` auf `/opt/setuphelfer/backend`

- **`_flatten_findmnt_filesystems`** in **`app.py`:** **kein Treffer** (Workspace **`main`** enthält diese Hilfsfunktion in `app.py`; Produktion weicht ab).
- **`_findmnt_mounts`:** in **`/opt/setuphelfer/backend/app.py`** vorhanden (Zeilen u. a. 11675+ laut früherem Stand — Produktivdatei hat **andere** `app.py`-Struktur/Versionierung als Workspace-Snapshot im Diff).
- **`STORAGE-PROTECTION-001`:** u. a. `core/safe_device.py`, `app.py`, Tests, Diagnostics.

### `diff` Workspace vs. `/opt` (Kernaussagen, ohne Deploy)

- **`app.py`:** **größere Abweichungen** (u. a. Versionslogik, Router-Registrierungen; Workspace enthält u. a. **`_flatten_findmnt_filesystems`** / angepasstes **`_findmnt_mounts`** — Produktion **`grep`** zeigt **keine** `_flatten_findmnt_filesystems` in **`app.py`**).
- **`core/safe_device.py`:** Produktion **ohne** Block **`_normalize_findmnt_bracket_block_source`** / Regex (Workspace hat diesen Klammer-`SOURCE`-Fix).

**Fazis Phase 2:** Produktion **entspricht nicht** dem Workspace-Stand für **`app.py`** und weicht bei **`safe_device.py`** ab. **Kein** Kopiervorgang und **kein** Restart in diesem Lauf (keine ausdrückliche Deploy-Freigabe im Prompt).

## 6. Ursachenklassifikation (Phase 3)

| Kategorie | Trifft zu? | Kurzbegründung |
|-----------|--------------|----------------|
| **A)** Alter `app.py` ohne findmnt-Flatten in **dieser** Datei | **Teilweise** | `/opt/.../app.py` ohne `_flatten_findmnt_filesystems`; für **`resolve_mount_source_for_path`** nutzt **`safe_device`** jedoch eigenes **`_flatten_findmnt_nodes`** — für diesen konkreten STORAGE-001 nicht die Hauptursache. |
| **B)** Alter `safe_device` (fehlender Klammer-Fix) | **Teilweise** | Diff zeigt fehlende Normalisierung; betrifft v. a. `SOURCE`-Syntax mit `[/…]` — **nicht** die hier gezeigte reine `/dev/sda1`-Quelle in der Shell. |
| **C)** **`setuphelfer`** kann **`/media/gabriel`** nicht traversieren | **Ja (Hauptursache)** | **`/media/gabriel`** ist **0750** **`root:root`** ohne world-`x` → User ohne passende UID/ACL kann den Zielbaum nicht betreten. |
| **D)** API/Logik fällt auf Vorfahren-Anker (`/media` / `/media/gabriel`) und wertet dann Root-FS | **Ja (Folge)** | **`resolve_mount_source_for_path`** nutzt **`_find_existing_anchor`**. Für Anker **`/media`** liefert **`findmnt -T /media`** → **`/`** / **`nvme0n1p2`** → **`_classified_for_block`** markiert **Systemplatte** → **STORAGE-001**. |
| **E)** Anderer Codepfad als Workspace-TestClient | **Unklar / neben** | Gleiches `validate_write_target`; relevant ist Prozess-User + Ankerlogik. |
| **F)** Sonstiges | — | — |

**Primär:** **C + D**. **Sekundär:** **A/B** (Drift Workspace ↔ `/opt`).

### `sudo -n -u setuphelfer` (Phase 3)

Wie zuvor: **Passwort nötig** — Traverse/Schreiben für **`setuphelfer`** hier **nicht** verifiziert (nicht erzwungen).

## 7. Minimaler Fixplan (Phase 4 — nur dokumentiert)

**Ohne** ausdrückliche Deploy-/Betriebsfreigabe in **diesem** Prompt: **keine** Ausführung.

1. **Betrieb / Freigabe (ohne neue Pfade, ohne Bind):** Sicherstellen, dass der **Dienstnutzer** den freigegebenen Pfad **traversieren** kann (nur mit **ausdrücklicher** Freigabe; **keine** automatische ACL durch dieses Ticket), **oder** technisch equivalent nachweisen (z. B. gezielter Operator-Test mit dokumentierter Policy).  
2. **Optional (nur mit ausdrücklicher Deploy-Freigabe):** Produktiven Code an Workspace angleichen (`app.py`, `safe_device.py`), Backup der alten Dateien, **`systemctl restart`**, erneuter **`target-check`** **nur** gegen **`/media/gabriel/setuphelfer-back`**.  
3. **Code (langfristig, außerhalb dieses Evidence-Laufs):** **`_find_existing_anchor`** / Mount-Auflösung so, dass bei fehlendem Traverse **nicht** still auf **`/media`** → Root-FS zurückgefallen wird (z. B. harte Fehlermeldung statt fälschlicher Systemplatten-Klassifikation) — **keine** Implementierung in diesem Schritt verlangt.

**Explizit verboten im Fixplan:** `/mnt/setuphelfer/backups`, Bind, andere Backup-Ziele, Backup-Start.

## 8. Deploy / Restart (Phase 5)

**Nicht durchgeführt** (keine ausdrückliche Freigabe im Prompt).

## 9. BR-001 in diesem Lauf (Phase 6)

**Kein** Backup gestartet. BR-001 bleibt **`blocked`** / **`review_required`** bis grüner Check **und** ausdrückliche Backup-Freigabe.

## 10. Abnahme (nur Analyse)

| Kriterium | Erfüllt? |
|-----------|----------|
| Keine Pfadumdeutung | **Ja** |
| Kein `/mnt/setuphelfer/backups` als Ziel | **Ja** |
| Kein Backup | **Ja** |
| Ursache dokumentiert | **Ja** |
| target-check nur den Freigabepfad betrachtet | **Ja** |

## 11. Workspace-Umsetzung (2026-05-12, Diagnosefix)

Im Repository wurde die in **Abschnitt 7** skizzierte **Code**-Variante umgesetzt: fehlende Traversierung unter **`/media`** / **`/run/media`** führt zu **STORAGE-PROTECTION-006** und API-Code **`backup.target_traverse_denied`**, nicht mehr zu fälschlicher **STORAGE-PROTECTION-001**. Details und Testnachweise: **`BR-001_target_permission_diagnostics_fix_2026-05-12.md`**. **Kein** produktiver Re-Deploy oder **`target-check`**-Re-Lauf in diesem Schritt (keine ausdrückliche Freigabe).

## 12. Strategischer Pfad `/media/setuphelfer/setuphelfer-back` (Doku, 2026-05-12)

Dieser Pfad ist in Produkt- und Evidence-Doku als **konventionelles externes Ziel** beschrieben — **nur** zulässig, wenn er **tatsächlich auf dem gewählten externen Blockgerät** liegt. Auf der Evidence-Maschine existiert er **nicht**; es wurde **kein** `mkdir`, **kein** Bind-Mount und **keine** ACL-Änderung durchgeführt. Das derzeit gemountete externe ext4-Volume mit LABEL **setuphelfer-back** liegt unter **`/media/gabriel/setuphelfer-back`**. Abstimmung mit dem Betreiber: strategischer Mount unter **`/media/setuphelfer/...`** vs. Beibehaltung des Benutzerpfads — siehe **`BR-001_external_target_policy_2026-05-12.md`** und **`BR-001_backend_deploy_status_2026-05-12.md`** (produktives Backend zu Workspace-Zeitpunkt noch nicht synchron, **sudo** für Deploy blockiert).

## 13. Deploy Diagnose-Fix (2026-05-13, Betreiberfreigabe)

Vier Dateien (`app.py`, `safe_device.py`, `registry.py`, `matcher.py`) — siehe **`BR-001_backend_deploy_status_2026-05-12.md`** (sha256 alt/neu, Operator-Runbook). **target-check** laut Freigabe nur gegen **`/media/gabriel/setuphelfer-back`** (nicht gegen `/media/setuphelfer/setuphelfer-back`, solange nicht extern gemountet). Im Cursor-Agenten: Deploy **BLOCKED** (kein TTY-`sudo`); produktiver **target-check** daher unverändert **STORAGE-001** bis Runbook auf dem Host ausgeführt wurde.

## 14. STRICT 2026-05-13 — Paralleler Snapshot (`core.versioning` vs. target-check)

**Kontext:** Nach Teildeploy kann **`app.py`** `core.versioning` erwarten, während **`/opt/setuphelfer/backend/core/versioning.py`** fehlt → **`ModuleNotFoundError`** auf **`/api/version`**.

| Prüfung | Ergebnis |
|---------|----------|
| Workspace `backend/core/versioning.py` | vorhanden |
| `/opt/setuphelfer/backend/core/versioning.py` | **fehlte** (vor geplantem `install`) |
| Zusätzliche lokale Imports in `versioning.py` | **keine** (nur stdlib); **`/opt/setuphelfer/config/version.json`** vorhanden |
| `sudo install` / `systemctl restart` (Cursor-Agent) | **nicht ausgeführt** (sudo Passwort/TTY) |
| **`GET /api/version`** | **HTTP 500** `Internal Server Error` |
| **`GET …/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`** (gleicher Lauf) | **HTTP 200**, **`code":"backup.target_check_ok"`**, u. a. **`mount.source":"/dev/sdd1"`** (Gerät kann sich vom Stand 2026-05-12 unterscheiden) |

**Hinweis (2026-05-13 Nachmessung):** `core/versioning.py` liegt inzwischen unter `/opt` (SHA256 = Workspace); **`/api/version` 500** folgt primär aus **altem** `/opt/setuphelfer/config/version.json` ohne `version_source_of_truth` — siehe Abschnitt **15** und **`BR-001_backend_update_and_version_fix_2026-05-13.md`**.

## 15. STRICT 2026-05-13 — Workspace-Parität, `version.json`, `target-check`

| Prüfung | Ergebnis |
|---------|----------|
| `app.py` … `matcher.py` (Workspace vs. `/opt`) | **SHA256 identisch** (siehe `BR-001_backend_update_and_version_fix_2026-05-13.md`) |
| `core/versioning.py` | **identisch** |
| `/opt/setuphelfer/config/version.json` | **Altes Schema** — **Ursache `/api/version` 500** (nicht `version_source_of_truth`) |
| `sudo` Deploy | **BLOCKED** |
| `findmnt -T /media/gabriel/setuphelfer-back` | **rw**, ext4, SOURCE `/dev/sdd1`, UUID **adbd53e5-…** |
| `GET …target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0` | **HTTP 200**, **`backup.backup_target_not_writable`**, API **`mount_readonly": true`**, **`ro`** in `mount.options`, EROFS auf Schreibprobe |
| Widerspruch Shell rw vs. API ro | **Ja** — **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`** |

**Hinweis:** Abschnitt 14 beschrieb u. a. erfolgreichen `target-check`; der Messzeitpunkt **2026-05-13** danach zeigt **fehlgeschlagenen Schreibtest** trotz gleichem Freigabepfad — Zustand des Mounts/API kann sich unterscheiden; beide Snapshots bleiben in den jeweiligen Evidence-Dateien nachvollziehbar.
