# Externe Backup-Ziel-Architektur (Setuphelfer)

## Root Cause (BR-001 Blocker)

Der Dienst **`setuphelfer-backend`** läuft als **`User=setuphelfer`** (nicht root) mit **`ProtectSystem=strict`**, **`PrivateTmp=yes`**, **`ProtectHome=yes`** und expliziten **`ReadWritePaths=`**.

Typische Desktop-USB-Einhängungen erscheinen unter **`/media/<login>/…`** (udisks2) und sind oft **`drwx------`** (nur Besitzer). Der Dienstnutzer ist **nicht** dieser Login → **kein Lesen, kein Schreiben**, noch bevor tar startet.

Das ist **kein** USB-, gzip- oder Runner-Defekt, sondern **Zielpfad-/ACL-/systemd-Architektur**.

## Zielbild: ohne Home-User-Abhängigkeit

| Muster | Zweck |
|--------|--------|
| **`/mnt/setuphelfer/backups`** | Standard (internes Team-Volume unter Kontrolle des Produkts; Gruppe `setuphelfer`, Modus typisch **0770**). |
| **`/media/setuphelfer/<label>/`** | Empfohlener **externer** Baum: einmalig anlegen, Besitzer **`root`**, Gruppe **`setuphelfer`**, Modus **0750** oder **0770** — **kein** `chmod 777`. |
| **`/mnt/setuphelfer/external/<uuid>/`** | Alternative unter `/mnt` (z. B. stabiler Admin-Mount per fstab); gleiche Gruppe/Rechte. |

**Nicht** als produktives externes BR-001-Ziel: Pfade, die nur unter **`/media/<persönlicher-login>/`** liegen und dem Dienst verschlossen sind.

## systemd

- **`ReadWritePaths`** muss jeden Pfad enthalten, unter dem der Dienst **schreiben** soll, wenn **`ProtectSystem=strict`** aktiv ist — sonst **EROFS**-ähnliches Verhalten im Service-Namespace.
- Repo-Units listen **`/media/setuphelfer`** (nicht benutzerspezifische `/media/gabriel/…`).
- **`setuphelfer-backup@.service`** (Runner als root) hat eigene **`ReadWritePaths`**; konsistent mit Backend halten.

## API-Diagnose (keine stillen Fehler)

Nach `validate_write_target` prüft der Code **`assert_backup_target_writable_for_service`**:

| ID | Bedeutung |
|----|-----------|
| **BACKUP-TARGET-USER-MOUNT-003** | Pfad unter `/media/<nicht-setuphelfer>/…` oder `/run/media/<nicht-setuphelfer>/…` und für den Dienst nicht beschreibbar. |
| **BACKUP-TARGET-PERMISSION-001** | Pfad zulässig (z. B. unter `/mnt/setuphelfer/`), aber Schreiben/Probe schlägt fehl — Gruppe, ACL oder fehlendes **`ReadWritePaths`**. |
| **BACKUP-TARGET-NOT-WRITABLE-002** | Generisch nicht beschreibbar. |

Details: `GET /api/backup/target-check`, `POST /api/backup/create`, `POST /api/backup/settings` liefern **`diagnosis_id`** in den Fehlerdetails, wenn zutreffend.

## Operator-Flow (kurz)

1. USB/ext4 einhängen (Blockgerät muss weiterhin die **safe_device**-Klassifikation passieren).
2. Ziel anlegen, z. B. `sudo mkdir -p /media/setuphelfer/br001 && sudo chown root:setuphelfer /media/setuphelfer/br001 && sudo chmod 0770 /media/setuphelfer/br001`.
3. **`ReadWritePaths`** prüfen bzw. Drop-in unter `/etc/systemd/system/setuphelfer-backend.service.d/` (siehe `docs/operations/systemd/setuphelfer-backend-backup-target.conf.example`).
4. `sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service`.
5. In den App-Einstellungen **`backup_dir`** auf dieses Verzeichnis setzen; **`GET /api/backup/target-check?backup_dir=…`** zur Kontrolle.

**Vollständige ausführbare Sequenz (Shell, curl, Freeze, Monitoring):**  
`docs/evidence/runtime-results/handoff/BR001_operator_final_execution_handoff.md`

## FAQ

### Warum kann Setuphelfer nicht nach `/media/<user>/…` schreiben?

Weil der Dienst als **`setuphelfer`** läuft, nicht als Ihr GUI-Login. udisks legt dort oft **0700** nur für den Einhängenden an. Nutzen Sie **`/media/setuphelfer/…`** oder **`/mnt/setuphelfer/external/…`** mit Gruppe **`setuphelfer`** — siehe Tabelle oben.

### Warum kein `chmod 777`?

World-writable Verzeichnisse verwässern jede Schutzlinie (Tar, Rescue, Mandanten). Minimalrecht: **Besitzer root, Gruppe setuphelfer, 0770**.

### Interne NVMe als „extern“?

Nicht zulässig für BR-001-STRICT: internes Root-Dateisystem darf nicht als externes Archivziel verkauft werden; die Produktsicherheitslogik bleibt unverändert.
