# Backup: Verify, Restore-Preview und Laufzeitressourcen

Kurznotiz für **Betrieb**, **VM-Tests** und **Support**, wenn Deep-Verify, Restore-Preview oder große Archive scheinbar „ohne Grund“ scheitern. Ergänzt [BACKUP_TARGET_PERMISSIONS.md](BACKUP_TARGET_PERMISSIONS.md) und [RESTORE_ISOLATED_TEST_FROM_BACKUP.md](RESTORE_ISOLATED_TEST_FROM_BACKUP.md).

## 1. systemd: `MemoryMax` / `MemorySwapMax` und OOM

Das Backend läuft typischerweise als **`setuphelfer-backend.service`**. Ist in einer **Drop-In-Unit** ein sehr kleines **`MemoryMax`** gesetzt (z. B. 512 M), können **Verify (deep)** oder **CPU-/Speicher-intensive** Schritte den Prozess per ** cgroup-OOM** beenden.

**Symptome:** Lauf bricht ab, Journal zeigt OOM oder Dienst-Neustart, API bricht ohne klaren Archivfehler ab.

**Maßnahme (Betrieb):** Drop-In unter `/etc/systemd/system/setuphelfer-backend.service.d/` anpassen, z. B. höheres **`MemoryMax`** / **`MemorySwapMax`**, dann `systemctl daemon-reload` und `systemctl restart setuphelfer-backend.service`. Für Tests sind Werte in der Größenordnung **4 G / 8 G** üblich; Produktionswerte an Hardware und Parallelität anpassen.

**Diagnosekatalog:** `SYSTEMD-MEMORYMAX-037` (siehe `docs/knowledge-base/diagnostics/DIAGNOSIS_CATALOG.md`).

## 2. `TMPDIR` und Staging (Verify / Preview)

Verify legt Staging oft unter **`/tmp`** bzw. unter dem für den Dienstprozess gültigen **`TMPDIR`** an. **`PrivateTmp=yes`** isoliert den Dienst-`/tmp` vom Host-`/tmp` — das ist sicherheitsmäßig sinnvoll, erschwert aber **manuelle Inspektion** der Preview-Verzeichnisse.

Wenn **`/tmp`** als **tmpfs** klein ist oder das Staging große Archive entpackt, treten **ENOSPC**-Fehler auf, obwohl große Datenplatten (z. B. `/mnt/...`) frei sind.

**Maßnahme:** Auf einem **großen, persistenten** Mount **`TMPDIR`** setzen (Drop-In `Environment=TMPDIR=...`), Verzeichnis anlegen, Besitz/Modus passend zum Dienstuser (siehe Gruppenmodell in `BACKUP_TARGET_PERMISSIONS.md`). Anschließend Dienst neu starten.

**Diagnosekatalog:** `RESTORE-TMPFS-007` (u. a. bei Preview-Extrakt mit Platzmangel); API-Hinweise zu PrivateTmp siehe Erfolgsantwort Restore-Preview (`private_tmp_isolation`).

## 3. Deep-Verify: Integrität vs. Full-Root-Archive

**Deep-Verify** prüft u. a. **Symlinks** und **Staging-Containment**. Full-System-Archive können **absolute Symlink-Ziele** oder Einträge enthalten, die im Staging als **„unsicher“** oder **„invalid_symlink“** gewertet werden. Das führt zu **`backup.verify_integrity_failed`**, ohne dass das Medium defekt sein muss.

**Maßnahme:** Kontext prüfen (Archivtyp, erwartbare Root-Full-Inhalte); ggf. **Basic-Verify** + Hash-Stichproben; bei produktionsnahen Full-Archiven die technische Auswertung in den Entwicklerdokumenten zu Verify/Restore heranziehen.

**Diagnosekatalog:** `VERIFY-STAGING-038`.

## 4. VirtualBox / Test-VMs: Platten vergrößern

Für wiederholbare **Verify/Preview**-Läufe müssen die **VDI-Kapazitäten** und die **Partitionen in der Gast-VM** zusammenpassen:

1. VM stoppen, Host: `VBoxManage modifymedium disk "<pfad>.vdi" --resize <MiB>` (Beispiel 64 GiB ≈ `65536` MiB).
2. Bei **Differencing-/Snapshot-VDIs** ggf. **Basis- und Kind-Medium** prüfen; logische Größe im Gast folgt der Kette.
3. Im Gast: **`growpart`** (Paket `cloud-guest-utils`) und **`resize2fs`** auf der **richtigen** Partition nur nach `lsblk`/`df`-Abgleich; bei Unsicherheit **nicht** raten.

## 5. Verwandte Dokumente

| Dokument | Thema |
|----------|--------|
| [../faq/BACKUP_RESTORE_FAQ_DE.md](../faq/BACKUP_RESTORE_FAQ_DE.md) / [../faq/BACKUP_RESTORE_FAQ_EN.md](../faq/BACKUP_RESTORE_FAQ_EN.md) | Kurz-FAQ |
| [../developer/BACKUP_RECOVERY_ENGINES.md](../developer/BACKUP_RECOVERY_ENGINES.md) | Engine-Überblick |
| [../developer/BACKUP_RESTORE_STABILITY_TEST_MATRIX.md](../developer/BACKUP_RESTORE_STABILITY_TEST_MATRIX.md) | Testmatrix |
| [diagnostics/DIAGNOSIS_CATALOG.md](diagnostics/DIAGNOSIS_CATALOG.md) | Diagnose-IDs |
