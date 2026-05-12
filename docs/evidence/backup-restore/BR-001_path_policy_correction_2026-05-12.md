# BR-001 — Pfad-Politkorrektur (Betreiberfreigabe, STRICT, 2026-05-12)

## Hintergrund: frühere falsche Pfadableitung

In älteren Evidence-Schritten wurde **`/mnt/setuphelfer/backups`** als intendiertes oder zu prüfendes BR-001-Ziel genutzt bzw. mit externem Volume über **Bind** in Verbindung gebracht. **`findmnt -T`** zeigte dort den **internen** Root-Stack (`/dev/nvme0n1p2`), nicht das USB-Volume **`/dev/sda1`**.

Diese Ableitung ist **für BR-001 nicht mehr maßgeblich** und darf **nicht** als Ersatz- oder Umleitungspfad dienen.

## Verbindliche neue Regel (Betreiber)

> **Nur** der **ausdrücklich freigegebene** Pfad bzw. ein **vom Betreiber im Prompt namentlich genannter** Unterordner **innerhalb** dieses Pfads ist zulässig. Keine automatische Pfaderweiterung, kein Ausweichen, kein anderer Mount unter `/media/...` ohne Freigabe.

## Aktuelle Freigabe (maßgeblich für BR-001)

| Feld | Wert |
|------|------|
| Gerät | **`sda` / `sda1`** |
| Mount / Zielpfad | **`/media/gabriel/setuphelfer-back`** |
| Dateisystem | **ext4** |
| Label | **setuphelfer-back** |
| UUID | **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`** |
| Größe (Partition) | ca. **931,5 G** (`lsblk`) |

### Explizit nicht erlaubt (Betreiberliste)

- **`/mnt/setuphelfer/backups`**
- **Bind-Mount** (weder vorschlagen noch anlegen)
- **Ersatzpfade** (`/tmp`, `/home`, `/var`, Root-FS, interne NVMe-Ziele)
- **`sdb1`**, **`sdd1`**, **INTENSO**, **`windows-backup`**
- **andere** `/media/...`-Ziele ohne gesonderte Freigabe
- **ACL-Automatik**, **Pfadkorrektur** durch Tooling

## Unterordner

In diesem Durchlauf wurde **kein** Unterordner im Prompt genannt → Ziel bleibt **`/media/gabriel/setuphelfer-back`** (kein neuer Unterordner erstellt, kein anderer Pfad geprüft).

## Verifikation (nur lesend, diese Session)

- Pfad existiert; **`findmnt -T /media/gabriel/setuphelfer-back`** → **`/dev/sda1`**, **ext4**, **rw**.
- **`df -hT`**, **`stat`**, **`realpath`:** konsistent mit o. g. Mount (Gerät **8/1**).
- Kein anderer Pfad für `target-check` oder Evidence verwendet.

## Dienstnutzer `setuphelfer`

- **`sudo -n -u setuphelfer test …`:** **nicht ausführbar** (Passwort erforderlich) → Traverse/Schreibzugriff **nicht verifiziert** (kein Erzwingen).

## Produktiver API-`target-check` (ausschließlich freigegebener Pfad)

**URL:** `GET http://127.0.0.1:8000/api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`

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

→ **Nicht** grün; **kein** Backup-Start.

## Status für BR-001

**`blocked`**

- Freigegebener Pfad ist **mount-seitig** korrekt auf **`/dev/sda1`** (extern, ext4, rw).
- **Kein** grüner produktiver **`target-check`** auf genau diesem Pfad (**STORAGE-001**).
- **Dienstnutzer-Zugriff** wegen fehlendem **`sudo -n`** nicht nachgewiesen.

Es erfolgte **keine** Umgehung auf andere Pfade, **kein** Bind, **keine** ACL-Änderung.

## Abnahme (Policy-Dokument)

| Kriterium | Erfüllt? |
|-----------|----------|
| Keine Pfadumdeutung | **Ja** |
| Kein `/mnt/setuphelfer/backups` als Ziel verwendet | **Ja** |
| Keine neuen Zielpfade erstellt | **Ja** |
| BR-001 nur bei grünem Check auf Freigabepfad — hier | **Nein** → **blocked** |
